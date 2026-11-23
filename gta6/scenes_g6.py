"""Timeline: picks the shot for time t, adds transitions, chapter tag, vignette and grain."""
import skia

from common import SHOTS, W, H, C, P, clamp, smooth, corner_tag
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


def render_frame(c, t):
    c.clear(C("#000000"))
    i = _find(t)
    _draw_shot(c, i, t)
    a = SHOTS[i][0]
    if i > 0 and t - a < XF:
        k = smooth((t - a) / XF)
        c.saveLayerAlpha(None, int((1 - k) * 255))
        _draw_shot(c, i - 1, min(t, SHOTS[i - 1][1] - 1e-3))
        c.restore()
    vignette(c, 0.45)
    ch = _chapter(i)
    if ch:
        corner_tag(c, ch, a=0.92)
    grain(c, t, 0.045)
