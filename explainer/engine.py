"""Beat engine: a beat is a set of elements laid out automatically and shown
from its start time until the next beat starts. Elements enter on their own
time (usually the word where the narrator says it)."""
import bisect
import json
import math
import os
import re

from kit import *  # noqa: F401,F403

HERE = os.path.dirname(os.path.abspath(__file__))
_WORDS = []
for seg in json.load(open(os.path.join(HERE, "transcript.json"))):
    for w in seg["words"]:
        _WORDS.append((w["s"], re.sub(r"[^a-z0-9]", "", w["w"].lower())))
_WSTARTS = [s for s, _ in _WORDS]


MISSES = []


def tw(prefix, after):
    """Time of the first spoken word starting with `prefix` at/after `after` s."""
    i = bisect.bisect_left(_WSTARTS, after - 1.5)
    for s, w in _WORDS[i:i + 120]:
        if w.startswith(prefix):
            return s
    MISSES.append((prefix, after))
    return after


# ------------------------------------------------------------------ elements
class El:
    t = None
    h = 0
    w = 0

    def draw(self, c, x, y, t, align, max_w=1640):  # y = top of element box
        pass


class T(El):
    """Headline line with *red* / ^amber^ accents."""

    def __init__(self, text, t=None, size=92, color=INK, weight="Black", gap=None):
        self.text, self.t, self.size, self.color, self.weight = text, t, size, color, weight
        self.h = size * 1.22 if gap is None else gap
        clean = text.replace("*", "").replace("^", "")
        self.w = text_w(clean, size, weight)

    def draw(self, c, x, y, t, align, max_w=1640):
        rich_line(c, self.text, x, y + self.size * 0.95, self.size, t, self.t, self.color, self.weight, align,
                  max_w=max_w)


def S(text, t=None, size=50, color=MUTED):
    """Supporting line: dropped on purpose to keep the screen minimal."""
    e = SP(0)
    e.t = t if t is not None else 0
    return e


class K(El):
    """Kicker pill: yellow rounded tag with black text (date, place)."""

    def __init__(self, text, t=None, size=34, color=ACC):
        self.text, self.t, self.size, self.color = text.upper(), t, size, color
        self.w = text_w(self.text, size * 0.95, "ExtraBold") + size * 1.2
        self.h = size * 1.9

    def draw(self, c, x, y, t, align, max_w=1640):
        p = ease_out(prog(t, self.t, 0.35))
        if p <= 0:
            return
        x0 = x - self.w / 2 if align == "center" else x
        s = lerp(0.7, 1, back_out(prog(t, self.t, 0.4)))
        with xf(c, x0 + self.w / 2, y + self.size * 0.75, s=s, alpha=p):
            rr(c, -self.w / 2, -self.size * 0.72, self.w, self.size * 1.44, self.size * 0.72, self.color)
            draw_text(c, self.text, 0, self.size * 0.36, self.size, "#111111", "Inter-Black-ish", 1.0, "center") \
                if False else draw_text(c, self.text, 0, self.size * 0.36, self.size * 0.95, "#111111", "ExtraBold", 1.0, "center")


class N(El):
    """Count-up number."""

    def __init__(self, value, t=None, dec=0, pre="", suf="", size=210, color=ACC, dur=1.1, comma=True):
        self.v, self.t, self.dec, self.pre, self.suf, self.size, self.color, self.dur = \
            value, t, dec, pre, suf, size, color, dur
        self.comma = comma
        self.h = size * 1.08
        self.w = text_w(self.fmt(value), size)

    def fmt(self, v):
        s = f"{v:,.{self.dec}f}" if self.comma else f"{v:.{self.dec}f}"
        return self.pre + s + self.suf

    def draw(self, c, x, y, t, align, max_w=1640):
        p = prog(t, self.t, 0.35)
        if p <= 0:
            return
        k = ease_out(prog(t, self.t, self.dur))
        s = self.fmt(self.v * k)
        size = self.size * lerp(0.85, 1.0, back_out(prog(t, self.t, 0.5)))
        draw_text(c, s, x, y + self.size * 0.86, size, self.color, a=ease_out(p), align=align)


class I(El):
    """Icon. burn/smoke = time flames/smoke start."""

    def __init__(self, name, t=None, size=300, anim="pop", burn=None, smoke=None, **kw):
        self.name, self.t, self.size, self.anim, self.burn_t, self.smoke_t, self.kw = \
            name, t, size, anim, burn, smoke, kw
        self.h = size * 1.12
        self.w = size

    def draw(self, c, x, y, t, align, max_w=0):
        cx = x if align == "center" else x + self.size / 2
        cy = y + self.h / 2
        kw = {k: (v(t) if callable(v) else v) for k, v in self.kw.items()}
        if self.smoke_t is not None:
            smoke(c, cx, cy - self.size * 0.25, self.size, t, self.smoke_t)
        icon(c, self.name, cx, cy, self.size, t, self.t, anim=self.anim, **kw)
        if self.burn_t is not None:
            burn(c, cx, cy + self.size * 0.1, self.size * 0.8, t, self.burn_t)


class G(El):
    """Custom graphic: fn(c, cx, top_y, t)."""

    def __init__(self, fn, h, t=None, w=900):
        self.fn, self.h, self.t, self.w = fn, h, t, w

    def draw(self, c, x, y, t, align, max_w=0):
        if t >= self.t:
            self.fn(c, x, y, t)


class LIST(El):
    """Left-aligned bullet list, centred as a block. items = [(text, t), ...]"""

    def __init__(self, items, size=74, t=None):
        self.items = [(T(s, tt, size), tt) for s, tt in items]
        self.t = items[0][1] if t is None else t
        self.size = size
        self.h = size * 1.55 * len(items)
        self.w = max(e.w for e, _ in self.items) + size * 0.9

    def draw(self, c, x, y, t, align, max_w=1640):
        x0 = x - self.w / 2 if align == "center" else x
        for i, (e, tt) in enumerate(self.items):
            yy = y + i * self.size * 1.55
            p = ease_out(prog(t, tt, 0.4))
            if p > 0:
                circ(c, x0 + self.size * 0.22, yy + self.size * 0.6, self.size * 0.12 * back_out(p), ACC, p)
            e.draw(c, x0 + self.size * 0.9, yy, t, "left", max_w=max_w)


class SP(El):  # spacer
    def __init__(self, h=30):
        self.h = h
        self.t = 0


# --------------------------------------------------------------------- beats
BEATS = []
CHAPTERS = []  # (start, num, name)


class Beat:
    def __init__(self, start, els, layout="stack", end=None, tape=False):
        self.start, self.els, self.layout, self.end, self.tape = start, els, layout, end, tape
        self.captions = None  # decided in finalize()
        k = 0
        for e in els:
            if e.t is None:
                e.t = start + 0.12 + 0.12 * k
                k += 1

    def draw(self, c, t):
        dur_out = 0.32
        a_out = 1 - ease_io(prog(t, self.end - dur_out, dur_out))
        push = 1 + 0.018 * clamp((t - self.start) / max(1.0, self.end - self.start))
        with xf(c, W / 2, H / 2 + (1 - a_out) * -30, s=push, alpha=a_out):
            with xf(c, -W / 2, -H / 2):
                if self.tape:
                    tp = ease_out(prog(t, self.start, 0.4))
                    tape(c, lerp(-80, 70, tp), -2, t)
                    tape(c, lerp(H + 80, H - 70, tp), 2, t)
                self._layout(c, t)

    def _layout(self, c, t):
        gap = 26
        if self.layout == "side":
            ic, rest = self.els[0], self.els[1:]
            cy = H / 2 - (70 if self.captions else 0)
            ic.draw(c, W * 0.29, cy - ic.h / 2, t, "center")
            tot = sum(e.h for e in rest) + gap * (len(rest) - 1)
            y = cy - tot / 2
            x = W * 0.45
            for e in rest:
                e.draw(c, x, y, t, "left", max_w=W - x - 120)
                y += e.h + gap
            return
        tot = sum(e.h for e in self.els) + gap * (len(self.els) - 1)
        y = H / 2 - tot / 2 + 10 - (70 if self.captions else 0)
        for e in self.els:
            e.draw(c, W / 2, y, t, "center")
            y += e.h + gap


def B(start, *els, layout="stack", tape=False):
    BEATS.append(Beat(start, list(els), layout, tape=tape))


def tape(c, y, ang, t, h=64):
    """Yellow/black caution tape across the frame."""
    with xf(c, W / 2, y, rot=ang):
        rr(c, -W, -h / 2, 2 * W, h, 0, "#F5C518")
        c.save()
        c.clipRect(skia.Rect.MakeLTRB(-W, -h / 2 + 6, W, h / 2 - 6))
        off = (t * 40) % 120
        for k in range(-20, 21):
            x0 = k * 120 + off
            c.drawPath(path([(x0, -h), (x0 + 55, -h), (x0 + 55 - h * 1.6, h), (x0 - h * 1.6, h)]), P("#111111"))
        c.restore()


def CH(start, num, name, sub):
    """Chapter card: red diagonal panel with #N on cream, caution tape at the bottom."""
    def fn(c, x, y, t, s0=start):
        p = ease_out(prog(t, s0, 0.35))
        c.save()
        c.translate(x - W / 2, y - (H / 2 - 160))
        c.drawRect(skia.Rect.MakeWH(W, H), P(CREAM, a=p))
        sl = ease_out(prog(t, s0, 0.45))
        c.drawPath(path([(0, 0), (lerp(-700, 700, sl), 0), (lerp(-700, 560, sl), H), (0, H)]), P("#E23B2E", a=p))
        k = back_out(prog(t, s0 + 0.15, 0.5))
        with xf(c, 330 * min(1, sl * 1.2), H / 2 + 120, s=lerp(0.5, 1, k), alpha=clamp(k)):
            draw_text(c, f"#{num}", 0, 0, 340, "#FFFFFF", "Black", 1.0, "center")
        # name (wrap to 2 lines)
        words = name.upper().split()
        if text_w(name.upper(), 120) > 1060 and len(words) > 1:
            k = min(range(1, len(words)), key=lambda j: abs(text_w(" ".join(words[:j]), 120)
                                                              - text_w(" ".join(words[j:]), 120)))
            lines = [" ".join(words[:k]), " ".join(words[k:])]
        else:
            lines = [name.upper()]
        y0 = H / 2 - 40 - (len(lines) - 1) * 70
        for i, ln in enumerate(lines):
            pp = ease_out(prog(t, s0 + 0.3 + i * 0.12, 0.4))
            draw_text(c, ln, 780 + (1 - pp) * 80, y0 + i * 140, 120, "#1A1414" if i < len(lines) - 1 else "#D93125",
                      "Black", pp)
        pp = ease_out(prog(t, s0 + 0.6, 0.4))
        sw = text_w(sub.upper(), 34, "ExtraBold") + 44
        rr(c, 782, y0 + (len(lines) - 1) * 140 + 40, sw, 56, 28, "#1A1414", pp)
        draw_text(c, sub.upper(), 782 + sw / 2, y0 + (len(lines) - 1) * 140 + 80, 34, "#FFFFFF", "ExtraBold", pp, "center")
        tape(c, H - 70, -2.5, t)
        c.restore()
    BEATS.append(Beat(start, [G(fn, 320, start)]))
    CHAPTERS.append((start, num, name))


def finalize(total):
    BEATS.sort(key=lambda b: b.start)
    for a, b in zip(BEATS, BEATS[1:]):
        a.end = b.start
    BEATS[-1].end = total + 1
    for b in BEATS:
        if b.end - b.start < 0.6:
            print("WARNING short beat at", b.start, b.end)
    CHAPTERS.sort()
    gap = 26
    for b in BEATS:
        if b.tape or (len(b.els) == 1 and isinstance(b.els[0], G) and b.els[0].h == 320):
            b.captions = False
            continue
        if b.layout == "side":
            rest = b.els[1:]
            tot = max(b.els[0].h, sum(e.h for e in rest) + gap * (len(rest) - 1))
        else:
            tot = sum(e.h for e in b.els) + gap * (len(b.els) - 1)
        b.captions = H / 2 + tot / 2 - 60 < H - 185


_bstarts = []


def chapter_tag(c, t):
    i = bisect.bisect_right([s for s, _, _ in CHAPTERS], t) - 1
    if i < 0:
        return
    s0, num, name = CHAPTERS[i]
    p = ease_out(prog(t, s0 + 2.2, 0.6))
    if p <= 0:
        return
    nxt = CHAPTERS[i + 1][0] if i + 1 < len(CHAPTERS) else 1e9
    p *= 1 - ease_out(prog(t, nxt - 0.3, 0.3))
    rr(c, 72, 64, 64, 44, 8, "#E23B2E", p)
    draw_text(c, f"{num:02d}", 104, 98, 28, "#FFFFFF", "Black", p, "center")
    draw_text(c, name.replace("*", "").replace("^", "").upper(), 152, 97, 28, MUTED, "Bold", p)


def render_frame(c, t):
    background(c)
    starts = _bstarts or _bstarts.extend(b.start for b in BEATS) or _bstarts
    i = bisect.bisect_right(starts, t) - 1
    if i >= 0:
        BEATS[i].draw(c, t)
    if i >= 0 and BEATS[i].captions:
        captions(c, t, BEATS[i])
    else:
        chapter_tag(c, t)


# ------------------------------------------------------------- captions
FIXW = {"samson": "Samsung", "samsong": "Samsung", "teck": "tech", "irish": "iris", "bones": "phones",
        "lunch": "launch", "whirled": "world", "plain": "plane", "bandit": "banned", "band": "banned",
        "litheamion": "lithium-ion", "lythium": "lithium", "eyephone": "iPhone", "righting": "riding",
        "bann": "banned", "nsylvania": "Pennsylvania", "linovo": "Lenovo", "dull": "Dell", "shored": "short",
        "censer": "sensor", "googall": "Google", "vitio": "video", "betting": "bedding", "pellaton": "Peloton",
        "pelaton": "Peloton", "pelatons": "Peloton's", "pellan": "Peloton", "sails": "sales", "cord": "court",
        "hustledan": "Heselden", "asseldon": "Heselden", "saguay": "Segway", "sagua": "Segway",
        "schooner": "scooter", "hiped": "hyped", "writing": "riding", "anchor": "Anker", "intact": "in tech",
        "sell": "cell", "jimmy": "Jimi", "seyo": "CEO", "eux": "CEO"}
_CHUNKS = []


def _build_chunks():
    seg_words = []
    for seg in json.load(open(os.path.join(HERE, "transcript.json"))):
        for w in seg["words"]:
            seg_words.append(w)
    cur = []
    for i, w in enumerate(seg_words):
        cur.append(w)
        nxt = seg_words[i + 1] if i + 1 < len(seg_words) else None
        brk = len(cur) >= 3 or w["w"][-1:] in ".,?!" or (nxt and nxt["s"] - w["e"] > 0.35) or not nxt
        if brk:
            end = (nxt["s"] if nxt and nxt["s"] - w["e"] < 0.6 else w["e"] + 0.25)
            _CHUNKS.append((cur[0]["s"], end, cur))
            cur = []


def captions(c, t, beat):
    if not _CHUNKS:
        _build_chunks()
    i = bisect.bisect_right([a for a, _, _ in _CHUNKS], t) - 1
    if i < 0:
        return
    s0, e0, words = _CHUNKS[i]
    if t > e0 or s0 < beat.start - 0.05:
        return
    size = 76
    f = font(size, "Black")
    toks = []
    for w in words:
        key = re.sub(r"[^a-z']", "", w["w"].lower())
        txt = FIXW.get(key, re.sub(r"[.,?!]", "", w["w"]))
        toks.append((txt.upper(), w["s"]))
    sp = f.measureText(" ")
    ws = [f.measureText(x) for x, _ in toks]
    x = W / 2 - (sum(ws) + sp * (len(ws) - 1)) / 2
    y = H - 110
    pop = back_out(prog(t, s0, 0.18))
    with xf(c, W / 2, y, s=lerp(0.85, 1, pop)):
        with xf(c, -W / 2, -y):
            for (txt, ws_), w_ in zip(toks, ws):
                col = ACC if ws_ <= t else "#FFFFFF"
                stroke = P("#000000", 12)
                c.drawString(txt, x, y, f, stroke)
                c.drawString(txt, x, y, f, P(col))
                x += w_ + sp
