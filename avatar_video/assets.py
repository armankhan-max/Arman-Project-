"""Precompute the static overlay assets: sticker-style avatars, bottom gradient, audio levels."""
import json, sys, wave
import numpy as np
from PIL import Image, ImageFilter

W, H, FPS = 1920, 1080, 30
AV_H = 520           # avatar height on screen
OUTLINE = 9          # white "pasted sticker" border

SRC = {1: "avatar/p1_cut_birefnet-portrait.png", 2: "avatar/p2_cut_b.png", 3: "avatar/p3_cut.png"}


def sticker(path, out, av_h=AV_H):
    im = Image.open(path).convert("RGBA")
    im = im.crop(im.split()[3].getbbox())
    s = av_h / im.height
    im = im.resize((round(im.width * s), av_h), Image.LANCZOS)
    a = im.split()[3].point(lambda v: 255 if v > 100 else 0)
    pad = OUTLINE + 30
    big = Image.new("L", (im.width + 2 * pad, im.height + pad), 0)
    big.paste(a, (pad, pad))
    border = big.filter(ImageFilter.MaxFilter(2 * OUTLINE + 1)).filter(ImageFilter.GaussianBlur(1.2))
    shadow = big.filter(ImageFilter.MaxFilter(2 * OUTLINE + 1)).filter(ImageFilter.GaussianBlur(14))
    canvas = Image.new("RGBA", big.size, (0, 0, 0, 0))
    sh = Image.new("RGBA", big.size, (0, 0, 0, 255)); sh.putalpha(shadow.point(lambda v: int(v * 0.55)))
    sh_c = Image.new("RGBA", big.size, (0, 0, 0, 0)); sh_c.paste(sh, (8, 10), sh)
    canvas.alpha_composite(sh_c)
    wb = Image.new("RGBA", big.size, (255, 255, 255, 255)); wb.putalpha(border)
    canvas.alpha_composite(wb)
    canvas.alpha_composite(im, (pad, pad))
    canvas.save(out)
    print(out, canvas.size)


def levels(wav_path, out):
    with wave.open(wav_path) as w:
        sr = w.getframerate(); ch = w.getnchannels()
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    if ch > 1: x = x.reshape(-1, ch).mean(1)
    hop = sr // FPS; n = len(x) // hop
    win = 2048; bands = 28
    freqs = np.fft.rfftfreq(win, 1 / sr)
    edges = np.geomspace(90, 6000, bands + 1)
    idx = [(np.searchsorted(freqs, edges[i]), max(np.searchsorted(freqs, edges[i + 1]), np.searchsorted(freqs, edges[i]) + 1)) for i in range(bands)]
    hann = np.hanning(win)
    spec = np.zeros((n, bands), np.float32); rms = np.zeros(n, np.float32)
    xp = np.pad(x, (win, win))
    for f in range(n):
        c = f * hop + win
        seg = xp[c - win // 2: c + win // 2]
        rms[f] = np.sqrt(np.mean(seg ** 2))
        m = np.abs(np.fft.rfft(seg * hann))
        spec[f] = [m[a:b].mean() for a, b in idx]
    spec = np.log1p(spec * 4)
    spec /= np.percentile(spec, 99) + 1e-6
    rms /= np.percentile(rms, 99) + 1e-6
    # smooth (attack fast, release slow)
    for f in range(1, n):
        spec[f] = np.maximum(spec[f], spec[f - 1] * 0.72)
        rms[f] = max(rms[f], rms[f - 1] * 0.8)
    np.savez_compressed(out, spec=np.clip(spec, 0, 1), rms=np.clip(rms, 0, 1))
    print(out, n)


if __name__ == "__main__":
    for k, p in SRC.items():
        sticker(p, f"avatar/sticker{k}.png", {1: 520, 2: 450, 3: 540}[k])
    if len(sys.argv) > 1:
        levels(sys.argv[1], "levels.npz")
