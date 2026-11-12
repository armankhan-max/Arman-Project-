"""2D stickman explainer scenes drawn in code (dark board, rim-lit stick figure, kicker text,
an illustrated prop card or checklist). The mouth moves with the voice, the figure blinks,
breathes and changes pose with the story."""
import math
import os
import random
import re
import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

import store

FPS = 30
INK = (10, 10, 16)
BODY = (238, 232, 214)
RIM = (142, 200, 255)

SHOCK = re.compile(r"\b(deadly|danger|shock|terrif|disaster|explod|dies|died|dead|kill|crash|warning|insane|horrif|scream)\w*", re.I)
THINK = re.compile(r"\?|\b(why|how|what if|imagine|wonder|maybe|secret|mystery)\b", re.I)
HAPPY = re.compile(r"\b(good|great|easy|cheap|save|best|love|win|works|perfect|simple|free)\w*", re.I)


def _font(size, text=""):
    deva = any("ऀ" <= ch <= "ॿ" for ch in text)
    for n in (["FreeSansBold.ttf"] if deva else []) + ["Inter-ExtraBold.otf", "FreeSansBold.ttf"]:
        try:
            return ImageFont.truetype(os.path.join(store.FONTS, n), size)
        except Exception:
            pass
    return ImageFont.load_default()


def _rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def back(t):
    t = max(0.0, min(1.0, t)) - 1
    return t * t * (2.70158 * t + 1.70158) + 1


def pick_pose(text, i):
    if SHOCK.search(text):
        return "shock"
    if THINK.search(text):
        return "think"
    if HAPPY.search(text):
        return "happy"
    return ["talk", "point", "talk", "shrug"][i % 4]


# pose = (left upper, left lower, right upper, right lower) arm angles in degrees (0 = down, 90 = sideways out)
POSES = {
    "talk": (25, 40, 30, 70),
    "point": (20, 15, 95, 95),
    "think": (20, 10, 35, 160),
    "shock": (150, 170, 150, 170),
    "shrug": (60, 120, 60, 120),
    "happy": (130, 150, 25, 40),
}


def _board(w, h, top, bottom, seed):
    g = np.linspace(0, 1, h)[:, None, None]
    arr = (np.array(top) * (1 - g) + np.array(bottom) * g).repeat(w, axis=1)
    img = Image.fromarray(arr.astype(np.uint8), "RGB")
    d = ImageDraw.Draw(img, "RGBA")
    rnd = random.Random(seed)
    for _ in range(140):  # faint dust / stars
        x, y, r = rnd.uniform(0, w), rnd.uniform(0, h), rnd.uniform(0.6, 2.2)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255, rnd.randint(20, 70)))
    vg = Image.new("L", (w // 8, h // 8), 0)
    ImageDraw.Draw(vg).ellipse([-w // 16, -h // 16, w // 8 + w // 16, h // 8 + h // 16], fill=255)
    vg = vg.filter(ImageFilter.GaussianBlur(w // 50)).resize((w, h))
    return Image.composite(img, Image.new("RGB", (w, h), (0, 0, 0)), vg.point(lambda v: 90 + v * 165 // 255))


class Figure:
    """Stick figure drawn on a 2x layer and scaled down for smooth edges."""

    def __init__(self, scale):
        self.s = scale  # head radius in output pixels

    def draw(self, pose_from, pose_to, k, t, talk, blink, look, expr):
        S = 2
        r = self.s * S
        W, H = int(r * 9), int(r * 12)
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        cx = W / 2
        breathe = math.sin(t * 2.2) * r * 0.04
        head_y = r * 1.6 + breathe
        neck = head_y + r
        hip = neck + r * 3.2
        lw = max(4, int(r * 0.32))
        a = [pose_from[j] + (pose_to[j] - pose_from[j]) * ease(k) for j in range(4)]
        if expr == "talk":  # small gesture while speaking
            a[3] += math.sin(t * 5) * 8 * talk
        sh = neck + r * 0.5
        col = BODY

        def seg(x, y, ang, L):
            rad = math.radians(ang)
            return x + math.sin(rad) * L, y + math.cos(rad) * L

        def limb(x, y, a1, a2, side):
            l1, l2 = r * 1.5, r * 1.4
            ex, ey = seg(x, y, a1 * side, l1)
            hx, hy = seg(ex, ey, a2 * side, l2)
            d.line([(x, y), (ex, ey), (hx, hy)], fill=col, width=lw, joint="curve")
            d.ellipse([hx - lw * 0.75, hy - lw * 0.75, hx + lw * 0.75, hy + lw * 0.75], fill=col)
            return hx, hy

        # legs
        step = math.sin(t * 1.3) * 3
        for side in (-1, 1):
            kx, ky = seg(cx, hip, (12 + step) * side, r * 1.7)
            fx, fy = seg(kx, ky, 4 * side, r * 1.7)
            d.line([(cx, hip), (kx, ky), (fx, fy)], fill=col, width=lw, joint="curve")
            d.line([(fx, fy), (fx + side * r * 0.55, fy)], fill=col, width=lw)
        d.line([(cx, neck), (cx, hip)], fill=col, width=int(lw * 1.15))
        limb(cx, sh, a[0], a[1], -1)
        limb(cx, sh, a[2], a[3], 1)
        # head with rim light
        d.ellipse([cx - r - 3, head_y - r - 3, cx + r + 3, head_y + r + 3], fill=RIM)
        d.ellipse([cx - r, head_y - r, cx + r, head_y + r], fill=INK)
        lx, ly = look
        ex = r * 0.38
        eh = r * 0.32 * (0.12 if blink else 1.0)
        if expr == "shock":
            eh *= 1.35
        for sgn in (-1, 1):
            x0 = cx + sgn * ex + lx * r * 0.12
            y0 = head_y - r * 0.12 + ly * r * 0.1
            d.ellipse([x0 - r * 0.17, y0 - eh / 2, x0 + r * 0.17, y0 + eh / 2], fill=(242, 234, 214))
        my = head_y + r * 0.45
        if expr == "shock":
            o = r * (0.16 + 0.08 * talk)
            d.ellipse([cx - o * 0.8, my - o, cx + o * 0.8, my + o], fill=(242, 234, 214))
        elif expr == "happy":
            d.arc([cx - r * 0.38, my - r * 0.35, cx + r * 0.38, my + r * 0.12], 15, 165, fill=(242, 234, 214), width=max(3, lw // 2))
        elif expr == "think":
            d.line([(cx - r * 0.2, my), (cx + r * 0.25, my - r * 0.06)], fill=(242, 234, 214), width=max(3, lw // 2))
        else:
            o = r * 0.06 + r * 0.22 * talk
            d.ellipse([cx - r * 0.24, my - o / 2, cx + r * 0.24, my + o / 2], fill=(242, 234, 214))
        return lay.resize((W // S, H // S), Image.LANCZOS)


def _wrap(d, text, font, maxw, max_lines=3):
    words, lines, cur = text.split(), [], ""
    for wd in words:
        tt = (cur + " " + wd).strip()
        if d.textlength(tt, font=font) <= maxw or not cur:
            cur = tt
        else:
            lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines[:max_lines]


def _card_image(path, size, accent):
    img = ImageOps.fit(Image.open(path).convert("RGB"), (size, size), Image.LANCZOS)
    mask = Image.new("L", (size * 2, size * 2), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, size * 2 - 1, size * 2 - 1], radius=size // 5, fill=255)
    mask = mask.resize((size, size), Image.LANCZOS)
    card = Image.new("RGBA", (size + 16, size + 16), (0, 0, 0, 0))
    ImageDraw.Draw(card).rounded_rectangle([0, 0, size + 15, size + 15], radius=size // 5 + 8, fill=accent + (255,))
    card.paste(img, (8, 8), mask)
    return card


def envelope(audio_path, dur, offset=0.0):
    """Per-frame loudness 0..1 of the narration, used to drive the mouth."""
    n = max(1, round(dur * FPS))
    try:
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{offset:.3f}", "-t", f"{dur:.3f}", "-i", audio_path,
                              "-f", "s16le", "-ac", "1", "-ar", "16000", "-"], capture_output=True, check=True).stdout
        x = np.abs(np.frombuffer(raw, np.int16).astype(np.float32) / 32768)
        hop = 16000 // FPS
        env = np.array([x[i * hop:(i + 1) * hop].mean() if i * hop < len(x) else 0 for i in range(n)])
        env = env / (np.percentile(env, 95) + 1e-6)
        return np.clip(env, 0, 1)
    except Exception:
        return (0.5 + 0.5 * np.sin(np.arange(n) * 1.7)) * 0.7


def render(scene, i, path, dur, w, h, accent="#FFB347", prop=None, audio=None, audio_offset=0.0, side=None):
    """scene: {narration, text, queries}. prop: optional illustration path for the card."""
    acc = _rgb(accent)
    n = max(2, round(dur * FPS))
    text = scene.get("narration", "")
    pose = pick_pose(text, i)
    expr = {"shock": "shock", "think": "think", "happy": "happy"}.get(pose, "talk")
    base = _board(w, h, (14, 22, 38), (6, 9, 16), i)
    land = w > h
    side = side if side is not None else (1 if i % 2 == 0 else -1)  # figure left (1) or right (-1)
    fig = Figure(h * (0.07 if land else 0.05))
    env = envelope(audio, dur, audio_offset) if audio else np.full(n, 0.5)
    kicker = (scene.get("text") or "").strip().upper()
    f_k = _font(int(h * 0.07), kicker)
    f_item = _font(int(h * 0.036))
    tmp = ImageDraw.Draw(base)
    k_lines = _wrap(tmp, kicker, f_k, w * 0.8, 2)
    # right-hand element: illustration card, or a checklist of key words
    card = _card_image(prop, int(h * 0.48), acc) if prop and os.path.exists(prop) else None
    items = []
    if card is None:
        import llm
        seen = llm.keywords(text, 3)
        items = [x.upper() for x in seen]
    good = not SHOCK.search(text)
    fig_x = w * (0.26 if side == 1 else 0.74) if land else w * 0.5
    fig_y = h * (0.86 if land else 0.9)
    el_x = w * (0.68 if side == 1 else 0.32) if land else w * 0.5
    el_y = h * 0.55 if land else h * 0.42
    prev_pose = POSES["talk"]

    def frame(fi):
        t = fi / FPS
        im = base.copy()
        d = ImageDraw.Draw(im, "RGBA")
        # kicker text
        if k_lines:
            a = ease(t / 0.35)
            for j, ln in enumerate(k_lines):
                tw = d.textlength(ln, font=f_k)
                y = h * 0.1 + j * h * 0.08 - (1 - a) * 20
                d.text(((w - tw) / 2, y), ln, font=f_k, fill=(acc if j == len(k_lines) - 1 else (255, 255, 255)) + (int(255 * a),))
        # element
        if card is not None:
            s = back((t - 0.25) / 0.5)
            if s > 0.01:
                cw = max(2, int(card.width * s))
                c2 = card.resize((cw, cw), Image.LANCZOS)
                bob = math.sin(t * 1.6) * h * 0.006
                im.paste(c2, (int(el_x - cw / 2), int(el_y - cw / 2 + bob)), c2)
        else:
            for j, it in enumerate(items):
                ta = t - 0.3 - j * 0.45
                if ta <= 0:
                    continue
                s = back(ta / 0.4)
                bw, bh = w * 0.25, h * 0.075
                x0, y0 = el_x - bw / 2 + (1 - s) * 40, el_y - h * 0.13 + j * h * 0.11
                d.rounded_rectangle([x0, y0, x0 + bw, y0 + bh], radius=bh / 3, fill=(24, 36, 58, int(235 * min(1, s))))
                tw = d.textlength(it, font=f_item)
                d.text((x0 + (bw - bh - tw) / 2, y0 + bh * 0.2), it, font=f_item, fill=(255, 255, 255))
                ix, iy, rr = x0 + bw - bh * 0.6, y0 + bh / 2, bh * 0.3
                d.ellipse([ix - rr, iy - rr, ix + rr, iy + rr], fill=((46, 204, 113) if good else (255, 70, 70)))
                if good:
                    d.line([(ix - rr * 0.5, iy), (ix - rr * 0.1, iy + rr * 0.4), (ix + rr * 0.5, iy - rr * 0.4)], fill=(255, 255, 255), width=4)
                else:
                    d.line([(ix - rr * 0.45, iy - rr * 0.45), (ix + rr * 0.45, iy + rr * 0.45)], fill=(255, 255, 255), width=4)
                    d.line([(ix - rr * 0.45, iy + rr * 0.45), (ix + rr * 0.45, iy - rr * 0.45)], fill=(255, 255, 255), width=4)
        # figure, glides in slightly and settles
        k = min(1, t / 0.5)
        talk = float(env[min(fi, len(env) - 1)])
        blink = (t % 3.7) < 0.12
        look = (0.6 * side if card is not None or items else 0, 0)
        p_to = POSES[pose]
        if pose == "point" and side == -1:
            p_to = (95, 95, 20, 15)
        lay = fig.draw(prev_pose, p_to, k, t, talk, blink, look, expr)
        if side == -1 and pose not in ("point",):
            lay = ImageOps.mirror(lay)
        fx = int(fig_x - lay.width / 2 + (1 - ease(t / 0.5)) * 30 * side * -1)
        fy = int(fig_y - fig.s * 9.3)
        im.paste(lay, (fx, fy), lay)
        d2 = ImageDraw.Draw(im, "RGBA")  # soft floor shadow
        d2.ellipse([fig_x - h * 0.09, fig_y - h * 0.012, fig_x + h * 0.09, fig_y + h * 0.012], fill=(0, 0, 0, 90))
        return im

    proc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}", "-r", str(FPS),
                             "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", path],
                            stdin=subprocess.PIPE)
    try:
        for fi in range(n):
            proc.stdin.write(frame(fi).convert("RGB").tobytes())
    finally:
        proc.stdin.close()
        proc.wait()
    if proc.returncode != 0:
        raise RuntimeError("stickman render failed")
    return path
