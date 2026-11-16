"""Composite the final video: stock background track + pasted avatar + voice waveform
+ word-highlighted captions + simple title text animations.

python render.py --bg bg.mp4 --voice voice.wav --out final.mp4 --jobs 3
python render.py --still 123.4 frame.png
"""
import argparse, json, math, os, subprocess, sys
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1920, 1080, 30
FB = "/usr/share/fonts/opentype/inter/Inter-Black.otf"
FXB = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
FSB = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
YELLOW = (255, 214, 10)
ACCENT = (255, 196, 0)

PLAN = json.load(open("plan.json"))
CAP = json.load(open("captions.json"))       # [{s,e,words:[{w,s,e}]}]
LV = np.load("levels.npz"); SPEC, RMS = LV["spec"], LV["rms"]
STICK = {k: np.asarray(Image.open(f"avatar/sticker{k}.png"), dtype=np.float32) for k in (1, 2, 3)}

AV_X = 34  # avatar left


def blend(frame, rgba, x, y, alpha=1.0):
    """Alpha-blend float32 RGBA patch onto uint8 frame at (x,y) with clipping."""
    h, w = rgba.shape[:2]
    x0, y0 = max(x, 0), max(y, 0); x1, y1 = min(x + w, W), min(y + h, H)
    if x0 >= x1 or y0 >= y1: return
    p = rgba[y0 - y:y1 - y, x0 - x:x1 - x]
    a = p[..., 3:4] * (alpha / 255.0)
    dst = frame[y0:y1, x0:x1].astype(np.float32)
    frame[y0:y1, x0:x1] = (dst + (p[..., :3] - dst) * a).astype(np.uint8)


def ease_out(t): return 1 - (1 - min(max(t, 0), 1)) ** 3


# ---------------- bottom gradient for legibility ----------------
GRAD_H = 420
_g = np.linspace(0, 1, GRAD_H) ** 1.6 * 0.72
GRAD = (1 - _g)[:, None, None].astype(np.float32)


# ---------------- captions ----------------
CAP_FONT = ImageFont.truetype(FB, 58)
CAP_CX = 1160   # caption centre x (right of the avatar)
CAP_Y = 955
CAP_MAXW = 1300


@lru_cache(maxsize=64)
def caption_img(key, hi):
    words = key.split("\x00")
    d = ImageDraw.Draw(Image.new("L", (1, 1)))
    sp = d.textlength(" ", font=CAP_FONT) + 16
    ws = [d.textlength(w, font=CAP_FONT) for w in words]
    # wrap into max 2 lines
    lines, cur, cw = [], [], 0
    for i, w in enumerate(ws):
        if cur and cw + sp + w > CAP_MAXW:
            lines.append(cur); cur, cw = [], 0
        cw += (sp if cur else 0) + w; cur.append(i)
    lines.append(cur)
    lh = 74
    img = Image.new("RGBA", (CAP_MAXW + 60, lh * len(lines) + 40), (0, 0, 0, 0))
    dr = ImageDraw.Draw(img)
    for li, line in enumerate(lines):
        tw = sum(ws[i] for i in line) + sp * (len(line) - 1)
        x = (img.width - tw) / 2; y = 16 + li * lh
        for i in line:
            if i == hi:
                pad = 10
                dr.rounded_rectangle((x - pad, y - 4, x + ws[i] + pad, y + 70), 14, fill=YELLOW + (255,))
                dr.text((x, y), words[i], font=CAP_FONT, fill=(15, 15, 15))
            else:
                dr.text((x, y), words[i], font=CAP_FONT, fill=(255, 255, 255), stroke_width=6, stroke_fill=(0, 0, 0))
            x += ws[i] + sp
    return np.asarray(img, dtype=np.float32)


def draw_caption(frame, t):
    for c in CAP:
        if c["s"] - 0.05 <= t < c["e"] + 0.15:
            break
    else:
        return
    hi = -1
    for i, w in enumerate(c["words"]):
        if t >= w["s"] - 0.02: hi = i
    key = "\x00".join(w["w"] for w in c["words"])
    img = caption_img(key, hi)
    k = ease_out((t - c["s"] + 0.05) / 0.18)
    y = CAP_Y + int((1 - k) * 25) - img.shape[0] // 2 + 37
    blend(frame, img, CAP_CX - img.shape[1] // 2, y, alpha=k)


# ---------------- waveform ----------------
WF_BARS, WF_W, WF_H = 28, 400, 92


@lru_cache(maxsize=1)
def wf_bg():
    im = Image.new("RGBA", (WF_W + 30, WF_H + 30), (0, 0, 0, 0))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((15, 19, WF_W + 15, WF_H + 19), WF_H // 2, fill=(0, 0, 0, 120))
    sh = sh.filter(ImageFilter.GaussianBlur(8))
    im.alpha_composite(sh)
    ImageDraw.Draw(im).rounded_rectangle((15, 15, WF_W + 15, WF_H + 15), WF_H // 2, fill=(14, 18, 28, 215),
                                         outline=(255, 255, 255, 60), width=2)
    return np.asarray(im, dtype=np.float32)


def draw_wave(frame, f, x, y):
    blend(frame, wf_bg(), x - 15, y - 15)
    f = min(f, len(SPEC) - 1)
    sp = SPEC[f]; r = RMS[f]
    # mirror spectrum so the centre bars are the strongest
    half = WF_BARS // 2
    vals = np.concatenate([sp[:half][::-1], sp[:half]])
    bw, gap = 7, (WF_W - 70 - WF_BARS * 7) / (WF_BARS - 1)
    cy = y + WF_H // 2
    # mic dot on the left
    dot = 1 if r > 0.12 else 0
    cx0 = x + 36
    yy, xx = np.ogrid[-16:17, -16:17]
    disk = (xx ** 2 + yy ** 2) <= (13 + 2 * dot) ** 2
    reg = frame[cy - 16:cy + 17, cx0 - 16:cx0 + 17]
    col = np.array([255, 70, 70] if dot else [150, 150, 150], np.uint8)
    reg[disk] = col
    for i in range(WF_BARS):
        v = 0.08 + 0.92 * float(vals[i]) * (0.35 + 0.65 * r)
        bh = max(6, int(v * (WF_H - 22)))
        bx = int(x + 62 + i * (bw + gap))
        c = np.array(YELLOW if v > 0.55 else (255, 255, 255), np.uint8)
        frame[cy - bh // 2:cy + bh // 2, bx:bx + bw] = c


# ---------------- titles (text animation) ----------------
TITLE_FONT = ImageFont.truetype(FB, 64)
SUB_FONT = ImageFont.truetype(FSB, 34)


@lru_cache(maxsize=16)
def title_img(text, sub):
    d = ImageDraw.Draw(Image.new("L", (1, 1)))
    tw = d.textlength(text, font=TITLE_FONT)
    sw = d.textlength(sub, font=SUB_FONT) if sub else 0
    w = int(max(tw, sw) + 80); h = 110 + (52 if sub else 0)
    im = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((20, 26, w + 20, h + 26), 18, fill=(0, 0, 0, 140))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)))
    dr = ImageDraw.Draw(im)
    dr.rounded_rectangle((20, 20, w + 20, h + 20), 18, fill=(255, 255, 255, 245))
    dr.rounded_rectangle((20, 20, 34, h + 20), 6, fill=ACCENT + (255,))
    dr.text((58, 34), text, font=TITLE_FONT, fill=(16, 18, 28))
    if sub:
        dr.text((60, 112), sub, font=SUB_FONT, fill=(90, 96, 110))
    return np.asarray(im, dtype=np.float32)


def draw_title(frame, t):
    for ti in PLAN["titles"]:
        if ti["s"] <= t < ti["e"]:
            img = title_img(ti["text"], ti.get("sub", ""))
            k_in = ease_out((t - ti["s"]) / 0.35)
            k_out = ease_out((ti["e"] - t) / 0.3)
            k = min(k_in, k_out)
            x = 70 - int((1 - k) * 120)
            blend(frame, img, x, 60, alpha=k)
            return


# ---------------- avatar ----------------
def avatar_for(t):
    for sc in PLAN["avatar"]:
        if sc["s"] <= t < sc["e"]:
            return sc["id"]
    return 2


def draw_avatar(frame, t, f):
    k = avatar_for(t)
    img = STICK[k]
    r = float(RMS[min(f, len(RMS) - 1)])
    bob = int(round(3 * math.sin(t * 2.1))) - int(r * 4)
    y = H - img.shape[0] + 26 + bob
    blend(frame, img, AV_X, y)
    return AV_X + img.shape[1]


# ---------------- frame ----------------
def compose(frame, f):
    t = f / FPS
    frame[H - GRAD_H:] = (frame[H - GRAD_H:].astype(np.float32) * GRAD).astype(np.uint8)
    right = draw_avatar(frame, t, f)
    draw_wave(frame, f, right - 30, 720)
    draw_caption(frame, t)
    draw_title(frame, t)
    return frame


def render_part(bg, start, n, out):
    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{start / FPS:.4f}", "-i", bg, "-frames:v", str(n),
                            "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                            "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    sz = W * H * 3
    for i in range(n):
        buf = dec.stdout.read(sz)
        if len(buf) < sz:
            frame = last.copy() if i else np.zeros((H, W, 3), np.uint8)
        else:
            frame = np.frombuffer(buf, np.uint8).reshape(H, W, 3).copy()
            last = frame.copy()
        enc.stdin.write(compose(frame, start + i).tobytes())
        if i % 1500 == 0:
            print(f"{out}: {i}/{n}", flush=True)
    enc.stdin.close(); enc.wait(); dec.wait()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--bg", default="bg.mp4")
    ap.add_argument("--voice", default="voice.wav")
    ap.add_argument("--out", default="final.mp4")
    ap.add_argument("--jobs", type=int, default=3)
    ap.add_argument("--part", type=int, nargs=3)  # start n index (internal)
    ap.add_argument("--still", nargs=2)
    a = ap.parse_args()
    total = int(PLAN["duration"] * FPS)
    if a.still:
        f = int(float(a.still[0]) * FPS)
        fr = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{f / FPS:.3f}", "-i", a.bg, "-frames:v", "1",
                             "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
        frame = np.frombuffer(fr, np.uint8).reshape(H, W, 3).copy()
        Image.fromarray(compose(frame, f)).save(a.still[1]); sys.exit()
    if a.part:
        render_part(a.bg, a.part[0], a.part[1], f"parts/part{a.part[2]:02d}.mp4"); sys.exit()
    os.makedirs("parts", exist_ok=True)
    nparts = a.jobs * 4
    step = math.ceil(total / nparts)
    todo = [(i * step, min(step, total - i * step), i) for i in range(nparts) if i * step < total]
    running = []
    for s, n, i in todo:
        if os.path.exists(f"parts/part{i:02d}.done"): continue
        while len(running) >= a.jobs:
            for p in running:
                if p.poll() is not None: running.remove(p); break
            else:
                import time; time.sleep(2)
        running.append(subprocess.Popen(f"python3 render.py --bg {a.bg} --part {s} {n} {i} && touch parts/part{i:02d}.done", shell=True))
    for p in running: p.wait()
    with open("parts/list.txt", "w") as fl:
        for _, _, i in todo: fl.write(f"file 'part{i:02d}.mp4'\n")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", "parts/list.txt", "-i", a.voice,
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
                    "-movflags", "+faststart", a.out], check=True)
    print("done", a.out)
