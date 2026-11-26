"""Timeline: picks the shot for time t, adds transitions, chapter tag, vignette and grain."""
import skia

from common import SHOTS, W, H, C, P, clamp, smooth, corner_tag, draw_bg, xf, rrect, marker_text, flash
from g6fx import vignette, grain, REC, SCREEN, DIRINV
from common import WORDS, lerp, ease_out
import math
import random
import scenes_t  # noqa: F401  (registers shots)

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


PHOTO = {"t_butcher": None, "t_bank": "the big score", "t_balcony": None}
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
NO_DIRECT = {"t_subscribe", "t_plan", "t_biz", "t_power", "t_used", "t_recap", "t_loyalty", "t_final", "t_butcher", "t_silence", "t_no", "t_king", "t_diaz"}


def _snap(x, lo, hi):
    best = x
    bd = 0.45
    for w, s0, e0 in WORDS:
        if abs(s0 - x) < bd and lo < s0 < hi:
            best, bd = s0, abs(s0 - x)
    return best


def _plan(i):
    """Coverage like the reference: an establishing wide, then clean cuts between a composed close shot of
    a character and the wide, every ~2-3 s, each cut landing on a word."""
    if i in _plans:
        return _plans[i]
    a, b, fn, _ = SHOTS[i]
    rnd = random.Random(i * 7919 + 3)
    segs = []
    if b - a < 3.6:
        segs.append((a, b, "W", 0))
    else:
        t0 = a
        n = 0
        while t0 < b - 0.05:
            L = rnd.uniform(2.0, 3.0) if n == 0 else rnd.uniform(1.8, 2.8)
            t1 = t0 + L
            if b - t1 < 1.4:
                t1 = b
            else:
                t1 = _snap(t1, t0 + 1.5, b - 1.2)
            segs.append((t0, t1, "W" if n % 2 == 0 else "C", n // 2))
            t0 = t1
            n += 1
    _plans[i] = segs
    return segs


_anchor = {}


def _clampc(cx, cy, z):
    hw, hh = W / (2 * z), H / (2 * z)
    return min(max(cx, hw), W - hw), min(max(cy, hh), H - hh)


def _director(i, t, subj):
    a, b, fn, _ = SHOTS[i]
    if fn.__name__ in NO_DIRECT:
        return skia.Matrix()
    for si, (t0, t1, kind, n) in enumerate(_plan(i)):
        if t0 <= t < t1:
            break
    else:
        return skia.Matrix()
    photos = [s for s in subj if s[0] == "photo"]
    ui = [s for s in subj if s[0] in ("ui", "photo", "car")]
    heads = [s for s in subj if s[0] == "head" and 14 < s[3] < 120 and 80 < s[1] < W - 80 and 60 < s[2] < H - 200
             and not any(math.dist((s[1], s[2]), (p[1], p[2])) < p[3] for p in photos)]
    if kind == "W" or not heads:
        return skia.Matrix()
    heads.sort(key=lambda s: s[1])
    h = heads[n % len(heads)]
    key = (i, si)
    anc = _anchor.get(key)
    if anc is None or math.dist(anc[:2], (h[1], h[2])) > 70:
        anc = (h[1], h[2], h[3])
        _anchor[key] = anc
    z = min(max(120.0 / anc[2], 1.45), 1.85)
    cx = anc[0]
    cy = anc[1] + (0.5 - 0.3) * H / z
    cx, cy = _clampc(cx, cy, z)
    hw, hh = W / (2 * z), H / (2 * z)
    for u in ui:
        if -50 < u[1] < W + 50 and -50 < u[2] < H + 50:
            mg = u[3] * 0.7
            if not (cx - hw + mg < u[1] < cx + hw - mg and cy - hh + mg * 0.5 < u[2] < cy + hh - mg * 0.5):
                return skia.Matrix()   # never crop out something the viewer should be seeing
    m = skia.Matrix()
    m.setTranslate(W / 2, H / 2)
    m.preScale(z, z)
    m.preTranslate(-cx, -cy)
    return m


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
