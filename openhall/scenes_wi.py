"""Master timeline: joins part A and part B and applies the shared finish (vignette, grain, cut dips)."""
from scenes_a import *  # noqa: F401,F403
from scenes_a import SCENES_A
try:
    from scenes_b import SCENES_B
except ImportError:
    SCENES_B = []

SCENES = SCENES_A + SCENES_B
CUTS = [s for s, _, _ in SCENES[1:]]


def render_frame(c, t):
    c.clear(C("#000000"))
    for start, end, fn in SCENES:
        if start <= t < end:
            c.save()
            fn(c, t)
            c.restoreToCount(1)
            break
    vignette(c, 0.3)
    grain(c, t, 0.04)
    dip = 0.0
    for ct in CUTS:
        d = abs(t - ct)
        if d < 0.1:
            dip = max(dip, 1 - d / 0.1)
    if t < 0.4:
        dip = max(dip, 1 - t / 0.4)
    if t > END - 1.2:
        dip = max(dip, clamp((t - (END - 1.2)) / 1.2))
    if dip:
        tint(c, "#000000", dip * 0.8)


END = 415.0
