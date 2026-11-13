"""Talking-photo avatar: finds the face in a portrait, then animates mouth, blinks and a hand-held
camera feel from the voice track. This is the built-in, free A-roll engine. For studio-grade lip sync
you can upload your own A-roll clip (from any avatar tool) and the editor will cut B-roll around it."""
import math
import random

import numpy as np

from . import gfx
from .core import clamp


def detect(path):
    """→ face geometry as fractions of the image, or a sensible centered guess."""
    info = {"found": False, "face": [0.36, 0.14, 0.28, 0.5]}
    try:
        import cv2
        img = cv2.imread(path)
        g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        H, W = g.shape
        casc = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        best = None
        for sf, mn in ((1.1, 6), (1.05, 4), (1.03, 3)):
            faces = casc.detectMultiScale(g, sf, mn, minSize=(int(W * 0.08), int(W * 0.08)))
            if len(faces):
                best = max(faces, key=lambda f: f[2] * f[3])
                break
        if best is not None:
            x, y, w, h = [float(v) for v in best]
            info = {"found": True, "face": [x / W, y / H, w / W, h / H]}
    except Exception:
        pass
    return info


class Avatar:
    def __init__(self, path, info=None, max_side=1600):
        from PIL import Image
        with Image.open(path) as im:
            im = im.convert("RGBA")
            if max(im.size) > max_side:
                im.thumbnail((max_side, max_side), Image.LANCZOS)
            self.arr = np.asarray(im).copy()
        self.h, self.w = self.arr.shape[:2]
        self.base = gfx.to_skia(self.arr)
        info = info or detect(path)
        fx, fy, fw, fh = info["face"]
        fx, fy, fw, fh = fx * self.w, fy * self.h, fw * self.w, fh * self.h
        self.face = (fx, fy, fw, fh)
        self.found = info.get("found", False)
        mw = fw * 0.36
        mcx, mcy = fx + fw * 0.5, fy + fh * 0.775
        self.mroi = self._clip(mcx - mw * 1.15, mcy - mw * 0.5, mw * 2.3, mw * 1.75)
        x0, y0, rw, rh = self.mroi
        yy, xx = np.mgrid[0:rh, 0:rw].astype(np.float32)
        self.mx, self.my = xx, yy
        seam = mcy - y0
        gx = np.exp(-((xx - (mcx - x0)) / (mw * 0.5)) ** 2)
        below = (yy - seam) / (mw * 0.12)
        rise = np.clip(below, 0, 1)
        decay = np.clip(1 - (yy - seam - mw * 0.12) / max(1.0, rh - seam - mw * 0.12), 0, 1) ** 1.5
        self.mdisp = (gx * rise * decay * mw * 0.24).astype(np.float32)
        self.mgap = (gx ** 1.5).astype(np.float32)
        self.mseam, self.mw = seam, mw
        self.eyes = []
        for ex in (0.3, 0.7):
            ew, eh = fw * 0.24, fh * 0.13
            self.eyes.append(self._clip(fx + fw * ex - ew / 2, fy + fh * 0.4 - eh / 2, ew, eh))
        self.rnd = random.Random(int(fx * 7 + fy))
        self.blinks = []
        t = 1.5
        while t < 7200:
            self.blinks.append(t)
            t += self.rnd.uniform(2.2, 5.5)

    def _clip(self, x, y, w, h):
        x, y = int(clamp(x, 0, self.w - 8)), int(clamp(y, 0, self.h - 8))
        return x, y, int(clamp(w, 8, self.w - x)), int(clamp(h, 8, self.h - y))

    def _mouth(self, amt):
        import cv2
        x0, y0, rw, rh = self.mroi
        src = self.arr[y0:y0 + rh, x0:x0 + rw]
        out = cv2.remap(src, self.mx, self.my - self.mdisp * amt, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        gap = self.mw * 0.2 * amt
        if gap > 1.0:
            d = (self.my - self.mseam - gap * 0.45) / (gap * 0.5)
            m = np.clip(1 - d * d, 0, 1) * self.mgap * min(1.0, amt * 1.3) * 0.8
            dark = np.array([52, 18, 22, 255], np.float32)
            out = (out.astype(np.float32) * (1 - m[..., None]) + dark * m[..., None]).astype(np.uint8)
        return out

    def _blink(self, roi, k):
        import cv2
        x0, y0, rw, rh = roi
        src = self.arr[y0:y0 + rh, x0:x0 + rw]
        yy, xx = np.mgrid[0:rh, 0:rw].astype(np.float32)
        cy = rh / 2.0
        win = np.exp(-((xx - rw / 2) / (rw * 0.42)) ** 4) * np.exp(-((yy - cy) / (rh * 0.46)) ** 4)
        K = 1 + 4.5 * k * win
        sy = cy + (yy - cy) * K
        return cv2.remap(src, xx, np.clip(sy, 0, rh - 1), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)

    def draw(self, c, t, amt, x, y, w, h, zoom=1.0, paint=None):
        """Draw the animated avatar covering rect (x,y,w,h). amt = mouth openness 0..1."""
        import skia
        s = gfx.cover(self.w, self.h, w, h) * zoom
        # hand-held phone-camera feel + breathing + tiny nods on loud syllables
        sway_x = (math.sin(t * 0.53) * 5 + math.sin(t * 1.31 + 1) * 2.5)
        sway_y = (math.sin(t * 0.41 + 2) * 4 + math.sin(t * 1.7) * 1.5) + amt * 3.0
        rot = math.sin(t * 0.33) * 0.35
        breathe = 1.012 + 0.006 * math.sin(t * 1.25)
        fcx, fcy = self.face[0] + self.face[2] / 2, self.face[1] + self.face[3] * 0.55
        c.save()
        c.clipRect(skia.Rect.MakeXYWH(x, y, w, h))
        c.translate(x + w / 2 + sway_x, y + h * 0.5 + sway_y)
        c.rotate(rot)
        c.scale(s * breathe, s * breathe)
        # keep the face framed slightly above centre, like a propped-up phone
        ox = clamp(fcx, w / (2 * s), self.w - w / (2 * s)) if zoom <= 1.01 else fcx
        oy = clamp(self.h / 2 if zoom <= 1.01 else fcy + self.face[3] * 0.1, h / (2 * s), self.h - h / (2 * s))
        c.translate(-ox, -oy)
        p = paint or skia.Paint(AntiAlias=True)
        c.drawImage(self.base, 0, 0, gfx.CUBIC, p)
        if self.found:
            if amt > 0.03:
                x0, y0, rw, rh = self.mroi
                c.drawImage(gfx.to_skia(self._mouth(amt)), x0, y0, gfx.LIN, p)
            k = 0.0
            for b in self.blinks:
                if b > t + 1:
                    break
                d = t - b
                if 0 <= d < 0.2:
                    k = math.sin(d / 0.2 * math.pi)
            if k > 0.05:
                for roi in self.eyes:
                    c.drawImage(gfx.to_skia(self._blink(roi, k)), roi[0], roi[1], gfx.LIN, p)
        c.restore()


def portrait_prompt(persona, fmt_hint="talking to camera"):
    return ("Medium close-up, chest up, of an original fictional character: %s, aged about %s. %s Looking straight into the camera, "
            "mouth gently closed in a slight warm smile, face centered in the upper middle of the frame, both eyes clearly visible, "
            "%s. Filmed on a smartphone propped on a table, eye level, natural window light" % (
                persona.get("look", "a friendly older person"), persona.get("age", 65), persona.get("set", "in a cosy kitchen").rstrip(".") + ".", fmt_hint))
