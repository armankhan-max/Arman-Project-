"""Timeline: picks the shot for time t, adds transitions, chapter tag, vignette and grain."""
import skia

from common import SHOTS, W, H, C, P, clamp, smooth, corner_tag, draw_bg, xf, rrect, marker_text, flash
from g6fx import vignette, grain, REC, SCREEN, DIRINV
from common import WORDS, lerp, ease_out
import math
import random
import scenes_a  # noqa: F401  (registers shots)
try:
    import scenes_b  # noqa: F401
except ImportError:
    pass

SHOTS.sort(key=lambda s: s[0])
XF = 0.0  # hard cuts, like the reference


def _find(t):
    for i, s in enumerate(SHOTS):
        if s[0] <= t < s[1]:
            return i
    return len(SHOTS) - 1 if t >= SHOTS[-1][0] else 0


def _chapter(i):
    for j in range(i, -1, -1):
        if SHOTS[j][3]:
            return SHOTS[j][3]
    return None


def _draw_shot(c, i, t):
    a, b, fn, _ = SHOTS[i]
    c.save()
    fn(c, t, t - a, b - a)
    c.restore()


PHOTO = {"s_mother": "baby Tommy", "s_bar": "one good night", "s_vault": "the score",
         "s_happy": "home.", "s_keep_dream": None}
PH = 1.15
_off = []


def _photo_out(c, i, t):
    """Reference-style 'freeze into a polaroid on the desk' transition at the end of a shot."""
    a, b, fn, _ = SHOTS[i]
    label = PHOTO.get(fn.__name__)
    t0 = b - PH
    k = smooth((t - t0) / PH)
    if not _off:
        _off.append(skia.Surface(W, H))
    sc = _off[0].getCanvas()
    sc.clear(C("#000000"))
    sc.save()
    fn(sc, t0, t0 - a, b - a)
    sc.restore()
    img = _off[0].makeImageSnapshot()
    draw_bg(c, "dark")
    s = 1.0 - 0.5 * k
    rot = -5 * k
    pad = 30 * k
    with xf(c, W / 2, H / 2 - 70 * k, s=s, rot=rot):
        if k > 0.02:
            rrect(c, -W / 2 - pad + 14, -H / 2 - pad + 18, W + pad * 2, H + pad * 2 + 170 * k, 8, "#000000", 0.4 * k)
            rrect(c, -W / 2 - pad, -H / 2 - pad, W + pad * 2, H + pad * 2 + 170 * k, 8, "#f7f3ea")
        c.drawImage(img, -W / 2, -H / 2, skia.SamplingOptions(skia.FilterMode.kLinear))
        if label and k > 0.45:
            marker_text(c, label, 0, H / 2 + 120, 96, "#1d1d1d", a=(k - 0.45) / 0.45, rot=-2)
    flash(c, t, t0, 0.18)


# ---------------------------------------------------------------- director camera
# The reference cuts every ~2 s (median 1.9-2.2 s) and moves the camera with the action: wide establishing
# frame, medium, close-up on whoever matters, pans that follow a subject. Each shot is broken into such
# camera setups; cut points snap to word starts so every cut lands on the voice.
_plans = {}
_last = {}
NO_DIRECT = {"s_subscribe", "s_bugme", "s_style", "s_psycho", "s_four", "s_hundred", "s_two_things", "s_years",
             "s_rigged", "s_part2", "s_loyalty", "s_drive_senator", "s_jobs", "s_100"}


def _snap(x, lo, hi):
    best = x
    bd = 0.45
    for w, s0, e0 in WORDS:
        if abs(s0 - x) < bd and lo < s0 < hi:
            best, bd = s0, abs(s0 - x)
    return best


def _plan(i):
    if i in _plans:
        return _plans[i]
    a, b, fn, _ = SHOTS[i]
    rnd = random.Random(i * 7919 + 3)
    segs = []
    t0 = a
    kinds = []
    while t0 < b - 0.05:
        L = rnd.uniform(1.6, 2.5)
        t1 = t0 + L
        if b - t1 < 1.1:
            t1 = b
        else:
            t1 = _snap(t1, t0 + 1.2, b - 1.0)
        if not segs:
            k = rnd.choice(["W", "P", "M", "W"])
        else:
            opts = ["C", "M", "W", "F", "C", "P", "M"]
            opts = [o for o in opts if o != kinds[-1]]
            k = rnd.choice(opts)
        kinds.append(k)
        segs.append((t0, t1, k, rnd.randint(0, 99), rnd.uniform(-1, 1)))
        t0 = t1
    _plans[i] = segs
    return segs


def _clampc(cx, cy, z):
    hw, hh = W / (2 * z), H / (2 * z)
    return min(max(cx, hw), W - hw), min(max(cy, hh), H - hh)


def _frame(kind, subj, seed, jit, k):
    heads = [s for s in subj if s[0] == "head" and 8 < s[3] < 260 and -100 < s[1] < W + 100 and -100 < s[2] < H]
    objs = [s for s in subj if s[0] in ("car", "photo") and -100 < s[1] < W + 100]
    pool = heads or objs
    if kind == "W" or (not pool and kind in ("C", "F")):
        z = 1.0 + 0.05 * k
        return W / 2 + jit * 20, H / 2, z
    if not pool:
        z = 1.18 + 0.06 * k
        return W / 2 + jit * 160, H / 2 + jit * 60, z
    if kind == "M":
        xs = [s[1] for s in pool]
        ys = [s[2] for s in pool]
        span = max(xs) - min(xs)
        z = min(max(W * 0.75 / (span + 420), 1.15), 1.5)
        return sum(xs) / len(xs), sum(ys) / len(ys) + H * 0.2 / z, z * (1 + 0.04 * k)
    if kind == "C":
        s0 = pool[seed % len(pool)]
        if s0[0] == "head":
            z = min(max(165 / s0[3], 1.25), 2.1)
            return s0[1], s0[2] + H * 0.2 / z, z * (1 + 0.04 * k)
        z = min(max(330 / s0[3], 1.2), 1.8)
        return s0[1], s0[2], z * (1 + 0.04 * k)
    if kind == "P":
        s0 = pool[seed % len(pool)]
        kk = smooth(k)
        z = lerp(1.0, 1.4, kk)
        return lerp(W / 2, s0[1], kk), lerp(H / 2, s0[2] + H * 0.15, kk), z
    if kind == "F":
        A = pool[seed % len(pool)]
        B = pool[(seed + 1) % len(pool)] if len(pool) > 1 else A
        kk = smooth(clamp((k - 0.35) / 0.35))
        z = 1.4 if A[0] == "head" else 1.3
        return lerp(A[1], B[1], kk), lerp(A[2], B[2], kk) + H * 0.18 / z, z
    return W / 2, H / 2, 1.0


def _director(i, t, subj):
    a, b, fn, _ = SHOTS[i]
    if fn.__name__ in NO_DIRECT:
        return skia.Matrix()
    for t0, t1, kind, seed, jit in _plan(i):
        if t0 <= t < t1:
            k = (t - t0) / max(0.01, t1 - t0)
            cx, cy, z = _frame(kind, subj, seed, jit, k)
            if kind != "F" and t0 > a:
                z *= 1 + 0.05 * (1 - ease_out(clamp((t - t0) / 0.35)))
            z = max(1.0, z)
            cx, cy = _clampc(cx, cy, z)
            m = skia.Matrix()
            m.setTranslate(W / 2, H / 2)
            m.preScale(z, z)
            m.preTranslate(-cx, -cy)
            return m
    return skia.Matrix()


def _subjects(i, t):
    a, b, fn, _ = SHOTS[i]
    L = _last.get("k")
    if L and L[0] == i and 0 <= t - L[1] < 0.1:
        return _last["subj"]
    rec = skia.PictureRecorder()
    rc = rec.beginRecording(skia.Rect(0, 0, W, H))
    REC.clear()
    DIRINV[0] = None
    SCREEN[0] = skia.Matrix()
    fn(rc, t, t - a, b - a)
    rec.finishRecordingAsPicture()
    return list(REC)


def render_frame(c, t):
    c.clear(C("#000000"))
    i = _find(t)
    a, b, fn, _ = SHOTS[i]
    if fn.__name__ in PHOTO and PHOTO[fn.__name__] is not None and t > b - PH:
        SCREEN[0] = None
        DIRINV[0] = None
        _photo_out(c, i, t)
    else:
        subj = _subjects(i, t)
        M = _director(i, t, subj)
        inv = skia.Matrix()
        M.invert(inv)
        SCREEN[0] = c.getTotalMatrix()
        DIRINV[0] = inv
        REC.clear()
        c.save()
        c.concat(M)
        fn(c, t, t - a, b - a)
        c.restore()
        _last["k"] = (i, t)
        _last["subj"] = list(REC)
        SCREEN[0] = None
        DIRINV[0] = None
    if i > 0 and t - a < 0.1 and SHOTS[i][3] and SHOTS[i][3] != _chapter(i - 1):
        flash(c, t, a, 0.12)
    vignette(c, 0.45)
    ch = _chapter(i)
    if ch:
        corner_tag(c, ch, a=0.92)
    grain(c, t, 0.045)
