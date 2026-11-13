"""Voiceover Analyzer Agent (uploaded narration) and narration synthesis (when there is only a script).

The original upload is never modified; analysis and processing work on registered copies."""
import os
import re
import wave
from concurrent.futures import ThreadPoolExecutor

import numpy as np

from fda.config import get_settings
from fda.database import models as m
from fda.providers import registry
from fda.providers.base import NotConfigured, ProviderError
from fda.services import assets, media
from fda.storage.store import scratch_dir

from .common import latest_script, sentences, style, uploads, words

SR = 44100


def decode_wav(src, dest, sr=SR):
    media.run([get_settings().ffmpeg_bin, "-y", "-v", "error", "-i", src, "-ac", "1", "-ar", str(sr), "-c:a", "pcm_s16le", dest], timeout=1800)
    return dest


def read_wav(path):
    with wave.open(path, "rb") as w:
        return np.frombuffer(w.readframes(w.getnframes()), "<i2").astype(np.float32) / 32768.0, w.getframerate()


def write_wav(path, x, sr=SR):
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype("<i2").tobytes())


def speech_regions(x, sr, thresh_db=-38, min_sil=0.22):
    hop = int(sr * 0.02)
    n = len(x) // hop
    if n == 0:
        return []
    rms = np.sqrt((x[:n * hop].reshape(n, hop) ** 2).mean(1) + 1e-12)
    db = 20 * np.log10(rms)
    ref = np.percentile(db, 95)
    voiced = db > max(thresh_db, ref - 32)
    regions, cur = [], None
    gap = int(min_sil / 0.02)
    sil = 0
    for i, v in enumerate(voiced):
        if v:
            if cur is None:
                cur = [i, i]
            cur[1] = i
            sil = 0
        elif cur is not None:
            sil += 1
            if sil > gap:
                regions.append(cur)
                cur, sil = None, 0
    if cur:
        regions.append(cur)
    return [(a * 0.02, (b + 1) * 0.02) for a, b in regions if (b - a) >= 3]


def align_text(text, regions):
    """Approximate alignment: spread the script's words over detected speech, weighted by word length.
    Used only when no speech recogniser is available; marked word_level=False."""
    ws = words(text)
    if not ws or not regions:
        return []
    total = sum(b - a for a, b in regions)
    wts = [len(w) + 1.5 + (2.5 if w[-1] in ".!?" else 1.0 if w[-1] in ",;:" else 0) for w in ws]
    W = sum(wts)
    out, acc = [], 0.0

    def at(t):
        for a, b in regions:
            if t <= b - a:
                return a + t
            t -= b - a
        return regions[-1][1]
    for w, wt in zip(ws, wts):
        s = at(acc / W * total)
        acc += wt
        e = at(acc / W * total)
        out.append({"w": w, "s": round(s, 3), "e": round(max(s + 0.05, e - 0.03), 3), "p": 0.0})
    return out


def segments_from_words(ws):
    segs, cur = [], []
    for i, w in enumerate(ws):
        cur.append(i)
        nxt_gap = (ws[i + 1]["s"] - w["e"]) if i + 1 < len(ws) else 0
        if w["w"][-1:] in ".!?।" or len(cur) >= 35 or nxt_gap > 1.2:
            segs.append((cur[0], cur[-1], round(max(0.0, nxt_gap), 3)))
            cur = []
    if cur:
        segs.append((cur[0], cur[-1], 0.0))
    return segs


def save_transcript(db, vo, lang, ws, word_level, provider):
    db.query(m.Transcript).filter_by(voiceover_id=vo.id).delete()
    tr = m.Transcript(voiceover_id=vo.id, language=lang, text=" ".join(w["w"] for w in ws), word_level=word_level, provider=provider, words=ws)
    db.add(tr)
    db.flush()
    for k, (a, b, pause) in enumerate(segments_from_words(ws)):
        db.add(m.TranscriptSegment(transcript_id=tr.id, idx=k, start_s=ws[a]["s"], end_s=ws[b]["e"], text=" ".join(w["w"] for w in ws[a:b + 1]),
                                   word_start=a, word_end=b, pause_after_s=pause))
    db.flush()
    return tr


def analyze_upload(ctx, original):
    db, p = ctx.db, ctx.project
    work = scratch_dir(p.id, "voice")
    src = assets.local(original)
    info = media.probe(src)
    if not info.get("audio"):
        raise ProviderError("The uploaded voiceover has no audio stream", retryable=False)
    ctx.progress(0.1, "Decoding narration")
    wav = decode_wav(src, os.path.join(work, "narration_analysis.wav"))
    proc = assets.register(db, wav, p.id, "processed", "audio", "narration_processed.wav", origin="upload", provider="ffmpeg", parent_id=original.id,
                           settings={"op": "decode mono 44.1kHz pcm"}, license="Owner's own recording", commercial_use="yes")
    det = media.detect(src, video=False, audio=True, duration=info["duration"])
    x, sr = read_wav(wav)
    regions = speech_regions(x, sr)
    vo = m.Voiceover(project_id=p.id, origin="upload", original_asset_id=original.id, processed_asset_id=proc.id, duration_s=info["duration"],
                     sample_rate=info["audio"]["sample_rate"], channels=info["audio"]["channels"], codec=info["audio"]["codec"],
                     analysis={"peak_db": det["peak_db"], "integrated_lufs": det["integrated_lufs"], "silences": det["silence"][:200],
                               "speech_regions": [[round(a, 2), round(b, 2)] for a, b in regions[:2000]],
                               "clipping": (det["peak_db"] or -99) > -0.3})
    db.add(vo)
    db.flush()
    ctx.progress(0.25, "Transcribing narration")
    tr_res, errors = None, []
    for prov in registry.for_cap(db, "stt", usable_only=True):
        try:
            if prov.paid:
                from fda.permissions import budget_manager as budget
                rec = budget.reserve(db, prov, "transcribe", info["duration"] / 60, "audio minutes", p.id)
            tr_res = prov.transcribe(wav, p.language)
            if prov.paid:
                budget.commit(db, rec)
            tr_res["provider"] = prov.name
            break
        except Exception as e:
            errors.append("%s: %s" % (prov.label, e))
    if tr_res and tr_res["words"]:
        ws = tr_res["words"]
        tr = save_transcript(db, vo, tr_res.get("language") or p.language, ws, tr_res.get("word_level", True), tr_res["provider"])
        note = "Transcribed with %s (%d words)" % (tr_res["provider"], len(ws))
    else:
        sc, sv = latest_script(db, p.id)
        if not sv:
            raise NotConfigured("No speech-to-text provider could transcribe the narration (%s). Upload the matching script too, or configure "
                                "local Whisper / OpenAI transcription in Settings → Providers." % "; ".join(errors) or "none configured")
        ws = align_text(sv.text, regions)
        tr = save_transcript(db, vo, p.language, ws, False, "approximate-alignment")
        note = "No speech recogniser available; aligned your script to the detected speech (approximate word timing)"
        ctx.log(note + ". Errors: " + "; ".join(errors)[:300], "warn")
    vo.analysis = dict(vo.analysis, words_per_minute=round(len(ws) / max(0.1, info["duration"] / 60), 1))
    long_pauses = [[round(ws[i]["e"], 2), round(ws[i + 1]["s"] - ws[i]["e"], 2)] for i in range(len(ws) - 1) if ws[i + 1]["s"] - ws[i]["e"] > 1.0]
    vo.analysis = dict(vo.analysis, long_pauses=long_pauses[:100])
    if not latest_script(db, p.id)[1]:
        sc = m.Script(project_id=p.id, origin="transcript", current_version=1)
        db.add(sc)
        db.flush()
        db.add(m.ScriptVersion(script_id=sc.id, version=1, text=tr.text, note="Transcript of the uploaded narration"))
    return {"summary": note + "; %.1fs, %.0f wpm" % (info["duration"], vo.analysis["words_per_minute"]), "state": {"voiceover_id": str(vo.id)}}


def _merge(script_words, marks):
    if not marks:
        return []
    if len(marks) == len(script_words):
        return [{"w": w, "s": round(mk["s"], 3), "e": round(mk["e"], 3), "p": 1.0} for w, mk in zip(script_words, marks)]
    out = []
    for i, w in enumerate(script_words):
        k = min(len(marks) - 1, int(round(i * (len(marks) - 1) / max(1, len(script_words) - 1))))
        out.append({"w": w, "s": round(marks[k]["s"], 3), "e": round(marks[k]["e"], 3), "p": 0.5})
    for i in range(1, len(out)):
        if out[i]["s"] <= out[i - 1]["s"]:
            out[i]["s"] = round(out[i - 1]["s"] + 0.04, 3)
            out[i]["e"] = max(out[i]["e"], out[i]["s"] + 0.05)
    return out


def synthesize(ctx):
    db, p = ctx.db, ctx.project
    ps, st = style(db, p)
    sc, sv = latest_script(db, p.id)
    if not sv:
        raise ProviderError("There is no script to voice", retryable=False)
    tts = None
    voice = st.get("voice")
    for prov in registry.for_cap(db, "tts"):
        if prov.name == st.get("tts_provider", prov.name) or not st.get("tts_provider"):
            tts = prov
            break
    if tts is None:
        raise NotConfigured("No text-to-speech provider is available")
    if tts.name != "edge_tts" and (voice or "").endswith("Neural"):
        voice = st.get("voice_" + tts.name) or voice
    work = scratch_dir(p.id, "tts")
    paras = [x for x in re.split(r"\n\s*\n", sv.text) if x.strip()]
    chunks = []
    for pi, para in enumerate(paras):
        buf = ""
        for s in sentences(para):
            if len(buf) + len(s) > 380 and buf:
                chunks.append((buf, False))
                buf = ""
            buf = (buf + " " + s).strip()
        if buf:
            chunks.append((buf, True))
    if tts.paid:
        from fda.permissions import budget_manager as budget
        rec = budget.reserve(db, tts, "tts", sum(len(c) for c, _ in chunks), "characters", p.id)
    results = [None] * len(chunks)
    done = [0]

    def job(i):
        text, _ = chunks[i]
        mp3 = os.path.join(work, "c%04d.mp3" % i)
        r = tts.speak(text, voice, mp3, int(st.get("voice_rate", 0)), int(st.get("voice_pitch", 0)))
        wav = decode_wav(mp3, os.path.join(work, "c%04d.wav" % i))
        x, _ = read_wav(wav)
        results[i] = (x, r.get("words") or [])
        done[0] += 1
        ctx.task.message = "Recording narration %d/%d" % (done[0], len(chunks))
    with ThreadPoolExecutor(4) as ex:
        list(ex.map(job, range(len(chunks))))
    if tts.paid:
        budget.commit(db, rec)
    ctx.progress(0.8, "Assembling narration")
    pieces, all_words, t = [np.zeros(int(0.4 * SR), np.float32)], [], 0.4
    for (text, para_end), (x, marks) in zip(chunks, results):
        sw = words(text)
        ws = _merge(sw, marks) or align_text(text, [(0.05, len(x) / SR - 0.05)])
        end = len(x) / SR
        if ws:
            end = min(end, ws[-1]["e"] + 0.25)
        x = x[:int(end * SR)]
        for w in ws:
            all_words.append({"w": w["w"], "s": round(w["s"] + t, 3), "e": round(w["e"] + t, 3), "p": w.get("p", 1.0)})
        pieces.append(x)
        gap = 0.75 if para_end else 0.32
        pieces.append(np.zeros(int(gap * SR), np.float32))
        t += len(x) / SR + gap
    full = os.path.join(work, "narration.wav")
    write_wav(full, np.concatenate(pieces))
    a = assets.register(db, full, p.id, "processed", "audio", "narration_tts.wav", origin="tts", provider=tts.name, settings={"voice": voice, "rate": st.get("voice_rate"),
                        "pitch": st.get("voice_pitch")}, license="Synthetic voice (%s)" % tts.label, commercial_use="unknown" if not tts.paid else "yes")
    vo = m.Voiceover(project_id=p.id, origin="tts", processed_asset_id=a.id, duration_s=t, sample_rate=SR, channels=1, codec="pcm_s16le",
                     analysis={"voice": voice, "provider": tts.name, "words_per_minute": round(len(all_words) / max(0.1, t / 60), 1)})
    db.add(vo)
    db.flush()
    save_transcript(db, vo, p.language, all_words, bool(results and results[0][1]), tts.name)
    return {"summary": "Narration recorded with %s (%s): %.1fs" % (tts.label, voice, t), "state": {"voiceover_id": str(vo.id)}}


def run(ctx):
    db, p = ctx.db, ctx.project
    existing = db.query(m.Voiceover).filter_by(project_id=p.id).order_by(m.Voiceover.created_at.desc()).first()
    if existing and not ctx.params.get("redo"):
        return {"skipped": True, "summary": "Narration already analysed", "state": {"voiceover_id": str(existing.id)}}
    ups = uploads(db, p.id, "audio")
    if ups:
        return analyze_upload(ctx, ups[-1])
    return synthesize(ctx)
