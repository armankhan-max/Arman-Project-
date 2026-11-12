"""Title -> script -> scenes -> voice -> visuals -> edit -> finished video. Runs in a background thread."""
import hashlib
import os
import subprocess
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor

import numpy as np

import avatar
import graphics
import stick2d
import llm
import look as looks
import media
import render
import sfx
import store
import thumb
import tts

GAP = 0.3  # seconds of breath between scenes
OUTRO = 4.0  # end card length
_running = set()
_sem = threading.Semaphore(1)  # one render at a time keeps small servers alive


def start(pid, preview=False):
    if pid in _running:
        return False
    _running.add(pid)
    store.update_project(pid, status="queued", progress=0, step="Waiting in queue", error="")
    threading.Thread(target=_guard, args=(pid, preview), daemon=True).start()
    return True


def _guard(pid, preview):
    try:
        with _sem:
            _run(pid, preview)
    except Exception as e:
        traceback.print_exc()
        p = store.get_project(pid)
        if p:
            p["log"].append("ERROR: " + str(e))
            p.update(status="error", error=str(e), step="Failed")
            store.save_project(p)
    finally:
        _running.discard(pid)


def _run(pid, preview):
    p = store.get_project(pid)
    cfg = store.get_settings()
    d = store.pdir(pid)
    style = cfg["styles"].get(p.get("style"), cfg["styles"]["documentary"])
    w, h = render.SIZES.get(p.get("aspect", "16:9"), render.SIZES["16:9"])
    prof = store.get_profile(p.get("profile_id") or "") if p.get("profile_id") else None
    if prof:  # brand profile: reference editing style, blocked words/sources, background music
        ref = ((prof.get("reference") or {}).get("settings") or {})
        style = dict(style)
        for k in ("shot_seconds", "grade"):
            if ref.get(k):
                style[k] = ref[k]
        if ref.get("transitions"):
            style["transitions"] = ref["transitions"]
        hint = " ".join(x for x in (style.get("script_hint", ""), ref.get("script_hint", ""),
                                     ("Avoid these topics and words: " + prof["block_words"]) if prof.get("block_words") else "") if x)
        style["script_hint"] = hint
        cfg = dict(cfg, styles={**cfg["styles"], p.get("style"): style})
        if ref.get("words_per_minute"):
            cfg["words_per_minute"] = ref["words_per_minute"]
        src = prof.get("sources") or {}
        cfg["_blocked_sources"] = [k for k, v in src.items() if v is False]
        cfg["_block_words"] = [w.strip().lower() for w in (prof.get("block_words") or "").split(",") if w.strip()]
        cfg["_block_domains"] = [w.strip().lower() for w in (prof.get("block_domains") or "").split(",") if w.strip()]
    OUTRO = 4.0 if style.get("outro", True) else 0.0  # end card only for styles that want one
    if not p.get("look") or p["look"].get("regen_seed"):  # this video's own fonts, colours, captions, moves, music
        keep = {k: v for k, v in (p.get("look") or {}).items() if k in ("music_volume", "voice_volume", "sfx_volume")}
        p["look"] = {**looks.generate_for(p["title"], p.get("style", ""), style, (p.get("look") or {}).get("regen_seed")), **keep}
    L = p["look"]
    style = {**style, "accent": L.get("accent") or style.get("accent", "#FFD400"),
             "image_suffix": ", ".join(x for x in (style.get("image_suffix", ""), L.get("flavor", "")) if x)}
    p["log"] = []

    def step(msg, prog):
        p.update(status="working", step=msg, progress=int(prog))
        p["log"].append(time.strftime("%H:%M:%S ") + msg)
        store.save_project(p)

    def log(msg):
        p["log"].append(msg)

    # 1. script
    if not (p.get("script") or "").strip():
        step("Writing the script with AI", 3)
        p["script"] = llm.write_script(cfg, p["title"], p["style"], float(p.get("minutes", 1)), p.get("language", "English"),
                                       p.get("notes", ""), p.get("persona", ""))
        p["scenes"] = []
    # 2. scenes
    if not p.get("scenes"):
        step("Planning scenes, B-roll and on-screen text", 10)
        narr = llm.split_scenes(llm.clean_script(p["script"]))
        if not narr:
            raise RuntimeError("The script is empty.")
        allowed = p.get("graphics")
        if allowed is None:
            allowed = style.get("graphics") or list(graphics.TYPES)
        p["scenes"] = llm.annotate(cfg, narr, p["title"], p["style"], log, allowed)
    scenes = p["scenes"]

    # 3. voice
    step("Recording the voiceover", 18)
    os.makedirs(os.path.join(d, "audio"), exist_ok=True)
    if p.get("avatar_video") and not p.get("voiceover"):
        p["voiceover"], p["voice_mode"] = p["avatar_video"], "upload"  # the avatar clip's own voice drives the timeline
    if p.get("voice_mode") == "upload" and p.get("voiceover"):
        full = tts.decode(os.path.join(d, p["voiceover"]))
        total = len(full) / tts.SR
        chars = [len(s["narration"]) + 1 for s in scenes]
        t = 0.0
        for s, c in zip(scenes, chars):
            s["start"], s["dur"] = round(t, 3), round(total * c / sum(chars), 3)
            s["words"] = tts.spread_words(s["narration"], 0, s["dur"])
            t += s["dur"]
        tts.write_wav(os.path.join(d, "narration.wav"), full)
    else:
        voice, rate = p.get("voice") or cfg["default_voice"], int(p.get("rate", 0))
        age = tts.AGES.get(p.get("age") or "", {})
        pitch = int(p.get("pitch", age.get("pitch", 0)))
        if not voice.startswith("el:"):
            rate += age.get("rate", 0)

        emotion = p.get("emotion") or style.get("emotion") or "natural"
        human = emotion != "off" and not voice.startswith("el:")  # ElevenLabs voices are already expressive

        def speak(i):
            s = scenes[i]
            key = hashlib.md5(f"{s['narration']}|{voice}|{rate}|{pitch}|{emotion if human else ''}".encode()).hexdigest()
            path = os.path.join(d, "audio", f"{key}.{'wav' if human else 'mp3'}")
            if s.get("tts_key") != key or not os.path.exists(path) or not s.get("words"):
                if human:
                    s["words"] = tts.humanize_synth(s["narration"], voice, path, rate, pitch, emotion)
                else:
                    s["words"] = tts.synth(s["narration"], voice, path, rate, pitch)
                s["tts_key"] = key
            s["audio"] = os.path.relpath(path, d)
            return tts.decode(path)

        with ThreadPoolExecutor(4) as ex:
            clips = list(ex.map(speak, range(len(scenes))))
        t, parts = 0.0, []
        gap = np.zeros(int(GAP * tts.SR), dtype=np.float32)
        for s, c in zip(scenes, clips):
            s["start"], s["dur"] = round(t, 3), round(len(c) / tts.SR + GAP, 3)
            parts += [c, gap]
            t += s["dur"]
        tts.write_wav(os.path.join(d, "narration.wav"), np.concatenate(parts))
    total = sum(s["dur"] for s in scenes)

    # 4. visuals
    step("Finding B-roll and generating images", 30)
    vdir = os.path.join(d, "visuals")
    os.makedirs(vdir, exist_ok=True)
    has_avatar = bool(p.get("avatar")) and os.path.exists(os.path.join(d, p["avatar"]))
    has_avatar_video = bool(p.get("avatar_video")) and os.path.exists(os.path.join(d, p["avatar_video"]))
    used, done = set(), [0]
    aroll_ids = [i for i, s in enumerate(scenes) if s.get("kind") == "aroll"]
    split_ids = {i for k, i in enumerate(aroll_ids) if k % 3 == 2 and scenes[i]["dur"] >= 4} if style.get("split_screen") else set()
    if p.get("style_prompt"):
        style = {**style, "image_suffix": p["style_prompt"] + ", " + style.get("image_suffix", "")}

    def visuals(i):
        s = scenes[i]
        n = max(1, round(s["dur"] / float(style.get("shot_seconds", 5))))
        g = graphics.parse(s.get("graphic", "")) if s.get("graphic") else None
        if s.get("locked") and s.get("assets") and all(os.path.exists(os.path.join(d, a["path"])) for a in s["assets"]):
            for a in s["assets"]:
                if a.get("source", "").startswith("avatar video"):
                    a["ss"] = s["start"]  # keep the host's lips in sync after scenes were moved
            done[0] += 1
            return  # the owner arranged this scene's shots by hand in the editor
        if g and not s.get("custom"):
            extra = OUTRO + 1 if i == len(scenes) - 1 else 1.0
            key = hashlib.md5(f"{s['graphic']}|{s['dur']}|{w}x{h}|{style.get('accent')}|{L.get('map_theme')}".encode()).hexdigest()[:12]
            gp = os.path.join(vdir, f"graphic_{key}.mp4")
            try:
                if not os.path.exists(gp):
                    portrait = None
                    if g["type"] == "card":
                        try:
                            portrait = os.path.join(d, media.fetch({**s, "image_prompt": f"portrait of {g['name']}, {g['role']}, realistic painting, head and shoulders"},
                                                                    1, cfg, style, vdir, 640, 800, used, "ai_image", log, i + 700)[0]["path"])
                        except Exception:
                            portrait = None
                    graphics.render(g, gp, s["dur"] + extra, w, h, style.get("accent", "#FFD400"),
                                    s.get("text", "") if g["type"] in ("bars", "timeline", "compare", "icons") else "", portrait,
                                    L.get("map_theme") or "navy")
                s["assets"] = [{"path": os.path.relpath(gp, d), "type": "video", "source": "motion graphic", "credit": ""}]
                done[0] += 1
                return
            except Exception as e:
                log(f"  Graphic '{s['graphic']}' failed, using B-roll instead ({e})")
        if style.get("renderer") == "stick2d" and not s.get("custom"):
            key = hashlib.md5(f"{s['narration']}|{s.get('text')}|{s['dur']}|{s['start']}|{w}x{h}|{i}".encode()).hexdigest()[:12]
            sp = os.path.join(vdir, f"stick_{key}.mp4")
            if not os.path.exists(sp):
                prop = None
                if i % 2 == 0:  # every other scene gets an illustrated prop card, the rest a checklist
                    try:
                        prop = os.path.join(d, media.fetch(s, 1, cfg, style, vdir, 768, 768, used, "ai_image", log, i + 900)[0]["path"])
                    except Exception as e:
                        log(f"  prop image failed ({e})")
                extra = OUTRO + 1 if i == len(scenes) - 1 else 1.0
                stick2d.render(s, i, sp, s["dur"] + extra, w, h, style.get("accent", "#FFB347"), prop,
                               os.path.join(d, "narration.wav"), s["start"])
            s["assets"] = [{"path": os.path.relpath(sp, d), "type": "video", "source": "motion graphic", "credit": ""}]
            done[0] += 1
            return
        if s.get("kind") == "aroll" and has_avatar_video and not s.get("custom"):
            s["assets"] = [{"path": p["avatar_video"], "type": "video", "source": "avatar video", "credit": "", "ss": s["start"]}]
            if i in split_ids:  # host on one half, the thing they talk about on the other
                b = media.fetch(s, 1, cfg, style, vdir, w // 2, h, used, p.get("source") or style.get("source", "mix"), log, i + 500)[0]
                s["assets"][0].update(type="split", b=b["path"], btype=b["type"], credit=b.get("credit", ""))
        elif s.get("kind") == "aroll" and has_avatar and not s.get("custom"):
            clip = avatar.lipsync(cfg, os.path.join(d, p["avatar"]), os.path.join(d, s.get("audio") or f"audio/{s.get('tts_key')}.mp3"),
                                  os.path.join(vdir, f"aroll_{s.get('tts_key')}.mp4"), log)
            s["assets"] = [{"path": os.path.relpath(clip, d), "type": "video", "source": "avatar lip-sync", "credit": ""}] if clip else \
                          [{"path": p["avatar"], "type": "image", "source": "avatar", "credit": "", "still": True}]
        elif s.get("custom") and s.get("assets") and os.path.exists(os.path.join(d, s["assets"][0]["path"])):
            s["assets"] = s["assets"][:1]
        else:
            ok = s.get("assets") and (len(s["assets"]) == n or s.get("locked")) and all(
                os.path.exists(os.path.join(d, a["path"])) and a.get("source") not in ("avatar", "avatar lip-sync", "avatar video", "motion graphic") for a in s["assets"])
            if not ok:
                s["custom"] = False
                s["assets"] = media.fetch(s, n, cfg, style, vdir, w, h, used, p.get("source") or style.get("source", "mix"), log, i)
        done[0] += 1
        p.update(progress=30 + int(25 * done[0] / len(scenes)))
        if done[0] % 5 == 0:
            store.save_project(p)

    with ThreadPoolExecutor(4) as ex:
        list(ex.map(visuals, range(len(scenes))))
    store.save_project(p)

    # 5. music
    music = None
    mood = p.get("music") or style.get("music", "cinematic")
    if mood and mood != "none":
        step("Adding background music", 56)
        music = os.path.join(d, "music.wav")
        lib = os.path.join(store.MUSIC, os.path.basename(mood))
        if os.path.exists(lib):
            track = tts.decode(lib)
            reps = int((total + OUTRO) * tts.SR / max(1, len(track))) + 1
            track = np.tile(track, reps)[: int((total + OUTRO) * tts.SR)]
            fade = int(2 * tts.SR)
            if len(track) > 2 * fade:
                track[-fade:] *= np.linspace(1, 0, fade)
            tts.write_wav(music, track)
        else:
            tts.write_wav(music, tts.make_music(mood, total + OUTRO, L.get("music_seed")))

    # 6. edit plan: camera moves, transitions, outro
    step("Editing: camera moves, transitions, motion graphics", 58)
    moves = L.get("moves") or style.get("moves") or render.MOVES
    transitions = [None if t in ("", "cut") else t for t in (L.get("transitions") or style.get("transitions") or ["fade"])]
    look_grade = looks.FILTERS.get(L.get("grade") or "", "")
    shots, boundaries, mi, timeline, tpos = [], [], 0, [], 0.0
    for si, s in enumerate(scenes):
        n = len(s["assets"])
        dur_s = s["dur"] + (OUTRO if si == len(scenes) - 1 else 0)
        wsum = sum(float(a.get("weight") or 1) for a in s["assets"]) or 1
        for k, a in enumerate(s["assets"]):
            dur = round((dur_s * float(a.get("weight") or 1) / wsum) * render.FPS) / render.FPS
            host = a.get("source", "").startswith("avatar")
            gfx = a.get("source") == "motion graphic"
            trans = None
            if k == 0 and si > 0:
                if s.get("trans"):  # set by hand in the editor
                    trans = None if s["trans"] == "cut" else s["trans"]
                else:
                    trans = transitions[(si - 1) % len(transitions)]
                    prev_host = scenes[si - 1]["assets"][-1].get("source", "").startswith("avatar")
                    if host and prev_host:
                        trans = None  # talking head to talking head: clean jump cut
                if trans:
                    boundaries.append(s["start"])
            if a.get("move"):
                move = a["move"]
            elif si == 0 and k == 0:
                move = "push_in"  # opening shot always pushes in
            elif host:
                move = "handheld"
            else:
                move = moves[mi % len(moves)]
                mi += 1
            grade = style.get("host_grade", "eq=saturation=1.05:gamma_r=1.03") if host else ("" if gfx else style.get("grade", ""))
            extra_f = [x for x in (look_grade if not (host or gfx) else "", looks.FILTERS.get(a.get("filter") or "", "")) if x]
            grade = ",".join([x for x in [grade] + extra_f if x])
            if move in ("card", "circles") and a["type"] != "image":
                move = "push_in"  # compositions are for photos
            if move == "circles" and not a.get("b"):
                other = next((x for x in s["assets"] if x is not a and x["type"] == "image"), None) or \
                        next((x for sc2 in scenes for x in sc2["assets"] if x is not a and x["type"] == "image" and x.get("source") != "motion graphic"), None)
                a = {**a, "b": other["path"] if other else None}
            shots.append({"asset": {**a, "path": os.path.join(d, a["path"]), "root": d, "accent": style.get("accent")}, "dur": dur, "move": move, "trans": trans,
                          "slowmo": bool(style.get("slowmo")) and a["type"] == "video" and not host and not gfx,
                          "speed": float(a.get("speed") or 1.0), "grade": grade})
            timeline.append({"scene": si, "k": k, "start": round(tpos, 2), "dur": dur, "move": move, "trans": trans or "cut",
                             "filter": a.get("filter") or "", "type": a["type"], "source": a.get("source", ""), "path": a["path"],
                             "b": a.get("b")})
            tpos += dur
    total_v = total + OUTRO
    drift = total_v - sum(x["dur"] for x in shots)
    shots[-1]["dur"] = max(0.4, shots[-1]["dur"] + drift)
    timeline[-1]["dur"] = shots[-1]["dur"]
    p["timeline"] = timeline

    sfx_path = None
    if p.get("sfx", style.get("sfx", True)) or style.get("ambience", "none") != "none":
        step("Sound design: whooshes, hits, risers, ambience", 60)
        sfx_path = os.path.join(d, "sfx.wav")
        track = sfx.design(scenes, total_v, boundaries, total + 0.2, style.get("ambience", "none"),
                           1.0 if p.get("sfx", style.get("sfx", True)) else 0.0)
        if not p.get("sfx", style.get("sfx", True)):
            track = sfx.ambience(total_v, style.get("ambience")) * 0.05
        tts.write_wav(sfx_path, track)
    if music:
        tts.write_wav(music, _extend_music(music, total_v, mood))

    hindi = any("\u0900" <= ch <= "\u097f" for ch in p["script"])
    pw, ph = (render.PREVIEW if preview else render.SIZES).get(p.get("aspect", "16:9"))
    credits = sorted({a["credit"] for s in scenes for a in s["assets"] if a.get("credit")})
    render.build_ass(os.path.join(d, "subs.ass"), scenes, pw, ph, style, p.get("captions", style.get("captions", True)),
                     p["title"] if p.get("show_title", style.get("show_title", True)) else None, hindi,
                     total + 0.2 if OUTRO else None, total_v, credits, L)
    step("Rendering shots and the final mix", 62)
    name = "video.mp4"
    render.render(p, shots, os.path.join(d, "narration.wav"), music, sfx_path, os.path.join(d, name),
                  lambda f: p.update(progress=62 + int(30 * f)) or store.save_project(p), preview, int(style.get("grain", 0)), L)
    total = total_v

    # 7. upload pack + thumbnail
    step("Writing titles, description and tags", 93)
    if not p.get("meta"):
        p["meta"] = llm.metadata(cfg, p["title"], p["script"], p.get("language", "English"))
    step("Designing 3 thumbnails", 96)
    make_thumb(p)
    try:
        import thumbref
        ref = None
        if p.get("thumb_ref"):
            ref = thumbref.fetch_reference(p["thumb_ref"], os.path.join(d, "thumb_ref.jpg"))
        subject = os.path.join(d, p["avatar"]) if p.get("avatar") else None
        files, _ = thumbref.make_variants(cfg, p["title"], scenes[0].get("image_prompt") or p["title"], ref, d,
                                          p.get("thumb_text") or (p.get("meta") or {}).get("thumb_text"), subject,
                                          style.get("image_suffix", ""))
        p["thumbs"] = [os.path.basename(f) for f in files]
        p["thumb"] = p["thumbs"][0]
    except Exception as e:
        log(f"  Extra thumbnails failed: {e}")
    p["credits"] = sorted({a["credit"] for s in scenes for a in s["assets"] if a.get("credit")})
    p.update(status="done", progress=100, step="Finished", duration=round(total, 1), video=name, version=int(time.time()),
             preview=bool(preview))
    p["log"].append(time.strftime("%H:%M:%S ") + "Finished")
    store.save_project(p)


def _extend_music(path, seconds, mood):
    m = tts.decode(path)
    need = int(seconds * tts.SR)
    if len(m) < need:
        m = np.concatenate([m, tts.make_music(mood if mood in tts.MOODS else "cinematic", (need - len(m)) / tts.SR + 1)])
    return m[:need]


def make_thumb(p, text=None, layout="left"):
    d = store.pdir(p["id"])
    cfg = store.get_settings()
    style = cfg["styles"].get(p.get("style"), cfg["styles"]["documentary"])
    bg = os.path.join(d, "thumb_bg.jpg")
    shots = sorted(f for f in os.listdir(os.path.join(d, "shots")) if f.endswith(".mp4")) if os.path.isdir(os.path.join(d, "shots")) else []
    pick = next((os.path.join(d, a["path"]) for s in p["scenes"] for a in s.get("assets", []) if a["type"] == "image"
                 and not a.get("source", "").startswith(("avatar", "generated"))), None)
    if pick:
        bg = pick
    elif shots:
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", os.path.join(d, "shots", shots[len(shots) // 3]), "-frames:v", "1", bg])
    subject = os.path.join(d, p["avatar"]) if p.get("avatar") else None
    text = text or (p.get("meta") or {}).get("thumb_text") or " ".join(p["title"].split()[:3])
    thumb.make(os.path.join(d, "thumb.jpg"), text, bg if os.path.exists(bg) else None, subject, layout, style.get("accent", "#FFD400"))
    p["thumb"] = "thumb.jpg"
