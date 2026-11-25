"""Render the Sheikh voiceover video.

python render.py --jobs 4 --out out.mp4 [--start 0 --end 30]
"""
import os, sys, json, argparse, subprocess, functools, math
import numpy as np
from PIL import Image, ImageDraw
from multiprocessing import Process

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine import *  # noqa
import timeline as TL

HERE = os.path.dirname(os.path.abspath(__file__))


# ---------------------------------------------------------------- overlays
@functools.lru_cache(maxsize=512)
def cap_layer(words, hi):
    """Caption chunk; word index `hi` highlighted in gold."""
    fnt = font("Montserrat-SemiBold.ttf", 50)
    words = list(words)
    text = " ".join(words)
    lines = wrap(fnt, text, 1500)
    lh = 66
    w = int(max(fnt.getlength(l) for l in lines)) + 60
    h = lh * len(lines) + 30
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    idx = 0
    for li, line in enumerate(lines):
        lw = fnt.getlength(line)
        x = (w - lw) / 2
        y = 12 + li * lh
        for wd in line.split():
            col = GOLD + (255,) if idx == hi else (255, 255, 255, 255)
            d.text((x, y), wd, font=fnt, fill=col, stroke_width=3, stroke_fill=(0, 0, 0, 200))
            x += fnt.getlength(wd + " ")
            idx += 1
    return shadowed(im, 8, 160, (0, 3))


def draw_caption(base, t):
    c = TL.caption_at(t)
    if c is None:
        return
    words, times, cs, ce = c
    hi = -1
    for i, (s, e) in enumerate(times):
        if s <= t:
            hi = i
    lay = cap_layer(tuple(words), hi)
    a = min(1.0, (t - cs) / 0.12, (ce + 0.15 - t) / 0.15)
    rise = (1 - ease_out((t - cs) / 0.25)) * 14
    paste(base, lay, (W - lay.width) / 2, H - 70 - lay.height + rise, max(0, a))


@functools.lru_cache(maxsize=128)
def title_layer(top, text, sub):
    f_top = font("Cinzel-Bold.ttf", 40)
    f_main = font("Playfair-Bold.ttf", 92 if len(text) < 28 else 76)
    f_sub = font("Montserrat-SemiBold.ttf", 38)
    lines = wrap(f_main, text, 1500)
    lh = int(f_main.size * 1.18)
    h = 70 + 40 + lh * len(lines) + (70 if sub else 0) + 30
    im = Image.new("RGBA", (W, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    y = 0
    if top:
        tw, _, _ = text_size(f_top, top, 8)
        draw_spaced(d, ((W - tw) / 2, y), top, f_top, GOLD + (255,), 8)
    y += 70 + 30
    for l in lines:
        lw = f_main.getlength(l)
        d.text(((W - lw) / 2, y), l, font=f_main, fill=CREAM + (255,))
        y += lh
    if sub:
        y += 18
        sw = f_sub.getlength(sub)
        d.text(((W - sw) / 2, y), sub, font=f_sub, fill=(230, 220, 200, 235))
    return shadowed(im, 14, 200, (0, 5))


def draw_title(base, o, t):
    u = (t - o["s"]) / 0.7
    out = (o["e"] - t) / 0.45
    a = min(ease_out(u), ease(out), 1.0)
    if a <= 0:
        return
    dim(base, 0.55 * a)
    lay = title_layer(o.get("top", ""), o["text"], o.get("sub", ""))
    y = (H - lay.height) / 2 + (1 - ease_out(u)) * 40
    paste(base, lay, 0, y, a)
    # gold rule that draws itself out from the centre
    rw = int(520 * ease_out((t - o["s"] - 0.2) / 0.8))
    if rw > 2:
        ry = int(y + 70)
        base[ry:ry + 3, W // 2 - rw // 2:W // 2 + rw // 2] = (base[ry:ry + 3, W // 2 - rw // 2:W // 2 + rw // 2] * (1 - a)
                                                            + np.array(GOLD, np.float32) * a)


@functools.lru_cache(maxsize=128)
def quote_layer(text, nwords):
    fnt = font("Playfair-Bold.ttf", 70)
    words = text.split()
    lines = wrap(fnt, text, 980)
    lh = 92
    im = Image.new("RGBA", (1100, lh * len(lines) + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    idx = 0
    for li, l in enumerate(lines):
        x = 0
        for wd in l.split():
            if idx < nwords:
                d.text((x, 10 + li * lh), wd, font=fnt, fill=CREAM + (255,))
            x += fnt.getlength(wd + " ")
            idx += 1
    return shadowed(im, 12, 190, (0, 4))


def draw_quote(base, o, t):
    u = (t - o["s"])
    a = min(ease_out(u / 0.5), ease((o["e"] - t) / 0.4), 1.0)
    if a <= 0:
        return
    base *= (1 - (1 - left_grad()) * a)
    words = o["text"].split()
    span = max(0.6, min(len(words) * 0.28, (o["e"] - o["s"]) * 0.55))
    n = len(words) if u >= span else int(len(words) * u / span) + 1
    lay = quote_layer(o["text"], n)
    y = (H - lay.height) / 2 - 30
    # gold quote mark + bar
    bar_h = int(lay.height * ease_out(u / 0.6))
    if bar_h > 0:
        base[int(y):int(y) + bar_h, 110:116] = base[int(y):int(y) + bar_h, 110:116] * (1 - a) + np.array(GOLD, np.float32) * a
    paste(base, lay, 150, y, a)


@functools.lru_cache(maxsize=1)
def lower_mask():
    x = 1 - np.linspace(0, 1, 1300, dtype=np.float32) ** 1.6
    y = np.sin(np.linspace(0, np.pi, 420, dtype=np.float32)) ** 1.2
    return (y[:, None] * x[None, :])[..., None]


@functools.lru_cache(maxsize=64)
def lower_layer(name, role):
    f1 = font("Cinzel-Bold.ttf", 54)
    f2 = font("Montserrat-SemiBold.ttf", 32)
    w = int(max(f1.getlength(name) + 8 * len(name), f2.getlength(role)) + 80)
    im = Image.new("RGBA", (w, 170), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 8, 150), fill=GOLD + (255,))
    draw_spaced(d, (36, 10), name, f1, CREAM + (255,), 8)
    d.text((38, 92), role, font=f2, fill=GOLD + (255,))
    return shadowed(im, 10, 190, (0, 4))


def draw_lower(base, o, t):
    u = t - o["s"]
    a = min(ease_out(u / 0.5), ease((o["e"] - t) / 0.4), 1.0)
    if a <= 0:
        return
    base[H - 520:H - 100, :1300] *= (1 - 0.6 * a * lower_mask())
    lay = lower_layer(o["name"], o["role"])
    x = 110 - (1 - ease_out(u / 0.6)) * 80
    paste(base, lay, x, H - 380, a)


@functools.lru_cache(maxsize=128)
def kw_layer(text, size, color):
    fnt = font("Montserrat-ExtraBold.ttf", size)
    tw = fnt.getlength(text) + 6 * len(text)
    pad = 34
    im = Image.new("RGBA", (int(tw + pad * 2), int(size * 1.6)), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, im.width - 1, im.height - 1), radius=14, fill=(18, 14, 10, 205), outline=GOLD + (255,), width=3)
    draw_spaced(d, (pad, size * 0.22), text, fnt, color + (255,), 6)
    return shadowed(im, 12, 170, (0, 5))


def draw_kw(base, o, t):
    u = t - o["s"]
    a = min(ease_out(u / 0.25), ease((o["e"] - t) / 0.3), 1.0)
    if a <= 0:
        return
    col = tuple(o.get("col", GOLD))
    lay = kw_layer(o["text"], o.get("size", 64), col)
    sc = 0.6 + 0.4 * back_out(u / 0.45)
    if abs(sc - 1) > 0.01:
        lay = lay.resize((max(1, int(lay.width * sc)), max(1, int(lay.height * sc))), Image.BILINEAR)
    pos = o.get("pos", "top")
    cy = {"top": 190, "mid": H / 2 - 60, "upper": 300}.get(pos, 190)
    paste(base, lay, (W - lay.width) / 2, cy - lay.height / 2, a)


@functools.lru_cache(maxsize=64)
def list_layer(items, n, off=0):
    fnt = font("Montserrat-SemiBold.ttf", 60)
    lh = 104
    im = Image.new("RGBA", (1300, lh * len(items) + 20), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for i, it in enumerate(items[:n]):
        y = 10 + i * lh
        d.ellipse((0, y + 14, 46, y + 60), fill=GOLD + (255,))
        d.text((12 if i + 1 + off < 10 else 3, y + 10), str(i + 1 + off), font=font("Montserrat-ExtraBold.ttf", 32), fill=(20, 16, 10, 255))
        d.text((78, y), it, font=fnt, fill=CREAM + (255,))
    return shadowed(im, 10, 200, (0, 4))


def draw_list(base, o, t):
    u = t - o["s"]
    a = min(ease_out(u / 0.4), ease((o["e"] - t) / 0.4), 1.0)
    if a <= 0:
        return
    base *= (1 - (1 - left_grad()) * a)
    items = tuple(o["items"])
    times = o.get("at", [o["s"] + i * 0.8 for i in range(len(items))])
    n = sum(1 for x in times if t >= x)
    lay = list_layer(items, n, o.get("offset", 0))
    paste(base, lay, 130, (H - lay.height) / 2 - 40, a)


DRAW = {"title": draw_title, "quote": draw_quote, "lower": draw_lower, "kw": draw_kw, "list": draw_list}


# ---------------------------------------------------------------- frames
class Renderer:
    def __init__(self):
        self.shots = TL.SHOTS
        self.readers = {}

    def src_frame(self, i, t):
        sh = self.shots[i]
        dur = sh["e"] - sh["s"] + XFADE
        lt = max(0.0, t - sh["s"] + (XFADE if i > 0 else 0.0))
        u = min(lt / dur, 1.0)
        kind, ref = sh["src"].split(":", 1)
        if kind == "img":
            return render_img(ref, sh.get("mv", "in"), u, dur)
        rd = self.readers.get(i)
        if rd is None:
            rd = VidReader(ref, dur, lt, sh.get("mv", "in"))
            rd.base = int(round(lt * FPS))
            self.readers[i] = rd
        fr = rd.frame(int(round(lt * FPS)) - rd.base)
        return vid_zoom(fr, sh.get("mv", "in"), u)

    def shot_index(self, t):
        for i, sh in enumerate(self.shots):
            if sh["s"] <= t < sh["e"]:
                return i
        return len(self.shots) - 1

    def frame(self, fi):
        t = fi / FPS
        i = self.shot_index(t)
        sh = self.shots[i]
        base = self.src_frame(i, t).astype(np.float32)
        nxt = i + 1 if i + 1 < len(self.shots) else None
        # cross-dissolve into the next shot over the last XFADE seconds of this one
        if nxt is not None and t >= sh["e"] - XFADE:
            k = ease((t - (sh["e"] - XFADE)) / XFADE)
            nb = self.src_frame(nxt, t).astype(np.float32)
            base = base * (1 - k) + nb * k
        # close readers we no longer need
        for j in list(self.readers):
            if j < i:
                self.readers.pop(j).close()
        # fade in / out of the whole video
        if t < 0.8:
            base *= ease(t / 0.8)
        if t > TL.END - 1.5:
            base *= ease((TL.END - t) / 1.5)
        title_on = False
        for o in TL.OVERLAYS:
            if o["s"] - 0.05 <= t <= o["e"] + 0.05:
                DRAW[o["k"]](base, o, t)
                if o["k"] in ("title", "quote", "list"):
                    title_on = True
        if not title_on:
            base *= bottom_grad() if TL.caption_at(t) else 1
            draw_caption(base, t)
        return finish(base, fi)


def work(a, b, path):
    r = Renderer()
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-c:v", "libx264", "-preset", "fast", "-crf", "19", "-pix_fmt", "yuv420p", path]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for fi in range(a, b):
        p.stdin.write(r.frame(fi).tobytes())
        if (fi - a) % 300 == 0:
            print(f"[{os.path.basename(path)}] {fi - a}/{b - a}", flush=True)
    p.stdin.close()
    p.wait()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="out.mp4")
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--start", type=float, default=0)
    ap.add_argument("--end", type=float, default=None)
    ap.add_argument("--still", type=float, nargs="*")
    a = ap.parse_args()
    if a.still:
        r = Renderer()
        for s in a.still:
            Image.fromarray(r.frame(int(s * FPS))).save(f"still_{s:07.2f}.jpg", quality=88)
        return
    end = a.end if a.end is not None else TL.END
    f0, f1 = int(a.start * FPS), int(end * FPS)
    parts_dir = a.out + "_parts"
    os.makedirs(parts_dir, exist_ok=True)
    # break shot boundaries into chunks so each worker gets an even load
    n = a.jobs * 3
    edges = [f0 + (f1 - f0) * k // n for k in range(n + 1)]
    chunks = [(edges[k], edges[k + 1], os.path.join(parts_dir, f"p{k:03d}.mp4")) for k in range(n)]
    todo = [c for c in chunks if not os.path.exists(c[2] + ".done")]
    running = []
    while todo or running:
        while todo and len(running) < a.jobs:
            c = todo.pop(0)
            pr = Process(target=lambda c=c: (work(*c), open(c[2] + ".done", "w").close()))
            pr.start()
            running.append(pr)
        running[0].join()
        running = [p for p in running if p.is_alive()]
    with open(os.path.join(parts_dir, "list.txt"), "w") as f:
        for c in chunks:
            f.write(f"file '{os.path.abspath(c[2])}'\n")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i",
                    os.path.join(parts_dir, "list.txt"), "-c", "copy", a.out], check=True)
    print("done", a.out)


if __name__ == "__main__":
    main()
