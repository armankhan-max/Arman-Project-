"""Soundtrack for the explainer: reuses the synth kit in ../video/audio.py with a new score and SFX timeline."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "video"))
sys.path.insert(0, HERE)

import numpy as np  # noqa: E402

import scenes as S  # noqa: E402

sys.modules["scenes"] = S
import audio as A  # noqa: E402


def build_music(dur):
    m = A.Track(dur)
    ch = {c["n"]: c["start"] for c in S.CHAPTERS}
    A.cue_warm(m, 0.0, ch[1])
    A.cue_curious(m, ch[1], ch[8], bpm=96, gain=0.9)
    A.cue_roadtrip(m, ch[8], ch[14], bpm=104, gain=0.7)
    A.cue_curious(m, ch[14], ch[99], bpm=100, gain=0.9)
    A.cue_hope(m, ch[99], dur - 1.0, build=0.2)
    A.final_chord(m, dur - 3.2, ["D3", "F#3", "A3", "D4"], 0.5, 3.0)
    x = m.stereo(int(dur * A.SR))
    return x


def build_sfx(dur, cuts):
    s = A.Track(dur)
    for c in S.CHAPTERS[1:]:
        s.add(A.whoosh(0.6, True, 0.6), c["start"] - 0.05, 0.9)
        s.add(A.hit(0.5), c["start"] + 0.3, 0.6)
    for b in S.BEATS[1:]:
        s.add(A.whoosh(0.35, b["i"] % 2 == 0, 0.25), b["show0"] - 0.1, 0.35, pan=0.3 * b["side"])
    for b in S.BEATS:
        if b["kind"] in ("stat", "chart"):
            s.add(A.pop(700, 0.5), b["hit"], 0.6, pan=0.2 * b["side"])
            s.add(A.ding(1318.5, 0.4), b["hit"] + 0.9, 0.5)
            if b.get("is_money") and b["val"] >= 10000:
                s.add(A.chime_sparkle(0.35), b["hit"] + 0.95, 0.6)
        if b["kind"] == "nolist":
            for k in range(3):
                s.add(A.buzzer(0.25), b["start"] + 0.7 + k * 0.7, 0.25)
    for seg in S.T:
        if "20 habits" in seg["text"].lower():
            s.add(A.riser(1.2, 0.3), seg["start"] - 1.1, 0.6)
            s.add(A.hit(0.7), seg["start"], 1.0)
    s.add(A.chime_sparkle(0.4), S.T[-1]["end"] + 0.3, 0.8)
    return s.stereo(int(dur * A.SR))


def build_ambience(dur):
    return np.zeros((int(dur * A.SR), 2))


A.build_music = build_music
A.build_sfx = build_sfx
A.build_ambience = build_ambience

if __name__ == "__main__":
    A.main()
