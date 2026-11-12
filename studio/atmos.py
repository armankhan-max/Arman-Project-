"""Atmosphere layers that make still images feel like live footage: drifting dust motes, rolling fog,
rising embers, snow, rain streaks and slow light leaks. Rendered once per video as a looping clip and
screen-blended over every picture shot."""
import math
import os
import random
import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

FPS = 30
KINDS = {"none": "None", "dust": "Floating dust", "fog": "Rolling fog", "embers": "Rising embers", "snow": "Snow",
         "rain": "Rain", "light_leak": "Light leaks", "bokeh": "Bokeh lights"}


def make(kind, path, w, h, seconds=8, seed=7):
    if kind in (None, "", "none"):
        return None
    if os.path.exists(path):
        return path
    rnd = random.Random(seed)
    sw, sh = w // 2, h // 2  # draw at half size, scaled up by ffmpeg (soft anyway)
    n = seconds * FPS
    if kind == "fog":
        big = np.array(Image.effect_noise((sw * 2, sh), 90).filter(ImageFilter.GaussianBlur(sh // 9)), np.float32)
        big = (big - big.min()) / (np.ptp(big) + 1e-6)
    parts = []
    count = {"dust": 70, "embers": 45, "snow": 110, "rain": 160, "bokeh": 22}.get(kind, 0)
    for _ in range(count):
        parts.append([rnd.uniform(0, sw), rnd.uniform(0, sh), rnd.uniform(0.3, 1.0), rnd.uniform(0, 6.28)])
    proc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{sw}x{sh}", "-r", str(FPS),
                             "-i", "-", "-vf", f"scale={w}:{h}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                             "-pix_fmt", "yuv420p", path], stdin=subprocess.PIPE)
    try:
        for f in range(n):
            t = f / FPS
            ph = 2 * math.pi * f / n  # everything loops seamlessly over the clip length
            if kind == "fog":
                off = int((sw) * f / n)
                a = big[:, off:off + sw] if off + sw <= big.shape[1] else np.concatenate([big[:, off:], big[:, :off + sw - big.shape[1]]], 1)
                g = (a * 120 * (0.85 + 0.15 * math.sin(ph))).clip(0, 255).astype(np.uint8)
                im = Image.fromarray(np.stack([g, g, g], -1), "RGB")
            elif kind == "light_leak":
                im = Image.new("RGB", (sw, sh))
                d = ImageDraw.Draw(im)
                for k, col in enumerate(((255, 140, 50), (255, 70, 110), (255, 200, 120))):
                    cx = sw * (0.5 + 0.55 * math.sin(ph + k * 2.1))
                    cy = sh * (0.4 + 0.4 * math.cos(ph * 1 + k))
                    r = sh * (0.45 + 0.1 * math.sin(ph + k))
                    a = 0.5 + 0.5 * math.sin(ph + k * 1.7)
                    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=tuple(int(c * 0.55 * a) for c in col))
                im = im.filter(ImageFilter.GaussianBlur(sh // 6))
            else:
                im = Image.new("RGB", (sw, sh))
                d = ImageDraw.Draw(im)
                for x, y, z, p0 in parts:
                    if kind == "dust":
                        px = (x + math.sin(ph + p0) * 25 * z + sw * z * 0.15 * f / n) % sw
                        py = (y + math.cos(ph * 1 + p0) * 18 * z - sh * 0.1 * z * f / n) % sh
                        r = 0.6 + 1.6 * z
                        c = int(150 * z * (0.6 + 0.4 * math.sin(ph * 3 + p0)))
                        d.ellipse([px - r, py - r, px + r, py + r], fill=(c, c, int(c * 0.9)))
                    elif kind == "embers":
                        py = (y - sh * (1 + z) * f / n) % sh
                        px = (x + math.sin(ph * 2 + p0) * 20) % sw
                        r = 0.8 + 1.4 * z
                        a = 0.5 + 0.5 * math.sin(ph * 6 + p0)
                        d.ellipse([px - r, py - r, px + r, py + r], fill=(int(255 * a * z), int(120 * a * z), int(30 * a * z)))
                    elif kind == "snow":
                        py = (y + sh * (1 + z) * f / n) % sh
                        px = (x + math.sin(ph * 2 + p0) * 14 * z) % sw
                        r = 0.7 + 1.8 * z
                        c = int(220 * z)
                        d.ellipse([px - r, py - r, px + r, py + r], fill=(c, c, c))
                    elif kind == "rain":
                        py = (y + sh * 3 * (0.6 + z) * f / n) % sh
                        px = (x - py * 0.12) % sw
                        c = int(110 * z)
                        d.line([(px, py), (px - 3, py + 14 * z + 6)], fill=(c, c, int(c * 1.1)), width=1)
                    elif kind == "bokeh":
                        px = (x + sw * 0.2 * z * math.sin(ph + p0)) % sw
                        py = (y + sh * 0.1 * math.cos(ph + p0)) % sh
                        r = 6 + 16 * z
                        a = 0.5 + 0.5 * math.sin(ph * 2 + p0)
                        d.ellipse([px - r, py - r, px + r, py + r], fill=(int(120 * a), int(100 * a), int(70 * a)))
                if kind in ("bokeh", "dust", "embers"):
                    im = im.filter(ImageFilter.GaussianBlur(1.2 if kind != "bokeh" else 5))
            proc.stdin.write(im.tobytes())
    finally:
        proc.stdin.close()
        proc.wait()
    return path if proc.returncode == 0 else None


def apply(shot_path, overlay, opacity=0.55, breathe=True):
    """Screen-blend the atmosphere over one rendered picture shot (in place) and add a gentle light 'breath'."""
    tmp = shot_path + ".atm.mp4"
    br = ",eq=eval=frame:brightness='0.018*sin(2*PI*t/2.9)'" if breathe else ""
    fc = (f"[0]format=gbrp[a];[1]format=gbrp[b];[a][b]blend=all_mode=screen:all_opacity={opacity:.2f}:shortest=1,format=yuv420p{br}"
          if overlay else f"[0]format=yuv420p{br}")
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", shot_path] + (["-stream_loop", "-1", "-i", overlay] if overlay else []) + [
        "-filter_complex", fc, "-shortest", "-c:v", "libx264", "-preset", "veryfast", "-crf", "17", "-pix_fmt", "yuv420p", "-an", tmp]
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode == 0 and os.path.getsize(tmp) > 1000:
        os.replace(tmp, shot_path)
    elif os.path.exists(tmp):
        os.remove(tmp)
