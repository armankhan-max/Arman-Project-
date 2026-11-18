"""Scene table + per-frame compositor."""
import os

import skia

from pgfx import *  # noqa: F401,F403
from psets import *  # noqa: F401,F403
from pscenes_a import *  # noqa: F401,F403
from pscenes_b import *  # noqa: F401,F403

SCENES = [
    (0.0, 3.9, s_hosp), (3.9, 6.9, s_mind), (6.9, 10.7, s_dreamwalk), (10.7, 14.3, s_nocane),
    (14.3, 22.2, s_reality), (22.2, 24.0, s_twoweeks), (24.0, 29.1, s_notebook), (29.1, 31.0, s_lazy),
    (31.0, 33.6, s_title), (33.6, 38.5, s_oet), (38.5, 46.6, s_split), (46.6, 53.8, s_expect),
    (53.8, 55.4, s_fantasy), (55.4, 62.7, s_drift), (62.7, 63.8, s_shower), (63.8, 64.9, s_commute),
    (64.9, 67.4, s_ceiling), (67.4, 71.5, s_interview), (71.5, 73.4, s_noeffort), (73.4, 76.0, s_tracked),
    (76.0, 83.2, s_graph), (83.2, 90.9, s_quote1), (90.9, 94.2, s_pattern), (94.2, 100.3, s_crush),
    (100.3, 108.9, s_exam), (108.9, 118.0, s_grads), (118.0, 124.3, s_host1), (124.3, 131.4, s_needs),
    (131.4, 136.3, s_burger), (136.3, 138.3, s_host2), (138.3, 148.6, s_kappes), (148.6, 157.5, s_assigned),
    (157.5, 160.1, s_energy), (160.1, 169.5, s_heels), (169.5, 179.6, s_bars), (179.6, 183.5, s_morewant),
    (183.5, 189.6, s_jobseeker), (189.6, 193.9, s_lovesick), (193.9, 199.6, s_mindmoves), (199.6, 205.6, s_relax),
    (205.6, 217.0, s_salary), (217.0, 222.4, s_salreal), (222.4, 228.6, s_pleasant), (228.6, 230.9, s_host3),
    (230.9, 232.5, s_ch2), (232.5, 243.4, s_gol), (243.4, 251.4, s_lawyer), (251.4, 257.6, s_noticed),
    (257.6, 265.0, s_week), (265.0, 269.6, s_commit), (269.6, 276.6, s_premature), (276.6, 280.9, s_gap),
    (280.9, 285.3, s_host4), (285.3, 289.75, s_friend), (289.75, 291.2, s_ch3), (291.2, 302.9, s_fear),
    (302.9, 312.6, s_sirois), (312.6, 317.9, s_quote2), (317.9, 324.9, s_seesaw), (324.9, 334.5, s_anxious),
    (334.5, 345.9, s_sitdream), (345.9, 356.0, s_bill), (356.0, 365.1, s_loop), (365.1, 367.0, s_ch4),
    (367.0, 371.4, s_host5), (371.4, 380.9, s_contrast), (380.9, 385.8, s_obstacles), (385.8, 394.4, s_ifthen),
    (394.4, 399.9, s_advance), (399.9, 404.3, s_truly), (404.3, 410.0, s_woop), (410.0, 431.5, s_evidence),
    (431.5, 436.9, s_modest), (436.9, 447.6, s_backhosp), (447.6, 453.9, s_finishline), (453.9, 459.6, s_oneminute),
    (459.6, 464.6, s_questions), (464.6, 472.6, s_end),
]
END = 472.6
# hard cuts get a quick dip; scene-internal cuts too
CUTS = [s for (s, e, f) in SCENES[1:]] + [27.1, 30.15, 113.6, 239.7, 254.0, 261.7, 338.5, 347.9, 376.6, 389.5,
                                          467.6]


def render_frame(c, t):
    c.clear(C("#000000"))
    for start, end, fn in SCENES:
        if start <= t < end:
            c.save()
            fn(c, t)
            c.restoreToCount(1)
            break
    vignette(c, 0.28)
    grain(c, t, 0.035)
    dip = 0.0
    for ct in CUTS:
        d = abs(t - ct)
        if d < 0.12:
            dip = max(dip, 1 - d / 0.12)
    if t < 0.5:
        dip = max(dip, 1 - t / 0.5)
    if t > END - 1.0:
        dip = max(dip, (t - (END - 1.0)) / 1.0)
    if dip:
        tint(c, "#000000", dip * 0.8)
