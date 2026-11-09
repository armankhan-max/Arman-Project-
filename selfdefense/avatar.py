"""Code-only lip sync for a single still photo.

No neural net: the voice track is turned into per-frame mouth controls
(open / wide / round) and the photo is warped with cv2.remap:
  * the jaw + lower lip are pulled down along a soft weight field,
  * the gap that opens between the lips is painted as a mouth interior
    (dark throat, hint of upper teeth),
  * lips narrow for round vowels and stretch for bright ones,
  * eyelids close for blinks, the whole head gets a tiny nod / sway.
Landmarks were measured by hand on assets/avatar.jpg (1672x940)."""
import math, os
import numpy as np, cv2, soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
FPS = 30

# ---- landmarks (image px) ----
SEAM = [(686, 454), (736, 462), (786, 468)]      # lip line: left corner, middle, right corner
MCX, MHW = 736.0, 51.0                             # mouth centre x, half width
CHIN_Y = 545.0
EYES = [  # cx, cy, half-w, half-h
    (704, 293, 34, 15),
    (837, 316, 32, 12),
]
ROI = (560, 220, 920, 640)                         # x0, y0, x1, y1 – only this part is warped

_c = np.polyfit([p[0] for p in SEAM], [p[1] for p in SEAM], 2)
def seam_y(x): return np.polyval(_c, x)

def sstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)


class Avatar:
    def __init__(self, path=os.path.join(HERE, "assets", "avatar.jpg")):
        img = cv2.imread(path)
        # gentle cinematic grade: warm mids, deeper blacks
        f = img.astype(np.float32) / 255
        f = np.clip((f - 0.03) * 1.06, 0, 1) ** 1.05
        f[..., 2] *= 1.03; f[..., 0] *= 0.96
        self.img = (np.clip(f, 0, 1) * 255).astype(np.uint8)
        x0, y0, x1, y1 = ROI
        self.roi = self.img[y0:y1, x0:x1].copy()
        ys, xs = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        self.xs, self.ys = xs, ys
        sy = seam_y(xs)
        ax = np.abs(xs - MCX)
        # lateral weight of the jaw: full under the mouth, fading to the jaw line
        u = np.clip(ax / MHW, 0, 1)
        lat_mouth = np.sqrt(np.clip(1 - u ** 2.2, 0, 1)) * (1 - sstep(0.9, 1.0, u))   # opening shape
        lat_jaw = 1 - sstep(MHW * 0.9, MHW * 2.6, ax)
        lm = 1 - sstep(MHW * 0.85, MHW * 1.15, ax)
        below = lm * sstep(-1.0, 1.5, ys - sy) + (1 - lm) * sstep(-22, 22, ys - sy)
        down_fade = 1 - sstep(CHIN_Y - 10, CHIN_Y + 45, ys)
        self.w_jaw = (below * np.maximum(lat_mouth, lat_jaw * 0.9) * down_fade).astype(np.float32)
        self.lat_mouth = lat_mouth.astype(np.float32)
        # upper lip lifts a little
        above = sstep(-1, 1, sy - ys) * (1 - sstep(8, 26, sy - ys))
        self.w_up = (above * (1 - sstep(MHW * 0.5, MHW * 1.2, ax))).astype(np.float32)
        # horizontal squeeze/stretch around the lips
        mouth_zone = np.exp(-((ys - sy) / 22.0) ** 2) * (1 - sstep(MHW * 1.1, MHW * 2.0, ax))
        self.w_h = (mouth_zone * (xs - MCX)).astype(np.float32)
        self.sy = sy.astype(np.float32)
        # eye weights
        self.eyes = []
        for cx, cy, hw, hh in EYES:
            d = ((xs - cx) / (hw * 1.2)) ** 2 + ((ys - cy) / (hh * 1.35)) ** 2
            m = (1 - sstep(0.6, 1.0, d)).astype(np.float32)
            top, bot = cy - hh * 1.35, cy + hh * 1.35
            # closed-lid source: skin above the eye stretched down over it
            src_y = (top - hh * 1.6) + (ys - top) * (hh * 1.6) / (bot - top)
            self.eyes.append((m, top, bot, src_y.astype(np.float32), cx, hw, hh, cy))
        # mouth interior colours (BGR)
        self.col_throat = np.array([22, 20, 48], np.float32)
        self.col_tongue = np.array([62, 58, 128], np.float32)
        self.col_teeth = np.array([160, 172, 186], np.float32)

    def face(self, o=0.0, wide=0.0, blink=0.0):
        """o: jaw open 0..1, wide: -1 (round) .. +1 (stretched), blink 0..1 -> warped ROI."""
        d = 15.0 * o
        dy = d * self.w_jaw - 0.22 * d * self.w_up
        dx = -0.10 * wide * self.w_h * (0.4 + o)
        mx = self.xs - dx; my = self.ys - dy
        x0, y0 = ROI[0], ROI[1]
        out = cv2.remap(self.roi, mx - x0, my - y0, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        if d > 0.4:
            gap = d * self.lat_mouth                      # height of opening at this column
            depth = self.ys - self.sy                      # how far below the seam we are
            inside = (depth > 0) & (depth < gap)
            soft = np.clip(np.minimum(depth, gap - depth) / 1.4, 0, 1) * inside
            rel = np.where(gap > 0.1, depth / np.maximum(gap, 0.1), 0)
            col = self.col_throat[None, None, :] * np.ones_like(out, np.float32)
            tongue = sstep(0.55, 1.0, rel)[..., None] * min(1, o * 1.3)
            col = col * (1 - tongue * 0.8) + self.col_tongue * tongue * 0.8
            teeth_h = np.minimum(gap * 0.30, 4.0)
            tv = 1 - sstep(teeth_h * 0.6, teeth_h + 0.8, depth)
            tw = (tv * (1 - sstep(MHW * 0.3, MHW * 0.6, np.abs(self.xs - MCX))))[..., None] * 0.7 * min(1, d / 7)
            shade = 1 - 0.35 * sstep(0.0, 0.6, rel)[..., None]   # darker deeper in
            col = col * shade
            col = col * (1 - tw) + self.col_teeth * tw
            a = soft[..., None].astype(np.float32)
            out = (out * (1 - a) + col * a).astype(np.uint8)
        if blink > 0.02:
            for m, top, bot, src_y, cx, hw, hh, cy_ in self.eyes:
                lid_y = top + (cy_ - top + hh * 0.8) * blink
                closed = cv2.remap(self.roi, self.xs - x0, src_y - y0, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
                cover = (m * (1 - sstep(lid_y - 1.5, lid_y + 1.5, self.ys)))[..., None]
                lash = (np.exp(-((self.ys - lid_y) / 1.3) ** 2) * m * min(1, blink * 2))[..., None] * 0.75
                o32 = out.astype(np.float32) * (1 - cover) + closed.astype(np.float32) * 0.9 * cover
                out = (o32 * (1 - lash) + np.array([20, 16, 18], np.float32) * lash).astype(np.uint8)
        img = self.img.copy()
        img[y0:ROI[3], x0:ROI[2]] = out
        return img


def mouth_track(wav_path, n_frames, fps=FPS):
    """Per-frame (open, wide) from the voice track."""
    a, sr = sf.read(wav_path, dtype="float32")
    if a.ndim > 1: a = a.mean(1)
    hop = sr / fps; win = int(sr * 0.045)
    opn = np.zeros(n_frames, np.float32); wide = np.zeros(n_frames, np.float32)
    han = np.hanning(win).astype(np.float32)
    freqs = np.fft.rfftfreq(win, 1 / sr)
    for i in range(n_frames):
        c = int((i + 0.5) * hop); s = max(0, c - win // 2)
        seg = a[s:s + win]
        if len(seg) < win: seg = np.pad(seg, (0, win - len(seg)))
        rms = math.sqrt(float((seg * seg).mean()) + 1e-12)
        db = 20 * math.log10(rms + 1e-9)
        opn[i] = np.clip((db + 42) / 26, 0, 1)
        sp = np.abs(np.fft.rfft(seg * han)) + 1e-9
        cen = float((sp * freqs).sum() / sp.sum())
        wide[i] = np.clip((cen - 1500) / 1200, -1, 1)
    # attack/release smoothing so the jaw moves like a jaw
    o2 = np.zeros_like(opn); v = 0
    for i, x in enumerate(opn):
        k = 0.65 if x > v else 0.45
        v = v + (x - v) * k; o2[i] = v
    o2 = o2 ** 0.85
    w2 = np.convolve(wide, np.ones(3) / 3, "same")
    return o2, w2


def blink_track(n_frames, fps=FPS, seed=7):
    rng = np.random.default_rng(seed); b = np.zeros(n_frames, np.float32)
    t = 1.2
    while t * fps < n_frames:
        f0 = int(t * fps)
        for k, v in enumerate([0.45, 1.0, 0.85, 0.4, 0.1]):
            if f0 + k < n_frames: b[f0 + k] = v
        t += rng.uniform(2.4, 5.5)
    return b


def head_track(n_frames, opn, fps=FPS):
    """Small nods that follow speech energy + slow sway (dx, dy, rot_deg, scale)."""
    t = np.arange(n_frames) / fps
    env = np.convolve(opn, np.ones(9) / 9, "same")
    nod = np.convolve(np.diff(env, prepend=0), np.ones(5) / 5, "same") * 40
    dx = 3.0 * np.sin(t * 0.37) + 1.5 * np.sin(t * 0.91 + 1)
    dy = 2.0 * np.sin(t * 0.53 + 2) + nod * 2.0
    rot = 0.35 * np.sin(t * 0.29) + 0.15 * np.sin(t * 0.77 + 0.5) + nod * 0.2
    sc = 1 + 0.004 * np.sin(t * 0.23)
    return dx, dy, rot, sc
