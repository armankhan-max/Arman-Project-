from fda.agents.editor import caption_groups
from fda.agents.storyboard import segment
from fda.agents.voiceover import align_text, segments_from_words


def words(n=60, gap=0.0):
    out, t = [], 0.0
    for i in range(n):
        w = "word%d" % i + ("." if i % 12 == 11 else ",") if i % 6 == 5 else "word%d" % i
        out.append({"w": w, "s": round(t, 3), "e": round(t + 0.3, 3)})
        t += 0.38 + (gap if i % 12 == 11 else 0)
    return out


def test_scene_segmentation_uses_real_timings():
    ws = words(80)
    sc = segment(ws, 4.5, ws[-1]["e"])
    assert sc[0]["start"] == 0.0
    for a, b in zip(sc, sc[1:]):
        assert abs(a["end"] - b["start"]) < 1e-6  # contiguous, no gaps
        assert b["a"] == a["b"] + 1  # every word belongs to exactly one scene
    assert sc[-1]["b"] == len(ws) - 1
    assert all(1.5 < s["end"] - s["start"] < 9 for s in sc[:-1])


def test_alignment_fallback_spreads_words_over_speech():
    out = align_text("Hello there. This is a test of alignment.", [(0.5, 2.0), (2.6, 4.0)])
    assert len(out) == 8 and out[0]["s"] >= 0.5 and out[-1]["e"] <= 4.0
    assert all(a["s"] <= b["s"] for a, b in zip(out, out[1:]))
    assert not any(1.99 < w["s"] < 2.59 for w in out)  # nothing placed inside the silence


def test_caption_groups_and_segments():
    ws = words(50, gap=0.8)
    caps = caption_groups(ws)
    assert sum(len(c) for c in caps) == 50 and all(len(c) <= 12 for c in caps)
    segs = segments_from_words(ws)
    assert segs[0][0] == 0 and segs[-1][1] == 49
