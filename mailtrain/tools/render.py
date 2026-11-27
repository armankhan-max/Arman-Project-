"""Old-film renderer.
Reads plan/edl.json (list of shots in EDITED-audio time) and renders 1920x1080 25fps
black & white footage with a 1950s film look (grain, flicker, dust, scratches,
gate weave, vignette, soft contrast) plus slow camera moves on stills.

usage: python render.py edl.json out_dir --jobs 4          (renders parts + joins)
       python render.py edl.json out.png --still <sec>      (single frame preview)
"""
import json, sys, os, subprocess, math, random, collections
import numpy as np, cv2
sys_path_added = __import__("sys").path.insert(0, __import__("os").path.dirname(__file__))
import overlay as OV

W, H, FPS = 1920, 1080, 25
XF = 8  # crossfade frames between shots

# ---------------------------------------------------------------- film look
class Film:
    def __init__(self, seed):
        self.rng = np.random.default_rng(seed)
        r = self.rng
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        d = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
        self.vig = np.clip(1.0 - 0.32 * np.clip(d - 0.35, 0, None) ** 1.6, 0.45, 1).astype(np.float32)
        # clumpy grain bank (generated small then upscaled)
        self.grain = []
        for i in range(10):
            g = r.normal(0, 1, (H // 2 + 8, W // 2 + 8)).astype(np.float32)
            g = cv2.resize(g, (W + 16, H + 16), interpolation=cv2.INTER_LINEAR)
            g += 0.45 * r.normal(0, 1, (H + 16, W + 16)).astype(np.float32)
            self.grain.append(g)
        self.flick = 0.0
        self.weave = np.zeros(2)
        self.scratches = []  # [x, life, dark, width]
        self.f = 0

    def apply(self, img):
        """img float32 HxW 0..1 -> uint8 HxW"""
        r = self.rng
        self.f += 1
        # tone: gentle S-curve, lifted blacks, rolled-off whites
        x = np.clip(img, 0, 1)
        x = x * x * (3 - 2 * x) * 0.55 + x * 0.45
        x = 0.05 + 0.88 * x
        # flicker
        self.flick = 0.8 * self.flick + 0.2 * r.normal(0, 0.03)
        x = x * (1.0 + self.flick) + 0.01 * r.normal()
        x *= self.vig
        # grain
        g = self.grain[self.f % len(self.grain)]
        oy, ox = r.integers(0, 16, 2)
        x = x + 0.055 * g[oy:oy + H, ox:ox + W] * (0.6 + 0.4 * x)
        out = np.clip(x * 255, 0, 255).astype(np.uint8)
        # dust specks
        n = r.poisson(1.6)
        for _ in range(n):
            cx, cy = int(r.integers(0, W)), int(r.integers(0, H))
            rad = int(r.integers(1, 5))
            col = 15 if r.random() < 0.7 else 235
            if r.random() < 0.5:
                cv2.circle(out, (cx, cy), rad, col, -1, cv2.LINE_AA)
            else:
                pts = np.cumsum(r.integers(-4, 5, (6, 2)), 0) + [cx, cy]
                cv2.polylines(out, [pts.astype(np.int32)], False, col, 1, cv2.LINE_AA)
        # hairline scratches
        if r.random() < 0.012:
            self.scratches.append([int(r.integers(80, W - 80)), int(r.integers(6, 40)), r.random() < 0.6, int(r.integers(1, 3))])
        keep = []
        for s in self.scratches:
            s[0] += int(r.integers(-2, 3))
            col = 40 if s[2] else 215
            cv2.line(out, (s[0], 0), (s[0] + int(r.integers(-3, 4)), H), col, s[3], cv2.LINE_AA)
            s[1] -= 1
            if s[1] > 0: keep.append(s)
        self.scratches = keep
        return out

    def weave_offset(self):
        self.weave = 0.85 * self.weave + self.rng.normal(0, 0.35, 2)
        return self.weave


# ---------------------------------------------------------------- sources
def load_still(path, crop=None):
    im = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if im is None:
        raise RuntimeError("cannot read " + path)
    if crop:
        h, w = im.shape
        x0, y0, x1, y1 = crop
        im = im[int(y0 * h):int(y1 * h), int(x0 * w):int(x1 * w)]
    im = im.astype(np.float32) / 255.0
    # auto levels (robust)
    lo, hi = np.percentile(im, [0.7, 99.6])
    if hi - lo > 0.15:
        im = np.clip((im - lo) / (hi - lo), 0, 1)
    # cover-fit to 1.12x the frame so we can move
    h, w = im.shape
    tw, th = int(W * 1.12), int(H * 1.12)
    s = max(tw / w, th / h)
    nw, nh = int(math.ceil(w * s)), int(math.ceil(h * s))
    im = cv2.resize(im, (nw, nh), interpolation=cv2.INTER_CUBIC if s > 1 else cv2.INTER_AREA)
    if s > 1.6:  # soften upscaled pixels, then restore some edge
        im = cv2.GaussianBlur(im, (0, 0), 0.6 * s / 2)
        bl = cv2.GaussianBlur(im, (0, 0), 3)
        im = np.clip(im + 0.5 * (im - bl), 0, 1)
    return im


def still_frames(src, n, rng):
    im = load_still(src["img"], src.get("crop"))
    ih, iw = im.shape
    move = src.get("move") or rng.choice(["in", "in", "out", "left", "right", "up"])
    z0, z1 = 1.0, 1.0
    cx0 = cx1 = iw / 2
    cy0 = cy1 = ih / 2
    base = min(iw / W, ih / H)  # scale where window == frame aspect fully inside
    if move == "in":
        z0, z1 = 1.0, 1.10
    elif move == "out":
        z0, z1 = 1.10, 1.0
    elif move in ("left", "right"):
        z0 = z1 = 1.04
        span = (iw - W * base / 1.04) / 2 * 0.9
        cx0, cx1 = (iw / 2 + span, iw / 2 - span) if move == "left" else (iw / 2 - span, iw / 2 + span)
    elif move in ("up", "down"):
        z0 = z1 = 1.04
        span = (ih - H * base / 1.04) / 2 * 0.9
        cy0, cy1 = (ih / 2 + span, ih / 2 - span) if move == "up" else (ih / 2 - span, ih / 2 + span)
    if ih / iw > 0.62 and move not in ("up", "down"):  # portrait/square: keep faces (upper part)
        cy0 = cy1 = max(H * base / 2 / z0, ih * 0.40)
    if "focus" in src:  # zoom target point (fractions)
        fx, fy = src["focus"]
        cx1 = fx * iw; cy1 = fy * ih
    for i in range(n):
        t = i / max(1, n - 1)
        e = t * t * (3 - 2 * t) * 0.35 + t * 0.65
        z = z0 + (z1 - z0) * e
        ww, hh = W * base / z, H * base / z
        cx = cx0 + (cx1 - cx0) * e
        cy = cy0 + (cy1 - cy0) * e
        cx = min(max(cx, ww / 2), iw - ww / 2)
        cy = min(max(cy, hh / 2), ih - hh / 2)
        yield cx, cy, ww, hh, im


def video_frames(src, n, rng):
    path, t0 = src["vid"], float(src["t"])
    t1 = float(src.get("t1", t0 + 60))
    avail = t1 - t0
    need = n / FPS
    speed = 1.0
    if need > avail:
        speed = max(avail / need, 0.4)
    crop = src.get("crop")  # fractions of the source frame
    vf = []
    if crop:
        x0, y0, x1, y1 = crop
        vf.append(f"crop=iw*{x1 - x0}:ih*{y1 - y0}:iw*{x0}:ih*{y0}")
    else:  # center crop to 16:9
        vf.append("crop=iw:iw*9/16:0:(ih-iw*9/16)/2")
    vf.append(f"setpts=PTS/{speed}")
    vf.append(f"fps={FPS}")
    vf.append(f"scale={int(W*1.06)}:{int(H*1.06)}:flags=lanczos,format=gray")
    cmd = ["ffmpeg", "-loglevel", "error", "-ss", str(t0), "-i", path, "-t", str(need / speed * 1.0 + 1),
           "-an", "-vf", ",".join(vf), "-f", "rawvideo", "-pix_fmt", "gray", "-"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    fw, fh = int(W * 1.06), int(H * 1.06)
    last = None
    zoom_in = rng.random() < 0.6
    for i in range(n):
        b = p.stdout.read(fw * fh)
        if len(b) == fw * fh:
            last = np.frombuffer(b, np.uint8).reshape(fh, fw).astype(np.float32) / 255.0
            lo, hi = np.percentile(last[::8, ::8], [0.5, 99.7])
            if hi - lo > 0.2:
                last = np.clip((last - lo) / (hi - lo), 0, 1)
        if last is None:
            last = np.zeros((fh, fw), np.float32)
        t = i / max(1, n - 1)
        z = 1.0 + 0.045 * (t if zoom_in else 1 - t)
        ww, hh = W * 1.0 / z, H * 1.0 / z
        yield fw / 2, fh / 2, ww, hh, last
    p.stdout.close(); p.wait()


def color_frames(n, val=0.0):
    im = np.full((H + 20, W + 20), val, np.float32)
    for i in range(n):
        yield (W + 20) / 2, (H + 20) / 2, W, H, im


def shot_iter(shot, n, rng):
    s = shot["src"]
    if "img" in s:
        return still_frames(s, n, rng)
    if "vid" in s:
        return video_frames(s, n, rng)
    return color_frames(n, s.get("color", 0.0))


def sample(film, cx, cy, ww, hh, im):
    dx, dy = film.weave_offset()
    sx = ww / W
    M = np.array([[sx, 0, cx - ww / 2 + dx * sx], [0, sx, cy - hh / 2 + dy * sx]], np.float32)
    return cv2.warpAffine(im, M, (W, H), flags=cv2.WARP_INVERSE_MAP | cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


# ---------------------------------------------------------------- render
_v = np.arange(256, dtype=np.float32) / 255
SEPIA = np.stack([np.clip(255 * (_v * 0.93 + 0.06 * _v ** 0.5 + 0.02), 0, 255),
                  np.clip(255 * (_v * 0.86 + 0.03), 0, 255),
                  np.clip(255 * (_v * 0.70 + 0.025), 0, 255)], 1).astype(np.uint8)  # RGB
_OVC = {}
def get_ov(o):
    k = json.dumps(o, sort_keys=True)
    if k not in _OVC:
        if o["kind"] == "tag": _OVC[k] = OV.tag(o["a"], o["b"], seed=hash(k) % 50)
        else: _OVC[k] = OV.depth(int(o["n"]), o.get("a", "Depth"), seed=hash(k) % 50)
    return _OVC[k]
def finish(gray_u8, t, ovs):
    rgb = SEPIA[gray_u8].astype(np.float32)
    for o in ovs:
        if o["t0"] <= t < o["t1"]:
            fi = min(1, (t - o["t0"]) / 0.35, (o["t1"] - t) / 0.35)
            arr = get_ov(o)
            a = arr[..., 3:] * fi
            rgb = rgb * (1 - a) + arr[..., :3] * 255 * a
    return np.clip(rgb, 0, 255).astype(np.uint8)

def render_range(edl, i0, i1, out, seed):
    film = Film(seed)
    rng = random.Random(seed)
    fr0 = int(round(edl[i0]["start"] * FPS))
    fr1 = int(round(edl[i1 - 1]["end"] * FPS))
    enc = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast",
                            "-crf", "27", "-maxrate", "9M", "-bufsize", "18M", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    OVS = [o for sh in edl[i0:i1] for o in sh.get("ovs", [])]
    tail = []  # frames of previous shot overlapping into this one
    written = 0
    for k in range(i0, i1):
        sh = edl[k]
        a = int(round(sh["start"] * FPS)); b = int(round(sh["end"] * FPS))
        last = (k == i1 - 1)
        xf_out = 0 if (last or sh.get("cut") or edl[k + 1].get("cut")) else XF
        n = b - a + xf_out
        frames = []
        for j, st in enumerate(shot_iter(sh, n, rng)):
            f = sample(film, *st)
            if j < len(tail):
                al = (j + 1) / (len(tail) + 1)
                f = tail[j] * (1 - al) + f * al
            fade = sh.get("fade_in", 0)
            if fade and j < fade:
                f = f * (j / fade)
            fo = sh.get("fade_out", 0)
            if fo and j >= (b - a) - fo:
                f = f * max(0.0, ((b - a) - j) / fo)
            if j < (b - a):
                enc.stdin.write(finish(film.apply(f), (fr0 + written) / FPS, OVS).tobytes()); written += 1
            else:
                frames.append(f)
        tail = frames
    enc.stdin.close(); enc.wait()
    return written, fr1 - fr0


def main():
    edl = json.load(open(sys.argv[1]))
    if "--still" in sys.argv:
        t = float(sys.argv[sys.argv.index("--still") + 1])
        k = next(i for i, s in enumerate(edl) if s["start"] <= t < s["end"])
        sh = edl[k]; n = int(round((sh["end"] - sh["start"]) * FPS))
        j = int((t - sh["start"]) * FPS)
        film = Film(1)
        for i, st in enumerate(shot_iter(sh, n, random.Random(1))):
            if i == j:
                f = sample(film, *st)
                for _ in range(3): film.apply(f)
                g = film.apply(f); cv2.imwrite(sys.argv[2], finish(g, t, [o for x in edl for o in x.get("ovs", [])])[..., ::-1]); break
        print("still", t, sh["src"]); return
    outdir = sys.argv[2]; os.makedirs(outdir, exist_ok=True)
    jobs = int(sys.argv[sys.argv.index("--jobs") + 1]) if "--jobs" in sys.argv else 4
    only = sys.argv[sys.argv.index("--part") + 1] if "--part" in sys.argv else None
    # split at hard cuts closest to equal frame counts
    total = edl[-1]["end"]
    bounds = [0]
    for p in range(1, jobs * 3):
        target = total * p / (jobs * 3)
        cands = [i for i, s in enumerate(edl) if s.get("cut") and i > bounds[-1]]
        if not cands: break
        i = min(cands, key=lambda i: abs(edl[i]["start"] - target))
        if i > bounds[-1]: bounds.append(i)
    bounds.append(len(edl))
    bounds = sorted(set(bounds))
    parts = [(bounds[i], bounds[i + 1]) for i in range(len(bounds) - 1)]
    from multiprocessing import Pool
    args = [(edl, a, b, os.path.join(outdir, f"part_{n:03d}.mp4"), 100 + n) for n, (a, b) in enumerate(parts)
            if only is None or str(n) == only]
    with Pool(jobs) as pool:
        res = pool.starmap(render_range, args)
    print(res)
    with open(os.path.join(outdir, "list.txt"), "w") as f:
        for n in range(len(parts)):
            f.write(f"file 'part_{n:03d}.mp4'\n")


if __name__ == "__main__":
    main()
