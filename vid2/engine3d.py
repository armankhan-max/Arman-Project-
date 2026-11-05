"""Tiny 3D engine on top of skia.

Places flat 2D cartoon characters (billboards) inside a lit 3D set and lets a
real perspective camera move around them. Coordinates: x right, y up, z forward
(into the scene). Units are roughly metres.
"""
import math
import numpy as np
import skia

W, H = 1080, 1920
NEAR = 0.05

INK = skia.Color(22, 20, 30)


def v3(x, y, z):
    return np.array([x, y, z], dtype=float)


def norm(a):
    n = np.linalg.norm(a)
    return a / n if n > 1e-9 else a


def lerp(a, b, t):
    return a + (b - a) * t


def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def ease(t):  # smoothstep-ish ease in/out
    t = clamp(t)
    return t * t * (3 - 2 * t)


def ease_out(t, p=3):
    t = clamp(t)
    return 1 - (1 - t) ** p


def ease_in(t, p=2):
    return clamp(t) ** p


def ease_back(t, s=1.7):  # overshoot pop
    t = clamp(t) - 1
    return t * t * ((s + 1) * t + s) + 1


def rgb(h, a=255):
    h = h.lstrip('#')
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


def mix(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(len(c1)))


def col(c):
    if len(c) == 3:
        return skia.Color(*c)
    return skia.Color(c[0], c[1], c[2], c[3])


class Camera:
    def __init__(self, pos, target, fov=55.0, roll=0.0, shake=(0, 0)):
        self.pos = np.array(pos, float)
        self.target = np.array(target, float)
        self.fov = fov
        self.roll = roll
        f = norm(self.target - self.pos)
        up = v3(0, 1, 0)
        if abs(f[1]) > 0.999:
            up = v3(0, 0, 1)
        r = norm(np.cross(up, f))
        u = np.cross(f, r)
        if roll:
            c, s = math.cos(math.radians(roll)), math.sin(math.radians(roll))
            r, u = r * c + u * s, -r * s + u * c
        self.R = np.stack([r, u, f])
        self.f = (H / 2) / math.tan(math.radians(fov) / 2)
        self.cx = W / 2 + shake[0]
        self.cy = H / 2 + shake[1]

    def to_cam(self, p):
        return self.R @ (np.asarray(p, float) - self.pos)

    def proj_cam(self, pc):
        return (self.cx + self.f * pc[0] / pc[2], self.cy - self.f * pc[1] / pc[2])

    def project(self, p):
        pc = self.to_cam(p)
        if pc[2] < NEAR:
            return None
        return self.proj_cam(pc) + (pc[2],)

    def K(self):
        return np.array([[self.f, 0, self.cx], [0, -self.f, self.cy], [0, 0, 1.0]])


def clip_near(pts):
    out = []
    n = len(pts)
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        ain, bin_ = a[2] >= NEAR, b[2] >= NEAR
        if ain:
            out.append(a)
        if ain != bin_:
            t = (NEAR - a[2]) / (b[2] - a[2])
            out.append(a + (b - a) * t)
    return out


LIGHT = norm(v3(-0.45, 0.8, -0.35))


class Scene:
    """Collects drawables for one frame, then paints them back-to-front."""

    def __init__(self, cam, bg=(30, 30, 40), fog=None, light=None, ambient=0.62):
        self.cam = cam
        self.items = []  # (layer, depth, fn)
        self.bg = bg
        self.fog = fog  # (color, start, end)
        self.light = light if light is not None else LIGHT
        self.ambient = ambient
        self.dof = None  # (focus camera-depth, blur sigma): things farther than focus get soft

    # ---------- shading
    def shade(self, color, normal, center):
        if normal is None:
            k = 1.0
        else:
            d = max(0.0, float(np.dot(normal, self.light)))
            k = self.ambient + (1 - self.ambient) * d
        c = tuple(min(255, int(color[i] * k)) for i in range(3))
        a = color[3] if len(color) > 3 else 255
        if self.fog:
            fc, s, e = self.fog
            dist = np.linalg.norm(center - self.cam.pos)
            t = clamp((dist - s) / (e - s)) * (fc[3] / 255 if len(fc) > 3 else 1)
            c = tuple(int(c[i] + (fc[i] - c[i]) * t) for i in range(3))
        return c + (a,)

    # ---------- primitives
    def poly(self, pts, color, outline=True, layer=1, normal='auto', lw=3.0,
             depth_bias=0.0, cull=False, shade=True, glow=False):
        pts = [np.asarray(p, float) for p in pts]
        center = sum(pts) / len(pts)
        n = None
        if isinstance(normal, str):
            n = norm(np.cross(pts[1] - pts[0], pts[2] - pts[0]))
        elif normal is not None:
            n = np.asarray(normal, float)
        if cull and n is not None and np.dot(n, self.cam.pos - center) <= 0:
            return
        if n is not None and np.dot(n, self.cam.pos - center) < 0:
            n = -n
        cam = self.cam
        cpts = clip_near([cam.to_cam(p) for p in pts])
        if len(cpts) < 3:
            return
        sp = [cam.proj_cam(p) for p in cpts]
        depth = float(sum(p[2] for p in cpts) / len(cpts)) + depth_bias
        c = self.shade(color, n if shade else None, center)

        def draw(canvas, sp=sp, c=c, outline=outline, lw=lw, glow=glow):
            path = skia.Path()
            path.moveTo(*sp[0])
            for p in sp[1:]:
                path.lineTo(*p)
            path.close()
            paint = skia.Paint(AntiAlias=True, Color=col(c))
            if glow:
                paint.setBlendMode(skia.BlendMode.kPlus)
            canvas.drawPath(path, paint)
            if outline:
                canvas.drawPath(path, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style,
                                                 StrokeWidth=lw, Color=INK,
                                                 StrokeJoin=skia.Paint.kRound_Join))
        self.items.append((layer, depth, draw))

    def quad_tex(self, O, U, V, tex, tw, th, layer=1, outline=True, depth_bias=0.0,
                 tint=None, lw=3.0, shade=True, alpha=255):
        """Plane O + u*U + v*V (u,v in 0..1) with a 2D texture drawn by tex(canvas)
        in a tw x th pixel space. Uses an exact homography so it stays correct
        when the camera is close."""
        O, U, V = (np.asarray(a, float) for a in (O, U, V))
        pts = [O, O + U, O + U + V, O + V]
        cam = self.cam
        cpts = clip_near([cam.to_cam(p) for p in pts])
        if len(cpts) < 3:
            return
        sp = [cam.proj_cam(p) for p in cpts]
        center = O + U / 2 + V / 2
        n = norm(np.cross(U, V))
        if np.dot(n, cam.pos - center) < 0:
            n = -n
        k = 1.0
        if shade:
            d = max(0.0, float(np.dot(n, self.light)))
            k = self.ambient + (1 - self.ambient) * d
        fogt = 0.0
        if self.fog:
            fc, s, e = self.fog
            fogt = clamp((np.linalg.norm(center - cam.pos) - s) / (e - s)) * (fc[3] / 255 if len(fc) > 3 else 1)
        Kc = cam.K() @ cam.R
        M = np.column_stack([Kc @ U / tw, Kc @ V / th, Kc @ (O - cam.pos)])
        M = M / M[2, 2] if abs(M[2, 2]) > 1e-12 else M
        m = skia.Matrix.MakeAll(*M.flatten().tolist())
        depth = float(sum(p[2] for p in cpts) / len(cpts)) + depth_bias
        fog = self.fog

        def draw(canvas, sp=sp, m=m, k=k, fogt=fogt):
            path = skia.Path()
            path.moveTo(*sp[0])
            for p in sp[1:]:
                path.lineTo(*p)
            path.close()
            canvas.save()
            canvas.clipPath(path, doAntiAlias=True)
            canvas.saveLayer(paint=skia.Paint(Alphaf=alpha / 255))
            canvas.save()
            canvas.concat(m)
            tex(canvas)
            canvas.restore()
            if k < 0.999:
                canvas.drawPaint(skia.Paint(Color=skia.Color(0, 0, 0, int(255 * (1 - k))),
                                            BlendMode=skia.BlendMode.kSrcATop))
            if tint:
                canvas.drawPaint(skia.Paint(Color=col(tint), BlendMode=skia.BlendMode.kSrcATop))
            if fogt > 0:
                fc = fog[0]
                canvas.drawPaint(skia.Paint(Color=skia.Color(fc[0], fc[1], fc[2], int(255 * fogt)),
                                            BlendMode=skia.BlendMode.kSrcATop))
            canvas.restore()
            canvas.restore()
            if outline:
                canvas.drawPath(path, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style,
                                                 StrokeWidth=lw, Color=INK))
        self.items.append((layer, depth, draw))

    def quad_tex4(self, pts, tex, tw, th, **kw):
        """Texture rect (0,0)-(tw,th) mapped onto planar 4-gon pts[0..3]
        (pts[0]->(0,0), pts[1]->(tw,0), pts[2]->(tw,th), pts[3]->(0,th))."""
        p = [np.asarray(a, float) for a in pts]
        e1 = norm(p[1] - p[0])
        nrm = norm(np.cross(p[1] - p[0], p[3] - p[0]))
        e2 = np.cross(nrm, e1)
        q = [(float(np.dot(a - p[0], e1)), float(np.dot(a - p[0], e2))) for a in p]
        src = [(0, 0), (tw, 0), (tw, th), (0, th)]
        Hm = homography(src, q)
        self._tex_plane(p, p[0], e1, e2, Hm, tex, **kw)

    def _tex_plane(self, pts, O, e1, e2, Hm, tex, layer=1, outline=True, depth_bias=0.0,
                   tint=None, lw=3.0, shade=True, alpha=255):
        cam = self.cam
        cpts = clip_near([cam.to_cam(a) for a in pts])
        if len(cpts) < 3:
            return
        sp = [cam.proj_cam(a) for a in cpts]
        center = sum(pts) / len(pts)
        n = norm(np.cross(e1, e2))
        if np.dot(n, cam.pos - center) < 0:
            n = -n
        k = 1.0
        if shade:
            d = max(0.0, float(np.dot(n, self.light)))
            k = self.ambient + (1 - self.ambient) * d
        fogt = 0.0
        if self.fog:
            fc, s0, e0 = self.fog
            fogt = clamp((np.linalg.norm(center - cam.pos) - s0) / (e0 - s0)) * (fc[3] / 255 if len(fc) > 3 else 1)
        Kc = cam.K() @ cam.R
        M = np.column_stack([Kc @ e1, Kc @ e2, Kc @ (O - cam.pos)]) @ Hm
        M = M / M[2, 2] if abs(M[2, 2]) > 1e-12 else M
        m = skia.Matrix.MakeAll(*M.flatten().tolist())
        depth = float(sum(a[2] for a in cpts) / len(cpts)) + depth_bias
        fog = self.fog

        def draw(canvas, sp=sp, m=m, k=k, fogt=fogt):
            path = skia.Path()
            path.moveTo(*sp[0])
            for a in sp[1:]:
                path.lineTo(*a)
            path.close()
            canvas.save()
            canvas.clipPath(path, doAntiAlias=True)
            canvas.saveLayer(paint=skia.Paint(Alphaf=alpha / 255))
            canvas.save()
            canvas.concat(m)
            tex(canvas)
            canvas.restore()
            if k < 0.999:
                canvas.drawPaint(skia.Paint(Color=skia.Color(0, 0, 0, int(255 * (1 - k))),
                                            BlendMode=skia.BlendMode.kSrcATop))
            if tint:
                canvas.drawPaint(skia.Paint(Color=col(tint), BlendMode=skia.BlendMode.kSrcATop))
            if fogt > 0:
                fc = fog[0]
                canvas.drawPaint(skia.Paint(Color=skia.Color(fc[0], fc[1], fc[2], int(255 * fogt)),
                                            BlendMode=skia.BlendMode.kSrcATop))
            canvas.restore()
            canvas.restore()
            if outline:
                canvas.drawPath(path, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style,
                                                 StrokeWidth=lw, Color=INK))
        self.items.append((layer, depth, draw))

    def box(self, center, size, color, top=None, outline=True, layer=1, lw=3.0, sides=None):
        cx, cy, cz = center
        sx, sy, sz = size[0] / 2, size[1] / 2, size[2] / 2
        P = [v3(cx + a * sx, cy + b * sy, cz + c * sz) for a in (-1, 1) for b in (-1, 1) for c in (-1, 1)]
        # index: a*4+b*2+c with a,b,c in {0,1}
        def p(a, b, c):
            return P[a * 4 + b * 2 + c]
        faces = {
            'top': ([p(0, 1, 0), p(1, 1, 0), p(1, 1, 1), p(0, 1, 1)], v3(0, 1, 0)),
            'bottom': ([p(0, 0, 0), p(0, 0, 1), p(1, 0, 1), p(1, 0, 0)], v3(0, -1, 0)),
            'front': ([p(0, 0, 0), p(1, 0, 0), p(1, 1, 0), p(0, 1, 0)], v3(0, 0, -1)),
            'back': ([p(0, 0, 1), p(0, 1, 1), p(1, 1, 1), p(1, 0, 1)], v3(0, 0, 1)),
            'left': ([p(0, 0, 0), p(0, 1, 0), p(0, 1, 1), p(0, 0, 1)], v3(-1, 0, 0)),
            'right': ([p(1, 0, 0), p(1, 0, 1), p(1, 1, 1), p(1, 1, 0)], v3(1, 0, 0)),
        }
        for name, (pts, n) in faces.items():
            if sides and name not in sides:
                continue
            c = top if (name == 'top' and top is not None) else color
            self.poly(pts, c, outline=outline, layer=layer, normal=n, lw=lw, cull=True)

    def cyl(self, base, radius, height, color, seg=14, layer=1, outline=True, top=None, r2=None):
        r2 = radius if r2 is None else r2
        bx, by, bz = base
        for i in range(seg):
            a0, a1 = 2 * math.pi * i / seg, 2 * math.pi * (i + 1) / seg
            pts = [v3(bx + radius * math.cos(a0), by, bz + radius * math.sin(a0)),
                   v3(bx + radius * math.cos(a1), by, bz + radius * math.sin(a1)),
                   v3(bx + r2 * math.cos(a1), by + height, bz + r2 * math.sin(a1)),
                   v3(bx + r2 * math.cos(a0), by + height, bz + r2 * math.sin(a0))]
            am = (a0 + a1) / 2
            n = v3(math.cos(am), 0.0, math.sin(am))
            self.poly(pts, color, outline=False, layer=layer, normal=n, cull=True)
        topc = top or color
        pts = [v3(bx + r2 * math.cos(2 * math.pi * i / seg), by + height, bz + r2 * math.sin(2 * math.pi * i / seg)) for i in range(seg)]
        self.poly(pts, topc, outline=outline, layer=layer, normal=v3(0, 1, 0), depth_bias=-0.01)

    def shadow(self, pos, rx=0.35, rz=0.22, alpha=70, layer=1):
        x, y, z = pos
        pts = [v3(x + rx * math.cos(a), y + 0.003, z + rz * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 18, endpoint=False)]
        self.poly(pts, (0, 0, 0, alpha), outline=False, layer=layer, normal=None, depth_bias=0.4, shade=False)

    def billboard(self, pos, height, drawfn, layer=1, depth_bias=0.0, flip=False, anchor=1.0):
        """drawfn(canvas) draws in a local space where the figure spans y in
        [-100*anchor .. 100*(1-anchor)] units of 'height = 100'. Scale is set so that
        100 local units == `height` metres. Anchor 1.0 means pos is at the feet."""
        cam = self.cam
        pc = cam.to_cam(pos)
        if pc[2] < NEAR * 4:
            return
        sx, sy = cam.proj_cam(pc)
        s = cam.f * height / pc[2] / 100.0
        depth = float(pc[2]) + depth_bias
        roll = cam.roll

        def draw(canvas, sx=sx, sy=sy, s=s):
            canvas.save()
            canvas.translate(sx, sy)
            if roll:
                canvas.rotate(-roll)
            canvas.scale(-s if flip else s, s)
            drawfn(canvas)
            canvas.restore()
        self.items.append((layer, depth, draw))

    def overlay(self, fn, layer=9, depth=0.0):
        self.items.append((layer, depth, fn))

    def light_shaft(self, top_pts, bottom_pts, color=(255, 240, 200, 40), layer=2):
        """Additive translucent volume between two quads (window -> floor)."""
        pts = top_pts + bottom_pts[::-1]
        cam = self.cam
        proj = [cam.project(p) for p in top_pts + bottom_pts]
        if any(p is None for p in proj):
            return
        a = [(p[0], p[1]) for p in proj[:len(top_pts)]]
        b = [(p[0], p[1]) for p in proj[len(top_pts):]]

        def draw(canvas):
            path = skia.Path()
            path.moveTo(*a[0])
            for q in a[1:]:
                path.lineTo(*q)
            for q in b[::-1]:
                path.lineTo(*q)
            path.close()
            ya = sum(q[1] for q in a) / len(a)
            yb = sum(q[1] for q in b) / len(b)
            xa = sum(q[0] for q in a) / len(a)
            xb = sum(q[0] for q in b) / len(b)
            sh = skia.GradientShader.MakeLinear([(xa, ya), (xb, yb)],
                                                [col(color), skia.Color(color[0], color[1], color[2], 0)])
            canvas.drawPath(path, skia.Paint(AntiAlias=True, Shader=sh, BlendMode=skia.BlendMode.kPlus,
                                             MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 14)))
        self.items.append((layer, 1e3, draw))

    def _bg(self, canvas):
        bg = self.bg
        if isinstance(bg, tuple) and len(bg) == 2 and isinstance(bg[0], tuple):
            sh = skia.GradientShader.MakeLinear([(0, 0), (0, H)], [col(bg[0]), col(bg[1])])
            canvas.drawPaint(skia.Paint(Shader=sh))
        else:
            canvas.drawColor(col(bg))

    def render(self, canvas):
        items = sorted(self.items, key=lambda it: (it[0], -it[1]))
        if not self.dof:
            self._bg(canvas)
            for layer, depth, fn in items:
                fn(canvas)
            return
        focus, sig = self.dof
        far = [it for it in items if it[0] == 0 or (it[0] < 5 and it[1] > focus)]
        near = [it for it in items if not (it[0] == 0 or (it[0] < 5 and it[1] > focus))]
        canvas.saveLayer(None, skia.Paint(ImageFilter=skia.ImageFilters.Blur(sig, sig, skia.TileMode.kClamp)))
        self._bg(canvas)
        for layer, depth, fn in far:
            fn(canvas)
        canvas.restore()
        for layer, depth, fn in near:
            fn(canvas)


def homography(src, dst):
    A = []
    for (x, y), (u, v) in zip(src, dst):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y, -u])
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y, -v])
    _, _, Vt = np.linalg.svd(np.array(A, float))
    Hm = Vt[-1].reshape(3, 3)
    return Hm / Hm[2, 2]


def picture(w, h, fn):
    rec = skia.PictureRecorder()
    c = rec.beginRecording(skia.Rect(0, 0, w, h))
    fn(c)
    return rec.finishRecordingAsPicture()
