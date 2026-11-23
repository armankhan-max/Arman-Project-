"""Timeline: picks the shot for time t, adds transitions, chapter tag, vignette and grain."""
import skia

from common import SHOTS, W, H, C, P, clamp, smooth, corner_tag, draw_bg, xf, rrect, marker_text, flash
from g6fx import vignette, grain
import scenes_a  # noqa: F401  (registers shots)
try:
    import scenes_b  # noqa: F401
except ImportError:
    pass

SHOTS.sort(key=lambda s: s[0])
XF = 0.22  # crossfade seconds


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


def render_frame(c, t):
    c.clear(C("#000000"))
    i = _find(t)
    a, b, fn, _ = SHOTS[i]
    if fn.__name__ in PHOTO and PHOTO[fn.__name__] is not None and t > b - PH:
        _photo_out(c, i, t)
    else:
        _draw_shot(c, i, t)
    a = SHOTS[i][0]
    if i > 0 and t - a < XF:
        k = smooth((t - a) / XF)
        c.saveLayerAlpha(None, int((1 - k) * 255))
        pt = min(t, SHOTS[i - 1][1] - 1e-3)
        pfn = SHOTS[i - 1][2]
        if PHOTO.get(pfn.__name__):
            _photo_out(c, i - 1, pt)
        else:
            _draw_shot(c, i - 1, pt)
        c.restore()
    vignette(c, 0.45)
    ch = _chapter(i)
    if ch:
        corner_tag(c, ch, a=0.92)
    grain(c, t, 0.045)
