"""Soundtrack for the Tommy video: licensed BGM per scene (louder for fun/hype, softer for serious) + SFX."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault("TRANSCRIPT", os.path.join(HERE, "transcript.json"))
os.environ.setdefault("MUSIC_DIR", os.path.join(HERE, "..", "gta6", "music"))
sys.path.insert(0, os.path.join(HERE, "..", "gta6"))
sys.path.insert(0, HERE)

import audio_g6 as G  # noqa: E402
from audio_g6 import (sfx, SFX, Track, hit, pop, click, ding, chime_sparkle, buzzer, shutter, coin, pew, boom,  # noqa
                      metal_slam, siren, tick, clap)

G.CUES = [
    (0.0, 15.3, "Crypto", 0.0, 1.15),
    (15.3, 29.5, "Investigations", 0.0, 1.0),
    (29.5, 46.3, "Sneaky_Snitch", 0.0, 1.2),
    (46.3, 55.0, "Hitman", 0.0, 1.0),
    (55.0, 77.3, "Volatile_Reaction", 0.0, 1.25),
    (77.3, 93.4, "Dark_Fog", 0.0, 0.75),
    (93.4, 101.4, "Scheming_Weasel_faster", 0.0, 1.3),
    (101.4, 117.9, "Night_on_the_Docks_-_Sax", 0.0, 0.95),
    (117.9, 141.2, "Funkorama", 0.0, 1.3),
    (141.2, 150.6, "Crypto", 60.0, 1.0),
    (150.6, 165.9, "Volatile_Reaction", 60.0, 1.3),
    (165.9, 173.6, "Dark_Fog", 60.0, 0.85),
    (173.6, 198.0, "Rollin_at_5", 0.0, 1.15),
    (198.0, 224.0, "Hitman", 60.0, 1.1),
    (224.0, 243.8, "Volatile_Reaction", 100.0, 1.3),
    (243.8, 279.0, "Funkorama", 60.0, 1.35),
    (279.0, 303.6, "Crypto", 100.0, 1.0),
    (303.6, 325.0, "Lightless_Dawn", 0.0, 0.9),
    (325.0, 352.9, "Volatile_Reaction", 20.0, 1.3),
    (352.9, 368.6, "Night_on_the_Docks_-_Sax", 40.0, 1.1),
    (368.6, 400.0, "Heartwarming", 0.0, 1.0),
]
_orig_music = G.build_music


def build_music(dur):
    import numpy as np
    out = _orig_music(dur)
    return out


def build_sfx(dur, cuts, wt):
    s = Track(dur)
    SFX.clear()
    sfx(0.1, lambda: metal_slam(0.8), 0.9)
    sfx(wt("15", 2.4), lambda: hit(0.6), 0.7)
    sfx(wt("rob", 8.2), lambda: hit(0.5), 0.6)
    sfx(wt("empire", 12.0), lambda: hit(0.5), 0.6)
    for w_, n_ in (("cold", 19.9), ("loud", 20.9)):
        sfx(wt(w_, n_), lambda: pop(600, 0.4), 0.6)
    sfx(wt("money", 25.0), lambda: coin(0.4), 0.7)
    for w_, n_ in (("deliver", 34.0), ("watch", 35.0), ("keep", 36.0)):
        sfx(wt(w_, n_) + 0.15, lambda: ding(1318.5, 0.35), 0.6)
    sfx(wt("too", 38.9), lambda: hit(0.6), 0.7)
    sfx(wt("reliable", 40.6), lambda: pop(700, 0.4), 0.6)
    sfx(wt("sonny", 47.8), shutter, 0.6)
    sfx(wt("1971", 55.9), lambda: hit(0.6), 0.7)
    sfx(wt("trap", 61.8), lambda: hit(0.8), 0.9)
    sfx(wt("11", 65.3), lambda: hit(0.9), 1.0)
    sfx(70.95, shutter, 0.7)
    sfx(wt("handcuffs", 73.2), click, 1.0)
    sfx(wt("handcuffs", 73.2) + 0.15, click, 1.0)
    sfx(wt("15", 75.7), lambda: hit(0.8), 0.9)
    sfx(77.4, lambda: metal_slam(0.6), 0.7)
    for w_, n_ in (("talks", 79.6), ("deal", 80.9), ("name", 82.6)):
        sfx(wt(w_, n_) - 0.15, lambda: pop(500, 0.4), 0.6)
    sfx(wt("don't", 84.8), lambda: hit(0.7), 0.8)
    for k in range(15):
        sfx(86.0 + k * 6.5 / 15, lambda: tick(0.3), 0.5)
    sfx(wt("subscribe", 96.2) + 0.8, click, 1.0)
    sfx(wt("subscribe", 96.2) + 1.0, lambda: ding(1568, 0.4), 0.8)
    sfx(wt("gates", 102.6), lambda: metal_slam(0.5), 0.6)
    sfx(wt("idea", 116.8), chime_sparkle, 0.7)
    sfx(118.0, chime_sparkle, 0.8)
    for w_, n_ in (("sunshine", 119.5), ("palm", 120.2), ("neon", 121.0)):
        sfx(wt(w_, n_), lambda: pop(700, 0.4), 0.6)
    for w_, n_ in (("fly", 130.0), ("meet", 130.6), ("product", 131.6), ("send", 132.3)):
        sfx(wt(w_, n_) + 0.15, lambda: ding(1318.5, 0.3), 0.5)
    sfx(wt("ken", 135.6), lambda: pop(500, 0.4), 0.6)
    sfx(wt("briefcase", 148.0), lambda: click(0.5), 0.7)
    sfx(wt("table", 149.4), lambda: coin(0.4), 0.7)
    for k in range(14):
        sfx(wt("shooting", 151.0) + k * 0.35, lambda: pew(0.3), 0.6, pan=-0.4 if k % 2 else 0.4)
    sfx(wt("killed", 155.0), lambda: hit(0.6), 0.7)
    sfx(wt("money", 161.0), lambda: buzzer(0.25), 0.5)
    sfx(wt("drugs", 162.4), lambda: buzzer(0.25), 0.5)
    for k in range(3):
        sfx(wt("phone", 164.8) + k * 0.5, lambda: ding(1975, 0.3), 0.6)
    sfx(wt("fortune", 172.6), lambda: hit(0.6), 0.7)
    sfx(wt("colonel", 180.6), lambda: pop(600, 0.4), 0.6)
    for w_, n_ in (("jobs", 185.0), ("contacts", 186.2), ("learn", 187.4)):
        sfx(wt(w_, n_) + 0.15, lambda: ding(1318.5, 0.3), 0.5)
    sfx(wt("diaz", 199.4) - 0.2, shutter, 0.8)
    for w_, n_ in (("paranoid", 203.6), ("loud", 204.2), ("dangerous", 204.6)):
        sfx(wt(w_, n_), lambda: pop(500, 0.4), 0.6)
    sfx(wt("caught", 220.3), lambda: hit(0.6), 0.7)
    for k in range(8):
        sfx(221.0 + k * 0.35, lambda: pew(0.25), 0.5, pan=-0.4 if k % 2 else 0.4)
    for k in range(12):
        sfx(226.6 + k * 0.5, lambda: pew(0.25), 0.5, pan=-0.4 if k % 2 else 0.4)
    sfx(wt("gone", 234.9), lambda: hit(0.6), 0.7)
    sfx(wt("yours", 236.4), lambda: hit(0.7), 0.8)
    for i, n_ in enumerate((246.0, 247.4, 248.8, 250.0, 251.3, 254.7)):
        sfx(n_ - 0.2, shutter, 0.6)
    sfx(wt("fake", 252.6), lambda: hit(0.6), 0.7)
    for k in range(10):
        sfx(258.9 + k * 0.3, lambda: coin(0.2), 0.4)
    for k in range(5):
        sfx(268.5 + k * 0.3, lambda: pew(0.25), 0.5)
    sfx(wt("rich", 271.2), lambda: hit(0.7), 0.8)
    sfx(wt("mister", 278.0), chime_sparkle, 0.6)
    for k in range(3):
        sfx(wt("calls", 282.8) + k * 0.5, lambda: ding(1975, 0.3), 0.6)
    sfx(wt("no", 291.2), lambda: hit(0.9), 1.1)
    for w_, n_ in (("needed", 295.0), ("used", 296.2), ("rot", 297.8), ("deal", 299.4), ("take", 302.8)):
        sfx(wt(w_, n_) - 0.2, lambda: pop(450, 0.4), 0.6)
    sfx(wt("army", 306.0), lambda: hit(0.6), 0.7)
    sfx(wt("his", 320.3), lambda: hit(0.7), 0.8)
    sfx(wt("opens", 321.9), click, 0.8)
    for k in range(24):
        sfx(325.3 + k * 0.28, lambda: pew(0.25), 0.5, pan=-0.4 if k % 2 else 0.4)
    sfx(wt("money", 330.7), lambda: coin(0.4), 0.6)
    for k in range(3):
        sfx(336.0 + k * 0.3, lambda: pew(0.3), 0.6)
    sfx(wt("traitor", 335.4), lambda: hit(0.6), 0.7)
    sfx(wt("1971", 343.8), shutter, 0.6)
    sfx(wt("paid", 347.6), lambda: hit(0.5), 0.6)
    sfx(wt("never", 351.0), lambda: pew(0.5), 0.9)
    sfx(wt("never", 351.0), lambda: hit(0.8), 0.9)
    sfx(wt("gone", 362.5), lambda: hit(0.5), 0.6)
    sfx(wt("king", 367.3), chime_sparkle, 0.8)
    for w_, n_ in (("kid", 370.6), ("silence", 373.8), ("deserved", 375.2)):
        sfx(wt(w_, n_) - 0.2, shutter, 0.6)
    sfx(387.0, lambda: hit(0.6), 0.7)
    for at_, fn, g, pn in SFX:
        s.add(fn(), at_, g, pn)
    return s.stereo(int(dur * G.SR))


G.build_sfx = build_sfx
G.fade_region = lambda x, a, b, fade=0.6: x          # no Lucia-specific music gaps here


def _amb(dur):
    import numpy as np
    return np.zeros((int(dur * G.SR), 2)) + 1e-9


G.build_ambience = _amb

if __name__ == "__main__":
    import timeline  # noqa: F401  so G.main can import SHOTS via scenes_g6 -> patch below
    sys.modules["scenes_g6"] = timeline
    G.main()
