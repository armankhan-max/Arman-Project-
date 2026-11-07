"""Master timeline: joins part A and part B and applies the shared finish (vignette, grain, cut dips)."""
from scenes_a import *  # noqa: F401,F403
from scenes_a import SCENES_A
try:
    from scenes_b import SCENES_B
except ImportError:
    SCENES_B = []

SCENES = SCENES_A + SCENES_B
CUTS = [s for s, _, _ in SCENES[1:]]


import json as _json
import os as _os

_TM = None
_tmp = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "timemap.json")
if _os.path.exists(_tmp):
    _TM = _json.load(open(_tmp))


def to_old(tn):
    """Edited-voice time -> original-voice time (all scenes are keyed to the original words)."""
    if not _TM:
        return tn
    for n0, a, b, nl in _TM["segments"]:
        if tn < n0 + nl:
            return a + (b - a) * max(0.0, tn - n0) / max(nl, 1e-6)
    return _TM["old_duration"] + (tn - _TM["new_duration"])


def to_new(to):
    if not _TM:
        return to
    for n0, a, b, nl in _TM["segments"]:
        if to < b:
            return n0 + nl * max(0.0, to - a) / max(b - a, 1e-6)
    return _TM["new_duration"]


def render_frame(c, tn):
    t = to_old(tn)
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
