"""Render the whole video: avatar lip-sync + code B-roll + layouts + transitions.

    python3 render.py frames START END OUT.mp4   # render a frame range (worker)
    python3 render.py still SECONDS OUT.png      # one preview frame
    python3 render.py events                     # dry-run to collect SFX cue times -> build/events.json
    python3 render.py all [WORKERS]              # everything -> build/video_noaudio.mp4
"""
import json, math, os, subprocess, sys
import numpy as np, cv2, skia

import kit
from kit import W, H, GOLD, RED, xf, rrect, text, brush_bar, kicker, clamp, ease_out, at, window, glow, fill_shader, linear, rect, P, C
import scenes2 as scenes
import avatar as av

FPS = av.FPS
HERE = os.path.dirname(os.path.abspath(__file__))
TL = json.load(open(os.path.join(HERE, "timeline.json")))
VOICE = os.path.join(HERE, "build", "voice.wav")
import soundfile as sf
DUR = sf.info(VOICE).duration
NF = int(DUR * FPS)

# ---- shot timing: each shot starts slightly before its first sentence
SH = []
for k, (si, lay, fn, kw) in enumerate(scenes.SHOTS):
    t0 = 0.0 if k == 0 else max(0.0, TL[si]["start"] - 0.12)
    SH.append([t0, None, si, lay, fn, kw])
for k in range(len(SH)):
    SH[k][1] = SH[k + 1][0] if k + 1 < len(SH) else DUR


def shot_at(t):
    for s in SH:
        if s[0] <= t < s[1]:
            return s
    return SH[-1]


_tracks = None


def tracks():
    global _tracks
    if _tracks is None:
        o, w = av.mouth_track(VOICE, NF + 2)
        b = av.blink_track(NF + 2)
        hd = av.head_track(NF + 2, o)
        _tracks = (o, w, b, hd)
    return _tracks


_AV = None


def avatar_img(fi):
    global _AV
    if _AV is None: _AV = av.Avatar()
    o, w, b, hd = tracks()
    return _AV.face(float(o[fi]), float(w[fi]), float(b[fi]))


FACE = (760.0, 390.0)  # look-at point in the photo


def place(img, fi, out_w, out_h, zoom, fx, fy, t_local=0.0):
    """Warp the avatar photo into an out_w x out_h box: `zoom` relative to
    cover-fit, photo point FACE lands at (fx, fy) of the box, + head motion."""
    o, w, b, (dx, dy, rot, sc) = tracks()
    base = max(out_w / img.shape[1], out_h / img.shape[0])
    s = base * zoom * sc[fi]
    M = cv2.getRotationMatrix2D(FACE, float(rot[fi]), s)
    M[0, 2] += fx - FACE[0] + dx[fi] * s
    M[1, 2] += fy - FACE[1] + dy[fi] * s
    # keep the box covered (clamp translation)
    return cv2.warpAffine(img, M, (out_w, out_h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def lower_third(c, t, name, role):
    k = ease_out(at(t, 0.5, 0.5)) * clamp((7.5 - t) / 0.4)
    if k <= 0: return
    with xf(c, 90 - (1 - k) * 60, 860, alpha=k):
        nw = kit.tw(name, 64) + 70
        brush_bar(c, 0, -70, nw, 96, RED, k, seed=9)
        text(c, name, 30, 0, 64, "#ffffff", "black", align="left")
        rect(c, 0, 40, (kit.tw(role, 36) + 4 * len(role) + 50) * k, 54, "#0b0a09", 0.85)
        text(c, role, 24, 80, 36, GOLD, "black", align="left", spacing=4)


NOISE = None


def grain(arr, fi):
    global NOISE
    if NOISE is None:
        r = np.random.default_rng(1)
        NOISE = [r.normal(0, 5, (H // 2, W // 2, 1)).astype(np.int16) for _ in range(6)]
    n = NOISE[fi % 6]
    n = np.repeat(np.repeat(n, 2, 0), 2, 1)
    rgb = arr[..., :3].astype(np.int16) + n
    arr[..., :3] = np.clip(rgb, 0, 255).astype(np.uint8)


def frame(fi):
    t = fi / FPS
    t0, t1, si, lay, fn, kw = shot_at(t)
    lt, d = t - t0, t1 - t0
    S = lambda i: TL[i]["start"] - t0 if 0 <= i < len(TL) else -99
    arr = np.zeros((H, W, 4), np.uint8); arr[..., 3] = 255
    if lay in ("A", "S", "P"):
        img = avatar_img(fi)
    if lay == "A":
        zoom = 1.04 + 0.07 * clamp(lt / max(d, 1)) + 0.12 * (1 if (hash(si) % 2) else 0)
        fx = W * (0.5 if zoom > 1.1 else 0.42)
        a = place(img, fi, W, H, zoom, fx, H * 0.40)
        arr[..., :3] = cv2.cvtColor(a, cv2.COLOR_BGR2RGB)
    elif lay == "S":
        a = place(img, fi, W // 2, H, 1.42 + 0.04 * clamp(lt / max(d, 1)), W * 0.25, H * 0.42)
        arr[:, :W // 2, :3] = cv2.cvtColor(a, cv2.COLOR_BGR2RGB)
    surf = skia.Surface(arr)
    c = surf.getCanvas()
    settle = 1.0 + 0.05 * (1 - ease_out(clamp(lt / 0.45)))
    if lay == "S":
        c.save(); c.clipRect(skia.Rect(W / 2, 0, W, H)); c.translate(W / 2, 0)
        c.translate(W / 4, H / 2); c.scale(settle, settle); c.translate(-W / 4, -H / 2)
        fn(c, lt, d, W // 2, H, S, **kw)
        kit.vignette(c, W / 2, H, 0.45)
        c.restore()
        fill_shader(c, skia.Rect(W / 2 - 40, 0, W / 2, H), linear(W / 2 - 40, 0, W / 2, 0, [("#000000", 0), ("#000000", 0.55)]))
        rect(c, W / 2 - 3, 0, 6, H, GOLD, 0.9)
    elif lay in ("P", "B"):
        c.save(); c.translate(W / 2, H / 2); c.scale(settle, settle); c.translate(-W / 2, -H / 2)
        fn(c, lt, d, W, H, S, **kw)
        c.restore()
        kit.vignette(c, W, H, 0.5)
    if lay == "P":
        pw, ph = 380, 240
        px, py = 30, H - ph - 30
        k = ease_out(clamp((lt - 0.15) / 0.4))
        a = place(img, fi, pw, ph, 1.6, pw * 0.5, ph * 0.45)
        pip = np.zeros((ph, pw, 4), np.uint8); pip[..., :3] = cv2.cvtColor(a, cv2.COLOR_BGR2RGB); pip[..., 3] = 255
        pimg = skia.Image.fromarray(pip)
        with xf(c, px + pw / 2, py + ph / 2, s=0.6 + 0.4 * k, alpha=k):
            rrect(c, -pw / 2 + 8, -ph / 2 + 12, pw, ph, 18, "#000000", 0.5)
            c.save(); c.clipRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-pw / 2, -ph / 2, pw, ph), 18, 18), True)
            c.drawImage(pimg, -pw / 2, -ph / 2); c.restore()
            rrect(c, -pw / 2, -ph / 2, pw, ph, 18, GOLD, stroke=5)
    if lay == "A":
        fill_shader(c, skia.Rect(0, 0, W, H), linear(0, 0, W, 0, [("#ff9a3c", 0.05 + 0.04 * math.sin(t * 0.7)), ("#ff9a3c", 0), ("#000000", 0.0)]))
        kit.vignette(c, W, H, 0.42)
        if kw.get("lower"):
            lower_third(c, lt, *kw["lower"])
        ks = kw.get("kick", [])
        for j, (ki, s) in enumerate(ks):
            st = S(ki); en = S(ks[j + 1][0]) - 0.1 if j + 1 < len(ks) else d + 1
            kicker(c, lt, st, min(en, st + 4.5), s, W * 0.5, 190, 86)
    # cut flash
    fl = 1 - clamp(lt / 0.16)
    if fl > 0 and t > 0.2:
        rect(c, 0, 0, W, H, "#ffffff", 0.22 * fl)
    # letterbox fade at the very start / end
    fade = min(clamp(t / 0.6), clamp((DUR - t) / 1.0))
    if fade < 1:
        rect(c, 0, 0, W, H, "#000000", 1 - fade)
    del c, surf
    grain(arr, fi)
    return arr


def render_range(f0, f1, out):
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for fi in range(f0, f1):
        p.stdin.write(frame(fi).tobytes())
        if fi % 300 == 0:
            print(f"[{out}] {fi}/{f1}", flush=True)
    p.stdin.close(); p.wait()


def collect_events():
    kit.REC["on"] = True
    out = []
    surf = skia.Surface(64, 36); c = surf.getCanvas()
    for t0, t1, si, lay, fn, kw in SH:
        if fn is None:
            ks = kw.get("kick", [])
            out += [("kick", TL[k]["start"]) for k, _ in ks]
            out.append(("cut", t0))
            continue
        S = lambda i, t0=t0: TL[i]["start"] - t0 if 0 <= i < len(TL) else -99
        kit.EVENTS.clear()
        t = 0.0
        while t < t1 - t0:
            c.save(); c.scale(64 / W, 36 / H); fn(c, t, t1 - t0, W, H, S, **kw); c.restore()
            t += 0.1
        seen = set()
        for kind, lt in kit.EVENTS:
            key = (kind, round(lt * 3))
            if key in seen or lt < 0 or lt > t1 - t0: continue
            seen.add(key); out.append((kind, t0 + lt))
        out.append(("title" if fn is scenes.title_card else "cut", t0))
    out.sort(key=lambda e: e[1])
    json.dump(out, open(os.path.join(HERE, "build", "events.json"), "w"))
    print(len(out), "events")


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "frames":
        render_range(int(sys.argv[2]), int(sys.argv[3]), sys.argv[4])
    elif mode == "still":
        fi = int(float(sys.argv[2]) * FPS)
        a = frame(fi); cv2.imwrite(sys.argv[3], cv2.cvtColor(a, cv2.COLOR_RGBA2BGR))
    elif mode == "events":
        collect_events()
    elif mode == "all":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 4
        parts = os.path.join(HERE, "build", "parts"); os.makedirs(parts, exist_ok=True)
        step = math.ceil(NF / n); procs = []; files = []
        for k in range(n):
            f = os.path.join(parts, f"p{k:02d}.mp4"); files.append(f)
            procs.append(subprocess.Popen([sys.executable, __file__, "frames", str(k * step), str(min(NF, (k + 1) * step)), f]))
        for p in procs: p.wait()
        lst = os.path.join(parts, "list.txt")
        open(lst, "w").write("".join(f"file '{f}'\n" for f in files))
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy",
                        os.path.join(HERE, "build", "video_noaudio.mp4")], check=True)
        print("done")
