"""Join rendered shots, upscale to 1080x1920, burn word-by-word captions, and mux the soundtrack.

Usage: python compose.py --audio audio/mix.wav --out phone_germs_3d.mp4 [--no-captions]
"""
import argparse
import glob
import json
import os
import subprocess

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 1080, 1920, 30
OFFSET = 0.25
FONT = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
SHOT_ORDER = ["s01", "s02", "s03", "s04", "s05", "s06", "s07", "s08", "s09", "s10"]


def chunks(words):
    out, cur = [], []
    for w in words:
        cur.append(w)
        if len(cur) == 3 or w["w"][-1] in ".,!?" or (len(cur) == 2 and len(w["w"]) > 7):
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    res = []
    for i, c in enumerate(out):
        s = c[0]["s"] + OFFSET
        e = (out[i + 1][0]["s"] + OFFSET) if i + 1 < len(out) else c[-1]["e"] + OFFSET + 0.6
        res.append((s, e, c))
    return res


def draw_caption(img, t, caps, font):
    for s, e, c in caps:
        if s <= t < e:
            break
    else:
        return img
    age = t - s
    scale = min(1.0, 0.82 + age / 0.12 * 0.18)
    words = [w["w"].strip(",.").upper() for w in c]
    cur = max([i for i, w in enumerate(c) if w["s"] + OFFSET <= t] or [0])
    size = int(96 * scale)
    f = font.font_variant(size=size)
    space = size * 0.28
    widths = [f.getlength(w) for w in words]
    total = sum(widths) + space * (len(words) - 1)
    lines = [list(range(len(words)))]
    if total > W * 0.86:
        lines = [list(range(len(words) - 1)), [len(words) - 1]]
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    y = 1330 - (len(lines) - 1) * size * 0.6
    for line in lines:
        lw = sum(widths[i] for i in line) + space * (len(line) - 1)
        x = (W - lw) / 2
        for i in line:
            col = (255, 222, 60) if i == cur else (255, 255, 255)
            d.text((x, y), words[i], font=f, fill=col, stroke_width=int(size * 0.11), stroke_fill=(0, 0, 0),
                   anchor="lm")
            x += widths[i] + space
        y += size * 1.15
    shadow = layer.split()[3].filter(ImageFilter.GaussianBlur(10))
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sh.putalpha(shadow.point(lambda a: int(a * 0.5)))
    img = Image.alpha_composite(img.convert("RGBA"), sh)
    return Image.alpha_composite(img, layer).convert("RGB")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--audio", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--frames", default=os.path.join(HERE, "frames"))
    ap.add_argument("--no-captions", action="store_true")
    a = ap.parse_args()
    files = []
    for sh in SHOT_ORDER:
        d = glob.glob(os.path.join(a.frames, sh + "_*"))[0]
        files += sorted(glob.glob(os.path.join(d, "f*.png")))
    caps = chunks(json.load(open(os.path.join(HERE, "audio", "words.json"))))
    font = ImageFont.truetype(FONT, 96)
    vf = ("eq=saturation=1.12:contrast=1.04,"
          "vignette=angle=PI/5:mode=forward,unsharp=5:5:0.6:5:5:0.0")
    cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-i", a.audio, "-map", "0:v", "-map", "1:a", "-vf", vf,
           "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
           "-af", "loudnorm=I=-14:TP=-1:LRA=11", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest", a.out]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i, p in enumerate(files):
        img = Image.open(p).convert("RGB").resize((W, H), Image.LANCZOS)
        if not a.no_captions:
            img = draw_caption(img, i / FPS, caps, font)
        ff.stdin.write(img.tobytes())
    ff.stdin.close()
    ff.wait()
    print("frames:", len(files), "->", a.out)


if __name__ == "__main__":
    main()
