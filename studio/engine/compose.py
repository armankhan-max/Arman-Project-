"""The frame renderer. Renderer.frame(t) is a pure function of the project and the time, so the same
code draws editor previews, single stills and the final parallel render."""
import bisect
import math
import os
import random
import subprocess

import numpy as np
import skia

from . import avatar as avatar_mod
from . import catalog, core, gfx, mg, stick
from .core import clamp, ease_out, ease_io, back_out, ramp, lerp, smooth
from .gfx import C, AA, text, text_w, rect, fill, linear, radial, draw_cover


def make_theme(key, seed):
    T = dict(catalog.THEMES.get(key) or catalog.THEMES["abyss"])
    T["key"] = key if key in catalog.THEMES else "abyss"
    r = random.Random(seed)
    sh = r.uniform(-14, 14)
    T["accent"] = core.hue_shift(T["accent"], sh)
    T["accent2"] = core.hue_shift(T["accent2"], sh * 0.6)
    T["v0"] = r.randint(0, 999)
    return T


class VideoReader:
    """Sequential frame access to a clip through an ffmpeg pipe (looped, speed-adjusted, crop-to-fill)."""

    def __init__(self, path, w, h, fps, offset=0.0, speed=1.0):
        self.args = (path, w, h, fps, offset, speed)
        self.w, self.h, self.n = w, h, -1
        self.proc, self.last = None, None

    def _open(self, start_frame):
        self.close()
        path, w, h, fps, offset, speed = self.args
        vf = "setpts=PTS/%.3f,fps=%d,scale=%d:%d:force_original_aspect_ratio=increase,crop=%d:%d" % (speed, fps, w, h, w, h)
        ss = offset + start_frame / float(fps) * speed
        self.proc = subprocess.Popen(["ffmpeg", "-v", "error", "-stream_loop", "-1", "-ss", "%.3f" % ss, "-i", path, "-an", "-vf", vf,
                                      "-pix_fmt", "rgba", "-f", "rawvideo", "-"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        self.n = start_frame - 1

    def get(self, n):
        if self.proc is None or n <= self.n - 1 or n > self.n + 90:
            self._open(max(0, n))
        size = self.w * self.h * 4
        while self.n < n:
            buf = self.proc.stdout.read(size)
            if len(buf) < size:
                return self.last
            self.n += 1
            if self.n == n:
                self.last = skia.Image.frombytes(buf, (self.w, self.h), skia.kRGBA_8888_ColorType)
        return self.last

    def close(self):
        if self.proc is not None:
            try:
                self.proc.stdout.close()
                self.proc.kill()
                self.proc.wait(timeout=5)
            except Exception:
                pass
            self.proc = None


class Renderer:
    def __init__(self, p, W=None, H=None, fps=30):
        st = p["settings"]
        portrait = st.get("aspect") == "9:16"
        self.VW, self.VH = (1080, 1920) if portrait else (1920, 1080)
        res = int(st.get("resolution") or 1080)
        if W is None:
            W, H = (res, res * 16 // 9 // 2 * 2) if portrait else (res * 16 // 9 // 2 * 2, res)
        self.W, self.H, self.fps = W, H, fps
        self.k = W / float(self.VW)
        self.p, self.st = p, st
        self.T = make_theme(st.get("theme", "abyss"), p.get("seed", 1))
        self.shots = sorted(p.get("shots", []), key=lambda s: s["start"])
        self.starts = [s["start"] for s in self.shots]
        self.overlays = p.get("overlays", [])
        self.caps = p.get("captions", [])
        self.cap_starts = [c["start"] for c in self.caps]
        self.dur = p.get("duration") or (self.shots[-1]["start"] + self.shots[-1]["dur"] if self.shots else 1)
        self.surface = skia.Surface(W, H)
        self.sa, self.sb = None, None
        self.readers = {}
        self.avatar = None
        self.env = None
        g = self.T["grade"]
        self.grade = gfx.grade_filter(g[0], g[1], g[2], g[3])
        self._grain = None
        self._vig = None
        envp = os.path.join(p.get("dir", ""), "voice_env_%d.npy" % 30)
        if os.path.exists(envp):
            self.env = np.load(envp)
        av = p.get("avatar") or {}
        if av.get("image") and os.path.exists(av["image"]) and any(s["kind"] == "avatar" for s in self.shots) or (av.get("image") and st.get("avatar_pip")):
            try:
                self.avatar = avatar_mod.Avatar(av["image"], av.get("info"))
            except Exception:
                self.avatar = None

    # ---------------------------------------------------------- helpers
    def speech(self, t):
        if self.env is None:
            return 0.0
        i = int(t * 30)
        return float(self.env[i]) if 0 <= i < len(self.env) else 0.0

    def paint_for(self, sh):
        f = gfx.FILTER_GRADES.get(sh.get("filter") or "none")
        cf = self.grade if not f else skia.ColorFilters.Compose(gfx.grade_filter(*f), self.grade)
        return skia.Paint(ColorFilter=cf, AntiAlias=True)

    def reader(self, sh):
        r = self.readers.get(sh["id"])
        if r is None:
            for k in list(self.readers):
                if len(self.readers) >= 3:
                    self.readers.pop(k).close()
            r = VideoReader(sh["asset"]["path"], self.W, self.H, self.fps, float(sh.get("offset") or 0), float(sh.get("speed") or 1))
            self.readers[sh["id"]] = r
        return r

    def close(self):
        for r in self.readers.values():
            r.close()
        self.readers = {}

    # ---------------------------------------------------------- shots
    def draw_image(self, c, sh, img, tl, paint):
        VW, VH = self.VW, self.VH
        d = max(0.5, sh["dur"])
        u = tl / d
        ue = smooth(clamp(u * 0.9 + 0.05)) if u <= 1 else u
        m = sh.get("motion") or "push_in"
        fx, fy = (sh.get("focus") or [0.5, 0.45])[:2]
        iw, ih = img.width(), img.height()
        if iw / float(ih) < (VW / float(VH)) * 0.8 and m not in ("card", "polaroid"):
            m = "card"  # tall pictures get a framed layout instead of a brutal crop
        if m in ("card", "polaroid", "parallax"):
            b = gfx.blurred(img, 30, 0.2, key=sh["asset"]["path"])
            if self.T["key"] in ("paper", "clean", "comic") and m != "parallax":
                mg.backdrop(c, self.T, tl, sh.get("v", 0), VW, VH)
            else:
                draw_cover(c, b, 0, 0, VW, VH, 1.15 + 0.06 * u, 0.5, 0.5, paint=paint, sampling=gfx.LIN)
                rect(c, 0, 0, VW, VH, self.T["bg"], 0.45)
            ar = iw / float(ih)
            bh = VH * (0.74 if m != "polaroid" else 0.6)
            bw = min(VW * 0.8, bh * ar)
            bh = bw / ar
            sc = 0.96 + 0.06 * ue
            c.save()
            c.translate(VW / 2 + (0.5 - u) * 40 * (1 if sh.get("v", 0) % 2 else -1), VH * 0.48)
            if m == "polaroid":
                c.rotate(-3.5 + (sh.get("v", 0) % 7))
            c.scale(sc, sc)
            pad = 18 if m != "polaroid" else 26
            c.drawRect(skia.Rect.MakeXYWH(-bw / 2 - pad + 10, -bh / 2 - pad + 16, bw + 2 * pad, bh + 2 * pad + (70 if m == "polaroid" else 0)),
                       skia.Paint(Color=C("#000000", 0.5), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 22), **AA))
            if m == "polaroid" or self.T["key"] in ("paper", "archive"):
                rect(c, -bw / 2 - pad, -bh / 2 - pad, bw + 2 * pad, bh + 2 * pad + (70 if m == "polaroid" else 0), "#f3efe4")
            c.save()
            rr = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-bw / 2, -bh / 2, bw, bh), 0 if m == "polaroid" else 14, 0 if m == "polaroid" else 14)
            c.clipRRect(rr, True)
            draw_cover(c, img, -bw / 2, -bh / 2, bw, bh, 1.02 + 0.05 * ue, fx, fy, paint=paint)
            c.restore()
            if m != "polaroid" and self.T["key"] not in ("paper", "archive"):
                c.drawRRect(rr, skia.Paint(Color=C(self.T["ink"], 0.35), Style=skia.Paint.kStroke_Style, StrokeWidth=2, **AA))
            c.restore()
            return
        zoom, rot, dx, dy, blur_a = 1.08, 0.0, 0.0, 0.0, 0.0
        if m == "push_in":
            zoom = lerp(1.04, 1.2, ue)
        elif m == "pull_out":
            zoom = lerp(1.22, 1.05, ue)
        elif m in ("pan_left", "pan_right"):
            zoom = 1.18
            a, b = (0.64, 0.36) if m == "pan_left" else (0.36, 0.64)
            fx = lerp(a, b, ue)
        elif m in ("pan_up", "pan_down"):
            zoom = 1.18
            a, b = (0.64, 0.38) if m == "pan_up" else (0.36, 0.62)
            fy = lerp(a, b, ue)
        elif m == "drift":
            zoom = lerp(1.1, 1.18, ue)
            fx, fy = lerp(fx - 0.08, fx + 0.08, ue), lerp(fy + 0.05, fy - 0.05, ue)
        elif m == "orbit":
            zoom, rot = 1.2, lerp(-1.6, 1.6, ue)
            fx = lerp(fx - 0.06, fx + 0.06, ue)
        elif m == "tilt":
            zoom, rot = lerp(1.16, 1.24, ue), lerp(2.2, 0.0, ue)
        elif m == "focus_pull":
            zoom = lerp(1.06, 1.16, ue)
            blur_a = 1 - ease_out(ramp(tl, 0.1, 1.1))
        elif m == "ramp_push":
            zoom = 1.02 + 0.12 * ease_out(ramp(u, 0, 0.28), 3) + 0.06 * clamp(u)
        elif m == "handheld":
            zoom = lerp(1.1, 1.16, ue)
            dx = math.sin(tl * 1.9) * 7 + math.sin(tl * 4.3 + 1) * 3
            dy = math.sin(tl * 1.4 + 2) * 6 + math.sin(tl * 3.7) * 2.5
            rot = math.sin(tl * 0.9) * 0.4
        elif m == "static":
            zoom = 1.02
        c.save()
        if rot or dx or dy:
            c.translate(VW / 2 + dx, VH / 2 + dy)
            c.rotate(rot)
            c.translate(-VW / 2, -VH / 2)
        draw_cover(c, img, -8, -8, VW + 16, VH + 16, zoom, fx, fy, paint=paint)
        if blur_a > 0.01:
            b = gfx.blurred(img, 18, 0.25, key=sh["asset"]["path"])
            p2 = skia.Paint(ColorFilter=paint.getColorFilter(), AntiAlias=True)
            draw_cover(c, b, -8, -8, VW + 16, VH + 16, zoom, fx, fy, a=blur_a, paint=p2, sampling=gfx.LIN)
        c.restore()

    def draw_shot(self, c, sh, tl):
        VW, VH, T = self.VW, self.VH, self.T
        kind = sh.get("kind")
        asset = sh.get("asset") or {}
        paint = self.paint_for(sh)
        v = (sh.get("v") or 0) + T["v0"]
        img = None
        if asset.get("kind") == "image" and asset.get("path"):
            img = gfx.load_image(asset["path"])
        if kind == "mg" and sh.get("mg"):
            mg.draw(c, sh["mg"], tl, sh["dur"], T, VW, VH, v, img)
        elif kind == "avatar" and self.avatar is not None:
            zoom = 1.0 if (sh.get("v") or 0) % 3 else 1.14  # punch-in on some cuts, like a real edit
            self.avatar.draw(c, sh["start"] + tl, self.speech(sh["start"] + tl), 0, 0, VW, VH, zoom, paint)
        elif kind == "anim2d":
            stick.draw_scene(c, sh, tl, sh["dur"], T, VW, VH, img, self.speech(sh["start"] + tl), paint)
        elif asset.get("kind") == "video" and asset.get("path") and os.path.exists(asset["path"]):
            fr = self.reader(sh).get(int(max(0, tl) * self.fps))
            if fr is not None:
                z = 1.0 + 0.05 * clamp(tl / max(0.5, sh["dur"]))
                c.save()
                c.translate(VW / 2, VH / 2)
                c.scale(z, z)
                c.drawImageRect(fr, skia.Rect.MakeXYWH(-VW / 2, -VH / 2, VW, VH), gfx.LIN, paint)
                c.restore()
            else:
                mg.backdrop(c, T, tl, v, VW, VH)
        elif img is not None:
            self.draw_image(c, sh, img, tl, paint)
        else:
            mg.backdrop(c, T, tl, v, VW, VH)
            if sh.get("key"):
                mg.g_keywords(c, {"words": [sh["key"]]}, tl, sh["dur"], T, VW, VH, v)

    def _offscreen(self, which, sh, tl):
        if self.sa is None:
            self.sa, self.sb = skia.Surface(self.W, self.H), skia.Surface(self.W, self.H)
        s = self.sa if which == 0 else self.sb
        cc = s.getCanvas()
        cc.save()
        cc.scale(self.k, self.k)
        cc.clear(C(self.T["bg"]))
        self.draw_shot(cc, sh, tl)
        cc.restore()
        return s.makeImageSnapshot()

    def transition(self, c, a, b, tl, p, kind):
        """Device-space composite of outgoing shot a and incoming shot b at progress p."""
        W, H = self.W, self.H
        A = self._offscreen(0, a, a["dur"] + tl)
        B = self._offscreen(1, b, tl)
        full = skia.Rect.MakeWH(W, H)

        def put(img, alpha=1.0, m=None):
            pt = skia.Paint(AntiAlias=True)
            pt.setAlphaf(clamp(alpha))
            if m:
                c.save()
                c.translate(W / 2 + m[0], H / 2 + m[1])
                c.scale(m[2], m[2])
                c.translate(-W / 2, -H / 2)
                c.drawImageRect(img, full, gfx.LIN, pt)
                c.restore()
            else:
                c.drawImageRect(img, full, gfx.LIN, pt)
        e = ease_io(p)
        if kind == "fade":
            put(A)
            put(B, e)
        elif kind in ("dip", "flash"):
            col = "#000000" if kind == "dip" else "#ffffff"
            put(A if p < 0.5 else B)
            c.drawRect(full, skia.Paint(Color=C(col, 1 - abs(p - 0.5) * 2)))
        elif kind == "zoom":
            put(A, 1.0, (0, 0, 1 + e * 0.9))
            put(B, clamp(e * 1.6), (0, 0, 0.72 + 0.28 * e))
        elif kind == "push":
            put(A, 1, (-W * e, 0, 1))
            put(B, 1, (W * (1 - e), 0, 1))
        elif kind == "slide":
            put(A, 1, (0, 0, 1 - 0.06 * e))
            c.drawRect(skia.Rect.MakeXYWH(0, H * (1 - e) - 40, W, 40), skia.Paint(Shader=linear(0, H * (1 - e) - 40, 0, H * (1 - e), [C("#000000", 0), C("#000000", 0.5)])))
            put(B, 1, (0, H * (1 - e), 1))
        elif kind == "wipe":
            put(A)
            c.save()
            x = -H * 0.3 + (W + H * 0.6) * e
            path = skia.Path()
            path.moveTo(-10, -10)
            path.lineTo(x + H * 0.15, -10)
            path.lineTo(x - H * 0.15, H + 10)
            path.lineTo(-10, H + 10)
            path.close()
            c.clipPath(path, True)
            put(B)
            c.restore()
            gfx.line(c, x + H * 0.15, -10, x - H * 0.15, H + 10, self.T["accent"], 6 * self.k + 2)
        elif kind == "glitch":
            put(A if p < 0.5 else B)
            r = random.Random(int(p * 12) + 7)
            other = B if p < 0.5 else A
            for _ in range(6):
                y = r.random() * H
                hh = r.uniform(0.02, 0.09) * H
                c.save()
                c.clipRect(skia.Rect.MakeXYWH(0, y, W, hh))
                c.translate(r.uniform(-0.08, 0.08) * W, 0)
                c.drawImageRect(other, full, gfx.LIN, skia.Paint(ColorFilter=skia.ColorFilters.Blend(C(r.choice([self.T["accent"], self.T["accent2"]]), 0.35), skia.BlendMode.kScreen)))
                c.restore()
        elif kind == "burn":
            put(A)
            put(B, e)
            k = 1 - abs(p - 0.5) * 2
            c.drawRect(full, skia.Paint(Shader=radial(W * (0.2 + 0.6 * p), H * 0.4, W * 0.8, [C("#ffb347", 0.85 * k), C("#ff5a1f", 0.4 * k), C("#ff5a1f", 0)]), BlendMode=skia.BlendMode.kScreen))
        elif kind == "pop":
            put(A)
            put(B, clamp(p * 3), (0, 0, 0.88 + 0.12 * back_out(p)))
        else:
            put(B)

    # ---------------------------------------------------------- overlays / captions / finish
    def draw_overlay(self, c, ov, tl):
        T, VW, VH = self.T, self.VW, self.VH
        ty = ov.get("type")
        if ty == "text":
            a = ramp(tl, 0, 0.25) * (1 - ramp(tl, ov["dur"] - 0.25, ov["dur"]))
            size = float(ov.get("size") or 72)
            anim = ov.get("anim") or "pop"
            sc = 1 + 0.35 * (1 - back_out(ramp(tl, 0, 0.3))) if anim == "pop" else 1
            dy = (1 - ease_out(ramp(tl, 0, 0.4))) * 50 if anim == "rise" else 0
            s = ov.get("text", "")
            if anim == "type":
                s = s[:int(len(s) * ramp(tl, 0.05, min(ov["dur"] * 0.6, 0.05 + len(s) * 0.04)))]
            text(c, s, VW * float(ov.get("x", 0.5)), VH * float(ov.get("y", 0.5)) + dy, size * sc, ov.get("color") or T["ink"],
                 ov.get("font") or T["display"], ov.get("align", "center"), a, stroke=ov.get("stroke", "#000000"), stroke_w=size * 0.08, shadow=10)
        elif ty == "keytext":
            p = ramp(tl, 0, 0.22)
            out = 1 - ramp(tl, ov["dur"] - 0.2, ov["dur"])
            s = mg.up(T, ov.get("text", ""))
            size = gfx.fit_size(s, T["display"], VW * 0.8, VH * 0.11, 30) * (1 + 0.3 * (1 - back_out(p)))
            y = VH * (0.2 if ov.get("pos") == "top" else 0.66)
            w = text_w(s, T["display"], size)
            if (ov.get("v", 0) % 2) == 0:
                rect(c, VW / 2 - w / 2 - 26, y - size * 0.92, (w + 52) * ease_out(p), size * 1.2, T["accent"], out)
                text(c, s, VW / 2, y, size, T["bg"], T["display"], "center", min(1, p * 2) * out)
            else:
                text(c, s, VW / 2, y, size, T["ink"], T["display"], "center", min(1, p * 2) * out, stroke="#000000", stroke_w=size * 0.1, shadow=12)
        elif ty in mg.DRAW:
            if ty in mg.FULLSCREEN:
                a = ramp(tl, 0, 0.3) * (1 - ramp(tl, ov["dur"] - 0.3, ov["dur"]))
                c.saveLayerAlpha(None, int(a * 255))
                rect(c, 0, 0, VW, VH, T["bg"], 0.8)
                mg.draw(c, ov, tl, ov["dur"], T, VW, VH, ov.get("v", 0) + T["v0"], None, with_backdrop=False)
                c.restore()
            else:
                mg.draw(c, ov, tl, ov["dur"], T, VW, VH, ov.get("v", 0) + T["v0"])

    def draw_captions(self, c, t):
        style = (self.st.get("captions") or "clean")
        if style == "none" or not self.caps:
            return
        i = bisect.bisect_right(self.cap_starts, t) - 1
        if i < 0:
            return
        cap = self.caps[i]
        if t > cap["end"] + 0.25:
            return
        T, VW, VH = self.T, self.VW, self.VH
        words = cap["words"]
        portrait = VW < VH
        base_y = VH * (0.9 if not portrait else 0.78) - VH * T.get("bars", 0)
        if style == "pop":
            j = max(0, bisect.bisect_right([w["s"] for w in words], t) - 1)
            g0 = (j // 3) * 3
            grp = words[g0:g0 + 3]
            size = VH * (0.085 if not portrait else 0.05)
            total = " ".join(mg.up(T, w["w"]) for w in grp)
            size = gfx.fit_size(total, T["display"], VW * 0.86, size, 26)
            x = VW / 2 - text_w(total, T["display"], size) / 2
            for w in grp:
                s = mg.up(T, w["w"])
                on = w["s"] <= t
                age = t - w["s"]
                sc = 1 + 0.25 * (1 - back_out(ramp(age, 0, 0.14))) if on else 1
                ww = text_w(s, T["display"], size)
                if on:
                    text(c, s, x + ww / 2, base_y, size * sc, T["accent"] if w is grp[min(len(grp) - 1, j - g0)] else "#ffffff", T["display"], "center",
                         stroke="#000000", stroke_w=size * 0.12, shadow=10)
                x += ww + text_w(" ", T["display"], size) + size * 0.12
            return
        size = VH * (0.044 if not portrait else 0.03)
        fnt = T["body"]
        lines = cap.get("lines")
        if lines is None:
            lines, cur = [], []
            for w in words:
                if cur and text_w(" ".join(x["w"] for x in cur + [w]), fnt, size) > VW * 0.72:
                    lines.append(cur)
                    cur = []
                cur.append(w)
            if cur:
                lines.append(cur)
            cap["lines"] = lines
        a = ramp(t, cap["start"] - 0.05, cap["start"] + 0.1)
        y0 = base_y - (len(lines) - 1) * size * 1.3
        for li, ln in enumerate(lines):
            s = " ".join(w["w"] for w in ln)
            w_total = text_w(s, fnt, size)
            y = y0 + li * size * 1.3
            if style == "box":
                rect(c, VW / 2 - w_total / 2 - 22, y - size * 0.98, w_total + 44, size * 1.34, "#000000", 0.72 * a, r=8)
            if style == "highlight":
                x = VW / 2 - w_total / 2
                sp = text_w(" ", fnt, size)
                for w in ln:
                    ww = text_w(w["w"], fnt, size)
                    cur_w = w["s"] <= t < w["e"] + 0.08
                    text(c, w["w"], x, y, size, T["accent"] if cur_w else ("#ffffff" if w["s"] <= t else "#d2d2d2"), fnt, a=a, stroke="#000000", stroke_w=size * 0.14, shadow=6)
                    x += ww + sp
            else:
                text(c, s, VW / 2, y, size, "#ffffff", fnt, "center", a, stroke=None if style == "box" else "#000000", stroke_w=size * 0.13, shadow=0 if style == "box" else 8)

    def finish(self, c, t):
        T, VW, VH = self.T, self.VW, self.VH
        if T["vignette"] > 0:
            fill(c, radial(VW / 2, VH / 2, math.hypot(VW, VH) / 2, [C("#000000", 0), C("#000000", 0), C("#000000", T["vignette"])], [0, 0.55, 1]), 0, 0, VW, VH)
        if T["grain"] > 0:
            if self._grain is None:
                rng = np.random.default_rng(5)
                self._grain = []
                for _ in range(4):
                    n = (rng.normal(128, 46, (270, 480)).clip(0, 255)).astype(np.uint8)
                    arr = np.dstack([n, n, n, np.full_like(n, 255)])
                    self._grain.append(gfx.to_skia(arr))
            g = self._grain[int(t * self.fps) % 4]
            p = skia.Paint(BlendMode=skia.BlendMode.kOverlay)
            p.setAlphaf(T["grain"] * 1.6)
            c.drawImageRect(g, skia.Rect.MakeWH(VW, VH), gfx.LIN, p)
        if T["key"] == "horror" and (int(t * 9) * 2654435761) % 23 == 0:
            rect(c, 0, 0, VW, VH, "#000000", 0.25)
        if T.get("bars"):
            bh = VH * T["bars"]
            rect(c, 0, 0, VW, bh, "#000000")
            rect(c, 0, VH - bh, VW, bh, "#000000")

    # ---------------------------------------------------------- frame
    def frame(self, t):
        c = self.surface.getCanvas()
        c.clear(C(self.T["bg"]))
        VW, VH = self.VW, self.VH
        t = clamp(t, 0, max(0, self.dur - 1e-3))
        if self.shots:
            i = max(0, bisect.bisect_right(self.starts, t) - 1)
            sh = self.shots[i]
            tl = t - sh["start"]
            tr = sh.get("transition") or "cut"
            td = min(float(sh.get("tdur") or 0.5), sh["dur"] * 0.45) if i > 0 else 0
            if i > 0 and tr != "cut" and tl < td:
                self.transition(c, self.shots[i - 1], sh, tl, tl / td, tr)
            else:
                c.save()
                c.scale(self.k, self.k)
                self.draw_shot(c, sh, tl)
                c.restore()
            # drop decoders for shots we have left behind
            for k in list(self.readers):
                if k != sh["id"] and (i == 0 or k != self.shots[i - 1]["id"]):
                    self.readers.pop(k).close()
        c.save()
        c.scale(self.k, self.k)
        if self.T.get("hud") and self.shots and self.shots[i].get("kind") != "mg":
            mg.hud(c, self.T, t, VW, VH, 0.35, "%s  //  %s" % (core.fmt_time(t), (self.p.get("title") or "")[:38].upper()))
        if self.avatar is not None and self.st.get("avatar_pip") and self.shots and self.shots[i].get("kind") not in ("avatar", "mg"):
            r = VH * 0.14
            cx, cy = VW - r - 60, VH - r - 70
            c.save()
            path = skia.Path()
            path.addCircle(cx, cy, r)
            c.clipPath(path, True)
            self.avatar.draw(c, t, self.speech(t), cx - r, cy - r, 2 * r, 2 * r, 2.0)
            c.restore()
            gfx.circle(c, cx, cy, r, "#ffffff", 0.9, stroke=5)
        self.finish(c, t)
        for ov in self.overlays:
            if ov["start"] <= t < ov["start"] + ov["dur"]:
                try:
                    self.draw_overlay(c, ov, t - ov["start"])
                except Exception:
                    pass
        self.draw_captions(c, t)
        fin = ramp(t, 0, 0.35) * (1 - ramp(t, self.dur - 1.1, self.dur - 0.1))
        if fin < 1:
            rect(c, 0, 0, VW, VH, "#000000", 1 - fin)
        c.restore()
        return self.surface

    def frame_bytes(self, t):
        return self.frame(t).makeImageSnapshot().toarray(colorType=skia.kBGRA_8888_ColorType).tobytes()

    def still(self, t, path, quality=86):
        img = self.frame(t).makeImageSnapshot()
        img.save(path, skia.kJPEG, quality) if path.lower().endswith((".jpg", ".jpeg")) else img.save(path, skia.kPNG)
        return path


def render_range(pjson, f0, f1, out, fps, W=None, H=None, crf=20, preset="veryfast"):
    """Worker: frames [f0, f1) → one video part."""
    p = core.load_json(pjson)
    r = Renderer(p, W, H, fps)
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", "%dx%d" % (r.W, r.H), "-r", str(fps), "-i", "-",
                           "-c:v", "libx264", "-preset", preset, "-crf", str(crf), "-pix_fmt", "yuv420p", "-g", str(fps * 2), out], stdin=subprocess.PIPE)
    try:
        for f in range(f0, f1):
            ff.stdin.write(r.frame_bytes(f / float(fps)))
            if (f - f0) % 15 == 0:
                with open(out + ".prog", "w") as fh:
                    fh.write(str(f - f0 + 1))
    finally:
        ff.stdin.close()
        ff.wait()
        r.close()
    with open(out + ".prog", "w") as fh:
        fh.write(str(f1 - f0))
    return out


if __name__ == "__main__":
    import sys
    a = sys.argv
    render_range(a[1], int(a[2]), int(a[3]), a[4], int(a[5]), int(a[6]) if len(a) > 6 and a[6] != "0" else None,
                 int(a[7]) if len(a) > 7 and a[7] != "0" else None, int(a[8]) if len(a) > 8 else 20, a[9] if len(a) > 9 else "veryfast")
