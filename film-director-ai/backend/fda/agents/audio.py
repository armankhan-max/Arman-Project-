"""Audio Agent: narration clean-up, original score, planned sound effects, ducking and loudness-normalised mix."""
import os
import re

from fda.database import models as m
from fda.services import assets, media
from fda.storage.store import scratch_dir
from fda.rendering.engine import sound

from .common import scenes, style, voiceover

SFX_WORDS = [("whoosh", "whoosh"), ("swoosh", "whoosh"), ("wind", "wind"), ("rumble", "rumble"), ("explosion", "rumble"), ("thunder", "rumble"), ("impact", "hit"),
             ("boom", "hit"), ("hit", "hit"), ("riser", "riser"), ("tension", "riser"), ("tick", "tick"), ("clock", "tick"), ("click", "click"), ("pop", "pop"),
             ("camera", "shutter"), ("shutter", "shutter"), ("typing", "typing"), ("keyboard", "typing"), ("heart", "heartbeat"), ("water", "water"), ("wave", "water"),
             ("ocean", "water"), ("glitch", "glitch"), ("static", "glitch"), ("bell", "ding"), ("ding", "ding"), ("chime", "ding")]
TRANS_SFX = {"push": "whoosh", "slide": "whoosh", "wipe": "whoosh", "zoom": "zoom", "dip": "hit", "glitch": "glitch", "flash": "flash", "burn": "burn"}
COMPANION = {"cinematic": ["suspense", "emotional"], "suspense": ["dark", "tension"], "emotional": ["ambient", "cinematic"], "ambient": ["emotional", "cinematic"],
             "tension": ["suspense", "epic"], "upbeat": ["curious"], "curious": ["upbeat"], "warm": ["curious"], "epic": ["tension"], "dark": ["suspense"], "playful": ["curious"]}


def sfx_name(text):
    t = (text or "").lower()
    for k, v in SFX_WORDS:
        if re.search(r"\b" + k, t):
            return v
    return None


def plan_cues(scs, st):
    cues = []
    if not st.get("sfx", True):
        return cues
    for i, sc in enumerate(scs):
        pl = sc.plan or {}
        for raw in (pl.get("sfx") or [])[:2]:
            n = sfx_name(raw)
            if n:
                cues.append((sc.start_s + (sc.end_s - sc.start_s - 0.2 if n == "riser" else 0.1), n, 0.5, sc.idx, raw))
        tr = pl.get("transition")
        if i and tr in TRANS_SFX:
            cues.append((sc.start_s, TRANS_SFX[tr], 0.45, sc.idx, "transition " + tr))
        if sc.visual_type == "motion_graphic":
            cues.append((sc.start_s + 0.25, "pop", 0.4, sc.idx, "graphic reveal"))
    cues.sort()
    dedup, last = [], {}
    for c in cues:  # never stack the same effect within 0.6 s
        if c[0] - last.get(c[1], -9) >= 0.6:
            dedup.append(c)
            last[c[1]] = c[0]
    return dedup


def run(ctx):
    db, p = ctx.db, ctx.project
    ps, st = style(db, p)
    vo = voiceover(db, p.id)
    if not vo or not vo.processed_asset_id:
        raise RuntimeError("No narration audio to mix")
    scs = scenes(db, p.id)
    dur = max([sc.end_s for sc in scs] + [vo.duration_s or 0]) + 0.2
    work = scratch_dir(p.id, "audio")
    voice_src = assets.local(db.get(m.Asset, vo.processed_asset_id))
    vw = os.path.join(work, "voice.wav")
    media.run(["ffmpeg", "-y", "-v", "error", "-i", voice_src, "-ac", "1", "-ar", str(sound.SR), "-af", "apad", "-t", "%.3f" % dur, vw])
    ctx.progress(0.2, "Composing the score")
    mood = st.get("music", "cinematic")
    sections = [(0.0, mood)]
    if mood != "none" and dur > 150:
        comp = COMPANION.get(mood, [mood])
        for k, frac in enumerate((0.38, 0.72)):
            sections.append((round(dur * frac, 2), comp[k % len(comp)]))
    mw = sound.build_music(os.path.join(work, "music.wav"), dur, mood, p.id.int % 9999, sections)
    ctx.progress(0.5, "Placing sound effects")
    cues = plan_cues(scs, st)
    sw = sound.build_sfx(os.path.join(work, "sfx.wav"), dur, [(c[0], c[1], c[2]) for c in cues], p.id.int % 9999, st.get("ambience") or None)
    ctx.progress(0.75, "Mixing")
    out = os.path.join(work, "mix.m4a")
    sound.mix(vw, mw, sw, out, float(st.get("music_volume", 0.5)), float(st.get("sfx_volume", 0.7)), bool(st.get("voice_enhance", True)), False)
    for role in ("music", "sfx", "mix", "voice"):
        old = db.query(m.AudioTrack).filter_by(project_id=p.id, role=role).one_or_none()
        if old:
            db.delete(old)
    db.flush()
    lic = dict(license="Original, generated in code", commercial_use="yes")
    ma = assets.register(db, mw, p.id, "music", "audio", "music.wav", origin="procedural", provider="procedural_audio", settings={"mood": mood, "sections": sections}, **lic)
    sa = assets.register(db, sw, p.id, "sfx", "audio", "sfx.wav", origin="procedural", provider="procedural_audio", settings={"cues": len(cues)}, **lic)
    xa = assets.register(db, out, p.id, "mix", "audio", "final_mix.m4a", origin="procedural", provider="ffmpeg",
                         settings={"chain": "highpass, denoise, EQ, de-ess, compression, sidechain ducking, loudnorm -14 LUFS" if st.get("voice_enhance", True) else "loudnorm only"}, **lic)
    db.add(m.AudioTrack(project_id=p.id, role="voice", asset_id=vo.processed_asset_id, volume=1.0, props={"enhance": bool(st.get("voice_enhance", True))}))
    db.add(m.AudioTrack(project_id=p.id, role="music", asset_id=ma.id, volume=float(st.get("music_volume", 0.5)), props={"mood": mood, "sections": sections, "ducking": True}))
    db.add(m.AudioTrack(project_id=p.id, role="sfx", asset_id=sa.id, volume=float(st.get("sfx_volume", 0.7)),
                        props={"cues": [{"t": round(c[0], 2), "name": c[1], "scene": c[3], "why": c[4]} for c in cues]}))
    db.add(m.AudioTrack(project_id=p.id, role="mix", asset_id=xa.id, volume=1.0, props={"target_lufs": -14}))
    return {"summary": "Audio mixed: %s score (%d sections), %d sound effects, voice %s" % (mood, len(sections), len(cues), "enhanced" if st.get("voice_enhance", True) else "untouched")}
