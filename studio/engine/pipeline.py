"""Project store, the generation job (script → voice → visuals → timeline → sound → render) and editor operations."""
import os
import queue
import random
import shutil
import subprocess
import sys
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor

import numpy as np

from . import avatar, catalog, compose, core, media, mg, sound, thumb, voice, writer

FPS = 30
_plock = threading.RLock()
_jobs = queue.Queue()
_state = {"current": None, "queue": []}
_cancel = set()

TRANS_SFX = {"push": "whoosh", "slide": "whoosh", "wipe": "whoosh", "zoom": "zoom", "dip": "hit", "glitch": "glitch", "flash": "flash", "burn": "burn", "pop": "pop"}
MG_SFX = {"title": "hit", "timeline": "tick", "clock": "tick", "stat": "pop", "counter": "pop", "list": "pop", "document": "typing", "quote": "typing",
          "world_map": "whoosh", "route_map": "whoosh", "bar_chart": "pop", "compare": "pop", "keywords": "hit", "icon_grid": "pop", "ring": "riser"}
COMPANION = {"cinematic": ["cinematic", "suspense", "emotional"], "suspense": ["suspense", "dark", "tension"], "emotional": ["emotional", "ambient", "cinematic"],
             "ambient": ["ambient", "emotional"], "tension": ["tension", "suspense", "cinematic"], "upbeat": ["upbeat", "curious"], "curious": ["curious", "upbeat", "ambient"],
             "warm": ["warm", "curious"], "epic": ["epic", "tension", "emotional"], "dark": ["dark", "suspense"], "playful": ["playful", "curious"]}


# ------------------------------------------------------------------ store
def pdir(pid):
    return os.path.join(core.PROJECTS, pid)


def load(pid):
    p = core.load_json(os.path.join(pdir(pid), "project.json"))
    if p:
        p["progress"] = core.load_json(os.path.join(pdir(pid), "progress.json"), {}) or {}
    return p


def save(p):
    with _plock:
        d = {k: v for k, v in p.items() if k != "progress"}
        core.save_json(os.path.join(p["dir"], "project.json"), d)


def set_progress(p, stage, pct, msg, error=None):
    pr = core.load_json(os.path.join(p["dir"], "progress.json"), {}) or {}
    log = pr.get("log", [])
    if not log or log[-1]["msg"] != msg:
        log.append({"t": time.time(), "msg": msg})
    pr = {"stage": stage, "pct": round(float(pct), 4), "msg": msg, "log": log[-60:], "error": error, "updated": time.time(),
          "started": pr.get("started") or time.time()}
    core.save_json(os.path.join(p["dir"], "progress.json"), pr)


def list_projects():
    out = []
    for pid in os.listdir(core.PROJECTS):
        p = core.load_json(os.path.join(pdir(pid), "project.json"))
        if p:
            pr = core.load_json(os.path.join(pdir(pid), "progress.json"), {}) or {}
            out.append({"id": p["id"], "title": p["title"], "status": p["status"], "created": p["created"], "format": p["settings"]["format"],
                        "duration": p.get("duration"), "minutes": p["settings"]["duration_min"], "has_video": bool((p.get("outputs") or {}).get("preview")),
                        "has_final": bool((p.get("outputs") or {}).get("video")), "thumb": bool((p.get("outputs") or {}).get("thumbnail")),
                        "pct": pr.get("pct", 0), "msg": pr.get("msg", "")})
    return sorted(out, key=lambda x: -x["created"])


def default_settings(fmt="documentary"):
    f = catalog.FORMATS.get(fmt, catalog.FORMATS["documentary"])
    s = core.get_settings()
    return {"language": "en", "duration_min": 3, "format": fmt, "aspect": f.get("aspect", "16:9"), "resolution": s.get("default_resolution", 1080),
            "voice": "andrew_doc", "theme": f["theme"], "captions": f["captions"], "music": f["music"], "music_volume": 0.5, "sfx": True, "sfx_volume": 0.7,
            "pace": f["pace"], "motion_graphics": [k for k, _ in catalog.MOTION_GRAPHICS if k not in ("credits",)],
            "sources": {"stock_video": True, "stock_photo": True, "archive": True, "ai": True}, "blocklist": "", "humanize": True,
            "voice_fx": True, "avatar_pip": False, "ambience": "", "ai_style": ""}


def create(data):
    pid = core.uid(10)
    d = pdir(pid)
    os.makedirs(os.path.join(d, "media"), exist_ok=True)
    fmt = data.get("format") or (data.get("settings") or {}).get("format") or "documentary"
    st = default_settings(fmt)
    st.update({k: v for k, v in (data.get("settings") or {}).items() if v is not None})
    mx = float(core.get_settings().get("max_minutes", 60))
    st["duration_min"] = max(0.3, min(mx, float(st.get("duration_min") or 3)))
    title = (data.get("title") or (data.get("prompt") or "Untitled video").split("\n")[0])[:100]
    p = {"id": pid, "dir": d, "title": title, "title_locked": bool(data.get("title_locked")), "prompt": (data.get("prompt") or title)[:10000],
         "own_script": (data.get("script") or "").strip() or None, "voice_upload": data.get("voice_upload"), "created": time.time(),
         "status": "draft", "settings": st, "seed": core.seed_of(pid, title), "brand": data.get("brand") or {},
         "persona": data.get("persona") or {}, "avatar": data.get("avatar") or {}, "thumb_choice": data.get("thumbnail") or {},
         "beats": [], "shots": [], "overlays": [], "captions": [], "outputs": {}}
    save(p)
    set_progress(p, "draft", 0, "Created")
    return p


def delete(pid):
    shutil.rmtree(pdir(pid), ignore_errors=True)


def estimate(st):
    """Rough minutes of processing for the review screen."""
    m = float(st.get("duration_min") or 3)
    shots = m * 60 / float(st.get("pace") or 4.5)
    return {"shots": int(shots), "words": int(m * writer.wpm(st.get("format"))), "minutes": round(1.2 + m * 1.6 + shots * 0.05, 1),
            "credits": int(m * 55)}


# ------------------------------------------------------------------ timeline
def caption_groups(beats):
    caps = []
    for b in beats:
        if b.get("silent") or not b.get("words"):
            continue
        cur = []
        for w in b["words"]:
            cur.append({"w": w["w"], "s": round(b["start"] + w["s"], 3), "e": round(b["start"] + w["e"], 3)})
            chars = sum(len(x["w"]) + 1 for x in cur)
            if chars >= 70 or (len(cur) >= 5 and w["w"][-1:] in ".,!?;:।") or len(cur) >= 13:
                caps.append({"start": cur[0]["s"], "end": cur[-1]["e"], "words": cur})
                cur = []
        if cur:
            caps.append({"start": cur[0]["s"], "end": cur[-1]["e"], "words": cur})
    return caps


def apply_times(p):
    """Beats own time. Shots, plan overlays, captions and chapter marks are all derived from them."""
    t = 0.6
    fixed = any("abs_start" in b for b in p["beats"])
    for i, b in enumerate(p["beats"]):
        if fixed:
            b["start"] = b["abs_start"]
            nxt = p["beats"][i + 1]["abs_start"] if i + 1 < len(p["beats"]) else b["abs_start"] + b["vdur"] + 1.6
            b["span"] = max(0.3, nxt - b["start"])
        else:
            b["start"] = round(t, 3)
            b["span"] = round(b["vdur"] + b.get("gap", 0.3), 3)
            t += b["span"]
    if p["beats"] and not fixed:
        p["beats"][-1]["span"] += 1.4
    end = p["beats"][-1]["start"] + p["beats"][-1]["span"] if p["beats"] else 1
    for s in p["shots"]:
        b = p["beats"][s["b"]]
        s["start"] = round(b["start"] + s["f0"] * b["span"], 3)
        s["dur"] = round((s["f1"] - s["f0"]) * b["span"], 3)
    p["shots"].sort(key=lambda s: s["start"])
    if p["shots"]:
        p["shots"][0]["dur"] += p["shots"][0]["start"]
        p["shots"][0]["start"] = 0.0
    for o in p["overlays"]:
        if o.get("b") is not None and o["b"] < len(p["beats"]):
            o["start"] = round(p["beats"][o["b"]]["start"] + o.get("off", 0), 3)
    p["captions"] = caption_groups(p["beats"])
    p["duration"] = round(end, 3)
    ch, seen = [], set()
    titles = [c["title"] for c in (p.get("outline") or {}).get("chapters", [])]
    for b in p["beats"]:
        if b["chapter"] not in seen and not b.get("silent"):
            seen.add(b["chapter"])
            ch.append({"t": b["start"] if len(seen) > 1 else 0, "title": titles[b["chapter"]] if b["chapter"] < len(titles) else "Part %d" % (b["chapter"] + 1)})
    p["chapters_time"] = ch


def build_timeline(p):
    st = p["settings"]
    fmt = st["format"]
    rnd = random.Random(p["seed"])
    T = catalog.THEMES[st["theme"]]
    pace = float(st.get("pace") or 4.5)
    allowed = set(st.get("motion_graphics") or [])
    minutes = float(st["duration_min"])
    titles = [c["title"] for c in (p.get("outline") or {}).get("chapters", [])]
    fixed = any("abs_start" in b for b in p["beats"])
    # 1. chapter title cards become silent beats
    beats = []
    last_ch = 0
    for b in [x for x in p["beats"] if not x.get("silent")]:
        if b["chapter"] != last_ch and "title" in allowed and minutes >= 3 and not fixed and fmt not in ("avatar", "shorts"):
            n = b["chapter"]
            beats.append({"text": "", "silent": True, "vdur": 2.3, "gap": 0.25, "chapter": n, "kind": "mg", "words": [],
                          "mg": {"type": "title", "text": titles[n] if n < len(titles) else "Part %d" % (n + 1), "sub": "Chapter %d" % (n + 1), "n": str(n + 1)}})
            if beats and len(beats) > 1:
                beats[-2]["gap"] = 0.7
        last_ch = b["chapter"]
        b["gap"] = 0.5 if b.get("emotion") in ("tense", "mystery", "sad") else 0.3
        beats.append(b)
    p["beats"] = beats
    # 2. which beats show the avatar (A-roll)
    aroll = set()
    if fmt == "avatar":
        run_b, seen_ch = 0, set()
        for i, b in enumerate(beats):
            first = b["chapter"] not in seen_ch
            seen_ch.add(b["chapter"])
            want = i < 2 or first or i >= len(beats) - 2 or run_b >= rnd.randint(2, 4)
            if want and not (i - 1 in aroll and i - 2 in aroll and i >= 3):
                aroll.add(i)
                run_b = 0
            else:
                run_b += 1
    motions = [m for m in catalog.MOTIONS if m not in ("static", "split", "card", "polaroid", "parallax")]
    framed = ["card", "polaroid", "parallax"]
    shots, overlays, last_motion = [], [], None
    n_shot = 0
    for bi, b in enumerate(beats):
        span = b["vdur"] + b.get("gap", 0.3)
        mgs = b.get("mg") if (b.get("silent") or (b.get("mg") and b["mg"].get("type") in allowed)) else None
        plan = b
        new_ch = bi > 0 and beats[bi - 1]["chapter"] != b["chapter"]

        def add(f0, f1, kind, **kw):
            nonlocal n_shot, last_motion
            s = {"id": "s%04d" % n_shot, "b": bi, "f0": round(f0, 4), "f1": round(f1, 4), "kind": kind, "v": rnd.randint(0, 9999), "filter": "none",
                 "speed": 1.0, "variant": kw.pop("variant", 0)}
            first_of_beat = f0 == 0
            if n_shot == 0:
                tr = "cut"
            elif kind == "mg" or (first_of_beat and new_ch):
                tr = rnd.choice(["dip", "fade", T["transitions"][0]])
            elif fmt == "avatar" and (kind == "avatar" or shots[-1]["kind"] == "avatar"):
                tr = "cut"
            elif not first_of_beat:
                tr = rnd.choice(["cut", "cut", "fade"] if pace < 4.4 else ["cut", "fade", "fade"])
            else:
                tr = rnd.choice(T["transitions"])
            s["transition"], s["tdur"] = tr, round(rnd.uniform(0.35, 0.6), 2)
            m = rnd.choice([x for x in motions if x != last_motion])
            if rnd.random() < (0.3 if T["key"] in ("paper", "archive", "casefile") else 0.08):
                m = rnd.choice(framed)
            s["motion"] = last_motion = m
            s["focus"] = [round(rnd.uniform(0.4, 0.6), 2), round(rnd.uniform(0.36, 0.52), 2)]
            s.update(kw)
            shots.append(s)
            n_shot += 1
            return s
        if mgs and mgs["type"] in mg.OVERLAY:
            overlays.append(dict(mgs, id=core.uid(6), b=bi, off=0.5, dur=round(min(4.5, span - 0.6), 2), v=rnd.randint(0, 99)))
            mgs = None
        if bi in aroll:
            if span > 7.5:
                cut = b["words"][len(b["words"]) // 2]["s"] / span if b.get("words") else 0.5
                add(0, cut, "avatar", v=3)
                add(cut, 1, "avatar", v=4)
            else:
                add(0, 1, "avatar", v=rnd.choice([1, 2, 3, 5]))
            continue
        if mgs and span >= 2.2:
            if span <= 8.5:
                add(0, 1, "mg", mg=mgs)
            else:
                cut = (span - 6.0) / span
                add(0, cut, "anim2d" if fmt in ("anim2d", "kids") else "visual", plan=1)
                add(cut, 1, "mg", mg=mgs)
            continue
        n = max(1, int(round(span / pace)))
        while n > 1 and span / n < 2.4:
            n -= 1
        for k in range(n):
            if fmt in ("anim2d", "kids") or (fmt == "whatif" and b.get("cast") and rnd.random() < 0.5):
                cast = b.get("cast") or [{"pose": rnd.choice(["stand", "talk", "think", "point", "walk"]), "expr": {"tense": "fear", "sad": "sad", "excited": "happy"}.get(b.get("emotion"), "neutral")}]
                add(k / n, (k + 1) / n, "anim2d", variant=k, cast=cast if k == 0 else [dict(c, pose=rnd.choice(["stand", "look_up", "think", "talk"])) for c in cast[:1]],
                    bubble=b.get("bubble", "") if k == 0 else "")
            else:
                add(k / n, (k + 1) / n, "visual", variant=k)
        if b.get("key") and "keywords" in allowed and rnd.random() < 0.4 and span > 2.4:
            off = 0.3
            for w in b.get("words", []):
                if b["key"].split()[0].lower().strip(".,") in w["w"].lower():
                    off = max(0.1, w["s"] - 0.05)
                    break
            overlays.append({"id": core.uid(6), "type": "keytext", "text": b["key"], "b": bi, "off": round(off, 2), "dur": round(min(2.4, span - off), 2),
                             "v": rnd.randint(0, 9), "pos": rnd.choice(["top", "low", "low"])})
    if "credits" in allowed and not fixed and minutes >= 2:
        beats.append({"text": "", "silent": True, "vdur": 5.0, "gap": 0.2, "chapter": beats[-1]["chapter"], "kind": "mg", "words": [], "mg": {"type": "credits", "lines": []}})
        shots.append({"id": "s%04d" % n_shot, "b": len(beats) - 1, "f0": 0, "f1": 1, "kind": "mg", "v": 1, "filter": "none", "speed": 1.0, "variant": 0,
                      "transition": "dip", "tdur": 0.6, "motion": "static", "focus": [0.5, 0.5], "mg": beats[-1]["mg"]})
    p["shots"], p["overlays"] = shots, overlays
    apply_times(p)


def fetch_visuals(p, progress, only=None):
    st = p["settings"]
    folder = os.path.join(p["dir"], "media")
    portrait = st.get("aspect") == "9:16"
    used = set(s["asset"]["id"] for s in p["shots"] if s.get("asset") and s["asset"].get("id"))
    todo = [s for s in p["shots"] if s["kind"] in ("visual", "anim2d") and not s.get("asset") and (only is None or s["id"] in only)]
    done = [0]
    rnd = random.Random(p["seed"] + 5)

    def job(s):
        b = p["beats"][s["b"]]
        plan = dict(b)
        if s["kind"] == "anim2d":
            plan = dict(b, kind="ai", prompt="Background set only: " + b.get("prompt", b["text"]))
        try:
            a = media.pick(plan, s.get("variant", 0), st, used, folder, p["seed"] + s["v"], portrait)
        except Exception:
            a = None
        if a:
            if a["kind"] == "video":
                slack = a.get("dur", 0) - s["dur"] - 0.5
                s["offset"] = round(rnd.uniform(0, slack), 2) if slack > 0.5 else 0.0
            s["asset"] = a
        done[0] += 1
        progress(done[0] / max(1, len(todo)), "Finding visuals %d/%d" % (done[0], len(todo)))
    with ThreadPoolExecutor(6) as ex:
        list(ex.map(job, todo))
    # motion graphics sit on a blurred copy of a neighbouring picture half the time
    prev = None
    for s in p["shots"]:
        if s["kind"] == "mg" and not s.get("asset") and prev and s["v"] % 2 == 0 and s["mg"].get("type") != "credits":
            s["asset"] = dict(prev, borrowed=True)
        if s.get("asset") and s["asset"].get("kind") == "image" and not s["asset"].get("borrowed"):
            prev = s["asset"]
    credits = sorted({s["asset"]["credit"] for s in p["shots"] if s.get("asset") and s["asset"].get("credit")})
    for s in p["shots"]:
        if s["kind"] == "mg" and s["mg"].get("type") == "credits":
            s["mg"]["lines"] = (["Narration: AI voice", "Music and sound design: original, generated for this video"] +
                                (["Some images in this video are AI-generated illustrations"] if any((x.get("asset") or {}).get("src") == "ai" for x in p["shots"]) else []) + credits)[:60]


def ensure_avatar(p, progress=lambda f, m: None):
    if p["settings"]["format"] != "avatar" and not p["settings"].get("avatar_pip"):
        return
    av = p.setdefault("avatar", {})
    if not p.get("persona") or not p["persona"].get("look"):
        progress(0.2, "Designing your host")
        p["persona"] = writer.make_persona(p["prompt"] or p["title"], (p.get("persona") or {}).get("bible", "") or (p.get("brand") or {}).get("persona", ""))
    if not av.get("image") or not os.path.exists(av["image"]):
        progress(0.5, "Creating the avatar")
        for k in range(4):
            dest = os.path.join(p["dir"], "media", "avatar_%d.jpg" % k)
            try:
                media.ai_image(avatar.portrait_prompt(p["persona"]), dest, 1280, 720, p["seed"] + k * 17, "home")
                info = avatar.detect(dest)
                av.update(image=dest, info=info)
                if info["found"]:
                    break
            except Exception:
                continue
    elif not av.get("info"):
        av["info"] = avatar.detect(av["image"])


def build_audio(p, progress=lambda f, m: None):
    st = p["settings"]
    d = p["dir"]
    dur = p["duration"]
    vw = os.path.join(d, "voice.wav")
    progress(0.1, "Assembling the voice track")
    if p.get("voice_upload") and any("abs_start" in b for b in p["beats"]):
        core.run(["ffmpeg", "-y", "-v", "error", "-i", p["voice_upload"], "-ac", "1", "-ar", str(sound.SR), "-c:a", "pcm_s16le", vw])
    else:
        sound.build_voice(vw, dur, [(b["start"], b["audio"], b["vdur"]) for b in p["beats"] if b.get("audio")])
    np.save(os.path.join(d, "voice_env_30.npy"), sound.envelope(vw, 30))
    progress(0.3, "Composing music")
    mood = st.get("music") or "cinematic"
    sections = [(0.0, mood)]
    if mood != "none" and dur > 150:
        comp = COMPANION.get(mood, [mood])
        marks = [c["t"] for c in p.get("chapters_time", [])][1:]
        k, last = 0, 0.0
        for t in marks:
            if t - last >= 75:
                k += 1
                sections.append((t, comp[k % len(comp)]))
                last = t
    p["music_sections"] = sections
    sound.build_music(os.path.join(d, "music.wav"), dur, mood, p["seed"], sections)
    progress(0.6, "Designing sound effects")
    cues = []
    rnd = random.Random(p["seed"] + 9)
    if st.get("sfx", True):
        for i, s in enumerate(p["shots"]):
            if i and s.get("transition") in TRANS_SFX and (s["kind"] == "mg" or rnd.random() < 0.6):
                cues.append((s["start"], TRANS_SFX[s["transition"]], 0.5))
            if s["kind"] == "mg":
                cues.append((s["start"] + 0.25, MG_SFX.get(s["mg"].get("type"), "pop"), 0.55))
        for b in p["beats"]:
            if b.get("sfx") and b["sfx"] != "none" and not b.get("silent"):
                cues.append((b["start"] + (0.0 if b["sfx"] != "riser" else b["vdur"]), b["sfx"], 0.5))
        for o in p["overlays"]:
            cues.append((o["start"], {"keytext": "pop", "callout": "click", "lower_third": "whoosh", "text": "pop"}.get(o.get("type"), "pop"), 0.4))
        cues += [(float(c["t"]), c["name"], float(c.get("gain", 0.6))) for c in p.get("user_sfx", [])]
    p["sfx_cues"] = [{"t": round(t, 2), "name": n} for t, n, g in sorted(cues)]
    sound.build_sfx(os.path.join(d, "sfx.wav"), dur, cues, p["seed"], st.get("ambience") or None)
    progress(0.85, "Mixing and mastering")
    sound.mix(vw, os.path.join(d, "music.wav"), os.path.join(d, "sfx.wav"), os.path.join(d, "audio.m4a"),
              float(st.get("music_volume", 0.5)), float(st.get("sfx_volume", 0.7)), st.get("voice_fx", True), st.get("voice_reverb", False))


def write_srt(p):
    def ts(t):
        return "%02d:%02d:%02d,%03d" % (t // 3600, t % 3600 // 60, t % 60, int(t * 1000) % 1000)
    out = []
    for i, c in enumerate(p["captions"]):
        out.append("%d\n%s --> %s\n%s\n" % (i + 1, ts(c["start"]), ts(c["end"] + 0.1), " ".join(w["w"] for w in c["words"])))
    path = os.path.join(p["dir"], "captions.srt")
    open(path, "w", encoding="utf-8").write("\n".join(out))
    return path


def render(p, progress=lambda f, m: None, final=False):
    """Parallel frame render + mux. final=False makes the fast 480p editor preview."""
    d = p["dir"]
    save(p)
    snap = os.path.join(d, "render_snapshot.json")
    core.save_json(snap, {k: v for k, v in p.items() if k != "progress"})
    r = compose.Renderer(p)
    W, H = (r.W, r.H) if final else ((854, 480) if r.VW > r.VH else (480, 854))
    r.close()
    fps = FPS if final else 24
    total = int(p["duration"] * fps)
    jobs = max(1, min(int(core.get_settings().get("render_jobs") or 2), 8, total // (fps * 4) or 1))
    parts_dir = os.path.join(d, "parts_final" if final else "parts_prev")
    shutil.rmtree(parts_dir, ignore_errors=True)
    os.makedirs(parts_dir)
    step = -(-total // jobs)
    procs, parts = [], []
    for j in range(jobs):
        f0, f1 = j * step, min(total, (j + 1) * step)
        if f0 >= f1:
            break
        out = os.path.join(parts_dir, "part%03d.mp4" % j)
        parts.append((out, f1 - f0))
        procs.append(subprocess.Popen([sys.executable, "-m", "engine.compose", snap, str(f0), str(f1), out, str(fps), str(W), str(H),
                                       "19" if final else "27", "veryfast" if final else "ultrafast"], cwd=core.ROOT, stderr=subprocess.PIPE))
    t0 = time.time()
    while any(pr.poll() is None for pr in procs):
        done = 0
        for out, n in parts:
            try:
                done += int(open(out + ".prog").read() or 0)
            except Exception:
                pass
        el = time.time() - t0
        eta = el / max(1, done) * (total - done)
        progress(done / max(1, total), "Rendering %s  %d%%  (about %s left)" % ("final video" if final else "preview", 100 * done // max(1, total), core.fmt_time(eta)))
        if p["id"] in _cancel:
            for pr in procs:
                pr.kill()
            raise RuntimeError("Cancelled")
        time.sleep(1.5)
    for pr in procs:
        if pr.returncode != 0:
            raise RuntimeError("Render worker failed: %s" % pr.stderr.read().decode("utf-8", "ignore")[-700:])
    lst = os.path.join(parts_dir, "list.txt")
    open(lst, "w").write("".join("file '%s'\n" % o for o, _ in parts))
    name = "final.mp4" if final else "preview.mp4"
    out = os.path.join(d, name)
    core.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst, "-i", os.path.join(d, "audio.m4a"), "-map", "0:v", "-map", "1:a",
              "-c", "copy", "-shortest", "-movflags", "+faststart", out])
    shutil.rmtree(parts_dir, ignore_errors=True)
    p.setdefault("outputs", {})["video" if final else "preview"] = out
    p["outputs"]["rev" if final else "prev_rev"] = int(time.time())
    return out


# ------------------------------------------------------------------ the job
def generate(p):
    st = p["settings"]

    def prog(stage, lo, hi):
        return lambda f, m: set_progress(p, stage, lo + (hi - lo) * core.clamp(f), m)
    p["status"] = "processing"
    save(p)
    if p.get("voice_upload"):
        set_progress(p, "voice", 0.02, "Listening to your voiceover")
        words = voice.transcribe(p["voice_upload"], st["language"])
        beats = voice.beats_from_words(words)
        o = {"title": p["title"], "chapters": [{"title": "Part %d" % (k + 1)} for k in range(max(1, len(beats) // 10))]}
        theme = catalog.THEMES[st["theme"]]["name"]
        for k in range(0, len(beats), 10):
            grp = beats[k:k + 10]
            plans = writer.plan_visuals(o, k // 10, "", st["format"], st.get("motion_graphics") or [], theme, p["seed"], [g["text"] for g in grp])
            for g, pl in zip(grp, plans):
                pl.update(g, chapter=min(k // 10, len(o["chapters"]) - 1))
                g.clear()
                g.update(pl)
            set_progress(p, "script", 0.05 + 0.2 * k / len(beats), "Storyboarding your voiceover")
        p["beats"], p["outline"] = beats, o
    else:
        writer.write_script(p, prog("script", 0.0, 0.25))
        save(p)
        voice.synth_beats(p["beats"], st["voice"], st["language"], os.path.join(p["dir"], "voice"), prog("voice", 0.25, 0.4), st.get("humanize", True))
    save(p)
    ensure_avatar(p, prog("avatar", 0.4, 0.43))
    set_progress(p, "timeline", 0.43, "Cutting the timeline")
    build_timeline(p)
    save(p)
    fetch_visuals(p, prog("visuals", 0.44, 0.7))
    save(p)
    build_audio(p, prog("audio", 0.7, 0.78))
    write_srt(p)
    save(p)
    render(p, prog("render", 0.78, 0.97), final=False)
    set_progress(p, "pack", 0.97, "Writing titles, description and thumbnail")
    try:
        p["pack"] = writer.gen_pack(p)
    except Exception:
        p["pack"] = {}
    try:
        thumb.for_project(p)
    except Exception:
        traceback.print_exc()
    p["status"] = "editing"
    p["dirty"] = False
    save(p)
    set_progress(p, "done", 1.0, "Ready to edit")


def rerender(p, final):
    def prog(stage, lo, hi):
        return lambda f, m: set_progress(p, stage, lo + (hi - lo) * core.clamp(f), m)
    p["status"] = "rendering"
    save(p)
    apply_times(p)
    fetch_visuals(p, prog("visuals", 0.0, 0.1))
    if p.get("audio_dirty", True):
        build_audio(p, prog("audio", 0.1, 0.25))
        p["audio_dirty"] = False
    write_srt(p)
    render(p, prog("render", 0.25, 0.99), final=final)
    p["status"] = "done" if final else "editing"
    p["dirty"] = False
    save(p)
    set_progress(p, "done", 1.0, "Render complete" if final else "Preview updated")


def _worker():
    while True:
        pid, kind = _jobs.get()
        _state["current"] = pid
        if pid in _state["queue"]:
            _state["queue"].remove(pid)
        p = load(pid)
        if not p:
            continue
        try:
            if kind == "generate":
                generate(p)
            else:
                rerender(p, final=(kind == "final"))
        except Exception as e:
            traceback.print_exc()
            p["status"] = "error" if kind == "generate" else "editing"
            save(p)
            set_progress(p, "error", 0, "Stopped", error=str(e)[:500])
        finally:
            _cancel.discard(pid)
            _state["current"] = None


_started = [False]


def enqueue(pid, kind="generate"):
    if not _started[0]:
        _started[0] = True
        threading.Thread(target=_worker, daemon=True).start()
    p = load(pid)
    p["status"] = "queued" if kind == "generate" else "rendering"
    save(p)
    set_progress(p, "queued", 0, "In queue")
    _state["queue"].append(pid)
    _jobs.put((pid, kind))


def cancel(pid):
    _cancel.add(pid)


def recover():
    """After a restart, mark interrupted jobs so the UI can offer a retry."""
    for it in list_projects():
        if it["status"] in ("queued", "processing", "rendering"):
            p = load(it["id"])
            p["status"] = "editing" if p.get("outputs", {}).get("preview") else "error"
            save(p)
            set_progress(p, "error", 0, "Interrupted", error="The server restarted during this job. Press retry.")


# ------------------------------------------------------------------ editor operations
def find_shot(p, sid):
    for i, s in enumerate(p["shots"]):
        if s["id"] == sid:
            return i, s
    raise KeyError("shot not found")


def edit_shot(p, sid, patch):
    i, s = find_shot(p, sid)
    for k in ("motion", "transition", "tdur", "filter", "speed", "focus", "offset", "bubble", "cast", "key"):
        if k in patch:
            s[k] = patch[k]
    if "mg" in patch:
        if patch["mg"]:
            s["mg"], s["kind"] = patch["mg"], "mg"
        else:
            s.pop("mg", None)
            s["kind"] = "visual"
    if patch.get("kind") in ("visual", "avatar", "anim2d", "mg"):
        s["kind"] = patch["kind"]
    p["dirty"] = True
    p["audio_dirty"] = True
    return s


def split_shot(p, sid, t):
    i, s = find_shot(p, sid)
    b = p["beats"][s["b"]]
    f = (t - b["start"]) / b["span"]
    if not (s["f0"] + 0.02 < f < s["f1"] - 0.02) or (t - s["start"]) < 0.6 or (s["start"] + s["dur"] - t) < 0.6:
        raise ValueError("Move the playhead inside the clip (at least 0.6 s from each edge).")
    n = dict(s, id="s" + core.uid(6), f0=round(f, 4), transition="cut", v=s["v"] + 7, variant=s.get("variant", 0) + 1)
    if s["kind"] == "visual":
        n.pop("asset", None)
    s["f1"] = round(f, 4)
    p["shots"].insert(i + 1, n)
    apply_times(p)
    p["dirty"] = True
    return n


def delete_shot(p, sid):
    i, s = find_shot(p, sid)
    same = [x for x in p["shots"] if x["b"] == s["b"]]
    if len(same) <= 1:
        raise ValueError("This is the only clip under this line of narration. Replace its visual instead.")
    k = same.index(s)
    if k > 0:
        same[k - 1]["f1"] = s["f1"]
    else:
        same[1]["f0"] = s["f0"]
    p["shots"].pop(i)
    apply_times(p)
    p["dirty"] = True


def replace_asset(p, sid, mode, data):
    """mode: candidate | ai | upload | search"""
    i, s = find_shot(p, sid)
    folder = os.path.join(p["dir"], "media")
    if mode == "candidate":
        a = media.obtain(data, folder)
    elif mode == "ai":
        dest = os.path.join(folder, "ai" + core.uid(10) + ".jpg")
        portrait = p["settings"].get("aspect") == "9:16"
        media.ai_image(data["prompt"], dest, 720 if portrait else 1280, 1280 if portrait else 720, random.randint(1, 99999),
                       data.get("style") or p["settings"].get("ai_style") or media.FORMAT_AI.get(p["settings"]["format"], "photo"))
        media.normalise_image(dest, dest)
        a = {"kind": "image", "path": dest, "src": "ai", "credit": "", "id": os.path.basename(dest)[:-4], "prompt": data["prompt"], "title": "AI image"}
    elif mode == "upload":
        path = data["path"]
        if path.lower().endswith((".mp4", ".mov", ".webm", ".mkv")):
            a = {"kind": "video", "path": path, "src": "upload", "credit": "", "id": core.h(path), "dur": core.media_duration(path), "title": "Upload"}
        else:
            dest = os.path.join(folder, "up" + core.uid(8) + ".jpg")
            media.normalise_image(path, dest)
            a = {"kind": "image", "path": dest, "src": "upload", "credit": "", "id": os.path.basename(dest)[:-4], "title": "Upload"}
    else:
        raise ValueError("unknown mode")
    s["asset"] = a
    if s["kind"] in ("avatar",):
        s["kind"] = "visual"
    s["offset"] = 0.0
    p["dirty"] = True
    return s


def revoice(p, bi, text):
    b = p["beats"][bi]
    if "abs_start" in b:
        raise ValueError("This project uses your uploaded voiceover, so the narration cannot be re-recorded here.")
    st = p["settings"]
    path = os.path.join(p["dir"], "voice", "b%04d_%s.mp3" % (bi, core.uid(6)))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    d, words = voice.synth(text, st["voice"], path, b.get("emotion", "calm"), st["language"], st.get("humanize", True))
    b.update(text=text, audio=path, vdur=d, words=words)
    apply_times(p)
    p["dirty"] = True
    p["audio_dirty"] = True
    return b


def add_overlay(p, ov):
    ov = dict(ov)
    ov["id"] = core.uid(6)
    ov["start"] = float(ov.get("start", 0))
    ov["dur"] = max(0.5, float(ov.get("dur", 3)))
    ov["b"] = None
    p["overlays"].append(ov)
    p["dirty"] = True
    p["audio_dirty"] = True
    return ov


def edit_overlay(p, oid, patch):
    for o in p["overlays"]:
        if o["id"] == oid:
            if patch.get("_delete"):
                p["overlays"].remove(o)
            else:
                if "start" in patch and o.get("b") is not None:
                    o["off"] = float(patch["start"]) - p["beats"][o["b"]]["start"]
                o.update({k: v for k, v in patch.items() if k not in ("id", "b")})
            p["dirty"] = True
            return o
    raise KeyError("overlay not found")


def preview_frame(p, t, w=640):
    r = compose.Renderer(p, w if p["settings"].get("aspect") != "9:16" else w * 9 // 16 // 2 * 2, (w * 9 // 16) // 2 * 2 if p["settings"].get("aspect") != "9:16" else w, FPS)
    try:
        path = os.path.join(p["dir"], "frame_%s.jpg" % core.uid(5))
        r.still(t, path)
    finally:
        r.close()
    return path
