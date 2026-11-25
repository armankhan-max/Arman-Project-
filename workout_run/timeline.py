"""Choreography for the ~16 minute POV cardio warm-up run.

Everything is locked to a 128 BPM grid, so every move cue, obstacle, coin chime and
music hit lands on the beat. Writes web/timeline.json, which is read by the renderer
(web/main.js) and the soundtrack generator (music.py).

Levels
  1 city      3 lanes   easy jog: jump / duck / side-step
  2 tunnel    3 lanes   + oncoming trains to dodge, high-knee sprints
  3 sky rail  train roofs high above the city: gap jumps, step-up jumps, roof-to-roof hops
  4 temple    single stone causeway: gaps, fire, spikes, blades, sharp left/right turns
  5 lava      3 lanes   fastest, everything + three sprint bursts, finish line
Rest breaks with guided stretches sit between the levels.
"""
import json
import math
import os
import random
from collections import Counter

BPM = 128
BEAT = 60 / BPM
BAR = 4 * BEAT
FPS = 30
LANE_X = [-2.6, 0.0, 2.6]
SAMPLE_HZ = 60
JUMP_T, JUMP_H = 0.75, 1.35
DUCK_IN, DUCK_HOLD, DUCK_OUT, DUCK_D = 0.14, 0.55, 0.28, -0.82
LANE_T = 0.4
CAR = 14.6
ROOF = 3.69
ROOF_TALL = 5.25
LVL_BARS = 80
REST_BARS = 20

LEVELS = [
    dict(kind="lanes", world=0, speed=10.5, gap=8, moves=["jump", "duck", "left", "right"], seed=3,
         sprints=[(56, 61)], oncoming=False),
    dict(kind="lanes", world=1, speed=13.0, gap=6, moves=["jump", "duck", "left", "right", "jump2"], seed=7,
         sprints=[(28, 34), (60, 66)], oncoming=True),
    dict(kind="skyrail", world=2, speed=13.5, gap=6, moves=["jump", "duck", "left", "right"], seed=19,
         sprints=[(30, 36), (62, 68)]),
    dict(kind="temple", world=3, speed=13.0, gap=5, moves=["jump", "duck", "turnL", "turnR"], seed=23,
         sprints=[(26, 32), (58, 64)]),
    dict(kind="lanes", world=4, speed=16.0, gap=4, moves=["jump", "duck", "left", "right", "jump2"], seed=11,
         sprints=[(20, 28), (44, 52), (66, 74)], oncoming=True),
]
REST_STRETCHES = [
    ["side_reach", "arm_circles"],
    ["lunge_twist", "quad"],
    ["hamstring", "side_reach"],
    ["arm_circles", "lunge_twist"],
]
COOLDOWN = ["quad", "hamstring"]


def build_sections():
    secs = []
    b = 0

    def add(name, kind, bars, world=None, extra=None):
        nonlocal b
        d = dict(name=name, kind=kind, t0=b * BAR, t1=(b + bars) * BAR, world=world)
        if extra:
            d.update(extra)
        secs.append(d)
        b += bars

    add("intro", "intro", 6)
    for i in range(5):
        add(f"card{i + 1}", "card", 2, i)
        add(f"lvl{i + 1}", "level", LVL_BARS, i)
        if i < 4:
            add(f"rest{i + 1}", "rest", REST_BARS, i, dict(stretches=REST_STRETCHES[i]))
    add("finish", "finish", 4, 4)
    add("cooldown", "rest", 16, 4, dict(stretches=COOLDOWN, cooldown=True))
    add("outro", "outro", 3)
    return secs, b


SECTIONS, TOTAL_BARS = build_sections()
DURATION = TOTAL_BARS * BAR


def sec(name):
    for s in SECTIONS:
        if s["name"] == name:
            return s
    raise KeyError(name)


def smooth(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


def jump_arc(u):
    return JUMP_H * 4 * u * (1 - u) if 0 < u < 1 else 0.0


def duck_off(u):
    if 0 <= u < DUCK_IN:
        return DUCK_D * smooth(u / DUCK_IN)
    if DUCK_IN <= u < DUCK_IN + DUCK_HOLD:
        return DUCK_D
    if DUCK_IN + DUCK_HOLD <= u < DUCK_IN + DUCK_HOLD + DUCK_OUT:
        return DUCK_D * (1 - smooth((u - DUCK_IN - DUCK_HOLD) / DUCK_OUT))
    return 0.0


def dirv(a):
    """Heading angle -> unit direction in x/z. a = 0 runs towards -z, positive a turns left (-x)."""
    return (-math.sin(a), -math.cos(a))


# ---------------------------------------------------------------------------------------------
class Level:
    """Shared machinery: beat-grid events, speed profile, distance table, coins."""

    def __init__(self, li):
        self.li = li
        self.cfg = LEVELS[li]
        self.rnd = random.Random(self.cfg["seed"])
        lv = sec(f"lvl{li + 1}")
        self.T0 = lv["t0"]
        self.Tlen = lv["t1"] - lv["t0"]
        self.pre = 2 * BAR + 0.5
        self.T_END = (sec("finish")["t1"] - self.T0 + 0.6) if li == 4 else self.Tlen + 1.3
        self.v = self.cfg["speed"]
        self.dt = 1 / SAMPLE_HZ
        self.n = int(math.ceil((self.T_END + self.pre) / self.dt)) + 1
        self.ts = [-self.pre + i * self.dt for i in range(self.n)]
        self.sprints = [(a * 4 * BEAT, b * 4 * BEAT) for a, b in self.cfg["sprints"]]

    def pick(self, choices):
        """Random move, biased towards the moves used least so far (keeps the workout balanced)."""
        if not hasattr(self, "_used"):
            self._used = Counter()
        w = [1.0 / (1 + self._used[c.replace("right", "left").replace("turnR", "turnL")]) ** 2 for c in choices]
        m = self.rnd.choices(choices, weights=w)[0]
        self._used[m.replace("right", "left").replace("turnR", "turnL")] += 1
        return m

    def idx(self, t):
        return max(0, min(self.n - 1, int(round((t + self.pre) / self.dt))))

    def in_sprint_zone(self, t, before=2 * BAR, after=BAR):
        return any(a - before <= t < b + after for a, b in self.sprints)

    def beat_slots(self):
        """Candidate action times (level-local seconds) on the beat grid."""
        b = 3 * 4
        n_beats = int(round(self.Tlen / BEAT))
        out = []
        while b < n_beats - 2 * 4:
            t = b * BEAT
            if self.in_sprint_zone(t):
                b += 1
                continue
            out.append(t)
            b += self.cfg["gap"]
        return out

    def speed_at(self, t):
        s = self.v
        for a, b in self.sprints:
            k = smooth((t - a) / 0.6) * (1 - smooth((t - b) / 0.8))
            s *= 1 + 0.33 * k
        if self.li == 4:
            tf = sec("finish")["t0"] - self.T0 + BEAT
            k = smooth((t - tf - 0.4) / 3.2)
            s *= 1 - k
        return s

    def sprint_at(self, t):
        k = 0.0
        for a, b in self.sprints:
            k = max(k, smooth((t - a) / 0.6) * (1 - smooth((t - b) / 0.8)))
        return k

    def build_distance(self):
        S = []
        acc = -self.v * self.pre
        for t in self.ts:
            S.append(acc)
            acc += self.speed_at(t + self.dt / 2) * self.dt
        self.S = S

    def s_at(self, t):
        i = (t + self.pre) / self.dt
        i0 = max(0, min(self.n - 2, int(i)))
        f = i - i0
        return self.S[i0] * (1 - f) + self.S[i0 + 1] * f

    def sprint_events(self):
        return [dict(t=a, move="sprint", t_end=b) for a, b in self.sprints]

    def make_coins(self, pos_at):
        coins = []
        t = 1.2
        end = self.Tlen - 1.0 if self.li != 4 else sec("finish")["t0"] - self.T0
        while t < end:
            run_len = self.rnd.choice([6, 8, 10, 12])
            k = 0
            tc = t
            while k < run_len and tc < end:
                p = pos_at(tc)
                coins.append(dict(x=round(p[0], 3), y=round(p[1], 3), z=round(p[2], 3), t=round(tc + self.T0, 3)))
                tc += 2.6 / self.speed_at(tc)
                k += 1
            t = tc + self.rnd.uniform(0.6, 1.8)
        return coins

    def track_dict(self, X, Y, Z, A, R):
        return dict(t0=round(-self.pre, 4), dt=self.dt,
                    s=[round(a, 3) for a in self.S],
                    px=[round(a, 3) for a in X], py=[round(a, 3) for a in Y], pz=[round(a, 3) for a in Z],
                    yaw=[round(a, 5) for a in A], roll=[round(a, 4) for a in R],
                    sprint=[round(self.sprint_at(t), 3) for t in self.ts])

    def export(self, extra):
        d = dict(index=self.li, kind=self.cfg["kind"], world=self.cfg["world"], t0=self.T0, speed=self.v,
                 events=self.events, coins=self.coins, length=self.S[-1])
        for e in d["events"]:
            e["t_abs"] = round(e["t"] + self.T0, 4)
            e["t"] = round(e["t"], 4)
            if "t_end" in e:
                e["t_end_abs"] = round(e["t_end"] + self.T0, 4)
                e["t_end"] = round(e["t_end"], 4)
        d.update(extra)
        return d


def lane_roll(e, t):
    u = (t - e["t"]) / LANE_T
    if 0 <= u <= 1.3:
        return (1 if e["move"] == "left" else -1) * 0.07 * math.sin(math.pi * min(u / 1.3, 1))
    return 0.0


# ---------------------------------------------------------------------------------------------
class LaneLevel(Level):
    def build(self):
        rnd = self.rnd
        self.build_distance()
        events = []
        lane = 1
        last = None
        trains = []

        def train_lo(o, t):
            return o["s"] - o["speed"] * (t - o["t_meet"])

        def lane_clear(ln, t0, t1):
            for o in trains:
                if o["lane"] != ln:
                    continue
                t = t0
                while t <= t1:
                    lo = train_lo(o, t)
                    if lo - 4 < self.s_at(t) < lo + o["cars"] * CAR + 4:
                        return False
                    t += 0.05
            return True

        for t_e in self.beat_slots():
            choices = list(self.cfg["moves"])
            if lane == 0:
                choices.remove("left")
            if lane == 2:
                choices.remove("right")
            for m in ("left", "right"):
                if m in choices:
                    nl = lane - 1 if m == "left" else lane + 1
                    if not lane_clear(nl, t_e - 0.1, t_e + 1.4):
                        choices.remove(m)
            if last in choices and len(choices) > 2:
                choices.remove(last)
            m = self.pick(choices)
            ev = dict(t=t_e, move=m, lane_from=lane)
            if m in ("left", "right"):
                nl = lane - 1 if m == "left" else lane + 1
                oncoming = bool(self.cfg.get("oncoming")) and rnd.random() < 0.6
                if oncoming:
                    t_meet = t_e + 0.72
                    o = dict(lane=lane, s=self.s_at(t_meet), cars=3, speed=18.0, t_meet=t_meet, scheme=rnd.randrange(4))
                else:
                    o = dict(lane=lane, s=self.s_at(t_e + 0.62), cars=3, speed=0.0, t_meet=0.0, scheme=rnd.randrange(4))
                trains.append(o)
                ev["oncoming"] = oncoming
                lane = nl
            ev["lane_to"] = lane
            events.append(ev)
            last = m
        events = events + self.sprint_events()
        events.sort(key=lambda e: e["t"])
        self.events = events

        X, Y, R = [], [], []
        lane_ev = [e for e in events if e["move"] in ("left", "right")]
        for t in self.ts:
            x = LANE_X[1]
            r = 0.0
            for e in lane_ev:
                x += (LANE_X[e["lane_to"]] - LANE_X[e["lane_from"]]) * smooth((t - e["t"]) / LANE_T)
                r += lane_roll(e, t)
            y = 0.0
            for e in events:
                if e["move"] in ("jump", "jump2"):
                    y += jump_arc((t - e["t"]) / JUMP_T)
                    if e["move"] == "jump2":
                        y += jump_arc((t - e["t"] - 2 * BEAT) / JUMP_T)
                elif e["move"] == "duck":
                    y += duck_off(t - e["t"])
            X.append(x)
            Y.append(y)
            R.append(r)

        obstacles = []
        occupied = []
        for e in events:
            m, te = e["move"], e["t"]
            if m in ("jump", "jump2"):
                for k in ([0] if m == "jump" else [0, 2 * BEAT]):
                    s = self.s_at(te + k + JUMP_T / 2)
                    typ = rnd.choice(["low", "low_spike", "low_elec"]) if self.li > 0 else rnd.choice(["low", "low", "low_spike"])
                    obstacles.append(dict(type=typ, lane=e["lane_from"], s=round(s, 3)))
                    occupied.append((e["lane_from"], s - 1.5, s + 1.5))
            elif m == "duck":
                s = self.s_at(te + DUCK_IN + DUCK_HOLD * 0.55)
                typ = rnd.choice(["high", "high_saw"]) if self.li > 0 else "high"
                obstacles.append(dict(type=typ, lane=e["lane_from"], s=round(s, 3)))
                occupied.append((e["lane_from"], s - 1.5, s + 1.5))

        def cam_in_lane(ln, s0, s1):
            for i, s in enumerate(self.S):
                if s0 - 3 <= s <= s1 + 3 and abs(X[i] - LANE_X[ln]) < 1.9:
                    return True
            return False

        def free(ln, a, b):
            if any(o[0] == ln and o[1] < b and a < o[2] for o in occupied):
                return False
            for o in trains:
                if o["lane"] != ln:
                    continue
                if o["speed"] == 0:
                    lo, hi = o["s"] - 4, o["s"] + o["cars"] * CAR + 4
                else:
                    lo, hi = o["s"] - 80, o["s"] + o["speed"] * 12 + o["cars"] * CAR
                if lo < b and a < hi:
                    return False
            return True

        # oncoming trains thundering past in a free lane (decoration)
        t_try = 5.0
        while t_try < self.Tlen - 6:
            ln_cam = min(range(3), key=lambda l: abs(X[self.idx(t_try)] - LANE_X[l]))
            for ln in rnd.sample([0, 1, 2], 3):
                if ln == ln_cam:
                    continue
                u = 20.0
                o = dict(lane=ln, s=self.s_at(t_try), cars=3, speed=u, t_meet=t_try, scheme=rnd.randrange(4))
                ok = True
                t = t_try - 5.0
                while t < t_try + 4.0:
                    lo = o["s"] - u * (t - t_try)
                    if lo - 3 < self.s_at(t) < lo + 3 * CAR + 3 and abs(X[self.idx(t)] - LANE_X[ln]) < 2.2:
                        ok = False
                        break
                    t += 0.05
                if ok and free(ln, o["s"] - 80, o["s"] + u * 12 + 3 * CAR):
                    trains.append(o)
                    break
            t_try += rnd.uniform(7, 12)

        s = 25.0
        while s < self.S[-1] - 20:
            ln = rnd.randrange(3)
            kind = rnd.random()
            if kind < 0.5:
                cars = rnd.choice([2, 3, 4])
                length = cars * CAR
                if not cam_in_lane(ln, s, s + length) and free(ln, s - 4, s + length + 4):
                    trains.append(dict(lane=ln, s=s, cars=cars, speed=0.0, t_meet=0.0, scheme=rnd.randrange(4)))
                    s += length * 0.5
            else:
                typ = rnd.choice(["low", "high", "low_spike", "high_saw", "low_elec"] if self.li > 0 else ["low", "high"])
                if not cam_in_lane(ln, s - 2, s + 2) and free(ln, s - 3, s + 3):
                    obstacles.append(dict(type=typ, lane=ln, s=round(s, 3)))
                    occupied.append((ln, s - 3, s + 3))
            s += rnd.uniform(12, 26)

        for o in trains:
            o["type"] = "train"
            o["s"] = round(o["s"], 3)
            o["t_meet"] = round(o["t_meet"], 4)
            o["len"] = round(o["cars"] * CAR, 3)
            obstacles.append(o)
        passes = sorted(round(o["t_meet"] + self.T0, 3) for o in trains if o["speed"] > 0)

        def pos_at(t):
            i = self.idx(t)
            return (X[i], 0.9 + max(Y[i] * 0.95, -0.35), -(self.S[i] + 0.8))

        self.coins = self.make_coins(pos_at)
        Z = [-s for s in self.S]
        return self.export(dict(track=self.track_dict(X, Y, Z, [0.0] * self.n, R), obstacles=obstacles, passes=passes))


# ---------------------------------------------------------------------------------------------
class SkyRail(Level):
    """Run on the roofs of parked trains on a viaduct high above the city."""

    def build(self):
        rnd = self.rnd
        self.build_distance()
        lane, h = 1, ROOF
        seg_start = self.S[0] - 40
        platforms = []  # (lane, s0, s1, h)
        events = []
        lane_last_end = {0: -1e9, 1: -1e9, 2: -1e9}
        bridges = []
        last = None
        for t_e in self.beat_slots():
            choices = list(self.cfg["moves"])
            if lane == 0:
                choices.remove("left")
            if lane == 2:
                choices.remove("right")
            if h != ROOF:
                choices = [c for c in choices if c != "duck"]
            for m in ("left", "right"):
                if m in choices:
                    nl = lane - 1 if m == "left" else lane + 1
                    if lane_last_end[nl] > self.s_at(t_e) - 50:
                        choices.remove(m)
            if last in choices and len(choices) > 2:
                choices.remove(last)
            m = self.pick(choices)
            ev = dict(t=t_e, move=m, lane_from=lane, h_from=h)
            if m == "jump":
                g0 = self.s_at(t_e + 0.14)
                g1 = self.s_at(t_e + JUMP_T - 0.12)
                platforms.append((lane, seg_start, g0, h))
                lane_last_end[lane] = g0
                r = rnd.random()
                if h == ROOF:
                    nh = ROOF_TALL if r < 0.45 else ROOF
                else:
                    nh = ROOF if r < 0.65 else ROOF_TALL
                seg_start, h = g1, nh
                ev["gap"] = [round(g0, 3), round(g1, 3)]
            elif m == "duck":
                bridges.append(round(self.s_at(t_e + DUCK_IN + DUCK_HOLD * 0.55), 3))
            else:
                nl = lane - 1 if m == "left" else lane + 1
                end = self.s_at(t_e + 0.62)
                platforms.append((lane, seg_start, end, h))
                lane_last_end[lane] = end
                seg_start = max(self.s_at(t_e) - rnd.uniform(25, 60), lane_last_end[nl] + 8)
                lane = nl
            ev["lane_to"] = lane
            ev["h_to"] = h
            events.append(ev)
            last = m
        platforms.append((lane, seg_start, self.S[-1] + 150, h))
        events = events + self.sprint_events()
        events.sort(key=lambda e: e["t"])
        self.events = events

        X, Y, R = [], [], []
        act = [e for e in events if e["move"] != "sprint"]
        for t in self.ts:
            x = LANE_X[1]
            base = ROOF
            off = 0.0
            r = 0.0
            for e in act:
                if e["move"] in ("left", "right"):
                    x += (LANE_X[e["lane_to"]] - LANE_X[e["lane_from"]]) * smooth((t - e["t"]) / LANE_T)
                    u = (t - e["t"]) / LANE_T
                    if 0 < u < 1:
                        off += 0.45 * 4 * u * (1 - u)
                    r += lane_roll(e, t)
                elif e["move"] == "jump":
                    u = (t - e["t"]) / JUMP_T
                    if t >= e["t"]:
                        base = e["h_from"] + (e["h_to"] - e["h_from"]) * smooth(u)
                    off += jump_arc(u)
                elif e["move"] == "duck":
                    off += duck_off(t - e["t"])
            X.append(x)
            Y.append(base + off)
            R.append(r)

        def pos_at(t):
            i = self.idx(t)
            return (X[i], Y[i] + 0.9, -(self.S[i] + 0.8))

        self.coins = self.make_coins(pos_at)

        deco = []
        occ = [(p[0], p[1], p[2]) for p in platforms]
        s = self.S[0] - 60
        while s < self.S[-1] + 120:
            ln = rnd.randrange(3)
            length = rnd.choice([2, 3, 4]) * CAR
            if all(not (o[0] == ln and o[1] - 6 < s + length and s < o[2] + 6) for o in occ):
                tall = rnd.random() < 0.3 and all(abs(b - (s + length / 2)) > length / 2 + 8 for b in bridges)
                deco.append((ln, s, s + length, ROOF_TALL if tall else ROOF))
                occ.append((ln, s, s + length))
            s += rnd.uniform(8, 22)
        obstacles = []
        for p in platforms + deco:
            ln, s0, s1, hh = p
            n = max(1, round((s1 - s0) / CAR))
            obstacles.append(dict(type="train", lane=ln, s=round(s0, 3), len=round(s1 - s0, 3), cars=n,
                                  tall=hh == ROOF_TALL, scheme=rnd.randrange(4), speed=0.0, t_meet=0.0))
        obstacles += [dict(type="bridge", s=b) for b in bridges]
        Z = [-s for s in self.S]
        return self.export(dict(track=self.track_dict(X, Y, Z, [0.0] * self.n, R), obstacles=obstacles, passes=[]))


# ---------------------------------------------------------------------------------------------
class Temple(Level):
    """A single stone causeway over an abyss with sharp 90 degree turns."""

    R_TURN = 3.0

    def build(self):
        rnd = self.rnd
        self.build_distance()
        events = []
        heading = 0
        last_corner_s = -1e9
        last = None
        corners = []
        hazards = []
        for t_e in self.beat_slots():
            s_e = self.s_at(t_e)
            choices = list(self.cfg["moves"])
            if heading == -1:
                choices.remove("turnL")
            if heading == 1:
                choices.remove("turnR")
            if s_e - last_corner_s < 34:
                choices = [c for c in choices if not c.startswith("turn")]
            if last in choices and len(choices) > 2:
                choices.remove(last)
            m = self.pick(choices)
            ev = dict(t=t_e, move=m)
            if m.startswith("turn"):
                d = -1 if m == "turnL" else 1
                sc = self.s_at(t_e + 0.2)
                corners.append((sc, d))
                heading += d
                last_corner_s = sc
                ev["s_corner"] = round(sc, 3)
            elif m == "jump":
                kind = rnd.choice(["gap", "gap", "fire", "spikes", "log"])
                if kind == "gap":
                    hazards.append(dict(type="gap", s0=round(self.s_at(t_e + 0.12), 3), s1=round(self.s_at(t_e + JUMP_T - 0.1), 3)))
                else:
                    hazards.append(dict(type=kind, s=round(self.s_at(t_e + JUMP_T / 2), 3)))
            elif m == "duck":
                kind = rnd.choice(["blade", "arch", "blade"])
                hazards.append(dict(type=kind, s=round(self.s_at(t_e + DUCK_IN + DUCK_HOLD * 0.55), 3)))
            events.append(ev)
            last = m
        self.events = events + self.sprint_events()
        self.events.sort(key=lambda e: e["t"])

        # path: straights joined by quarter-circle fillets
        r = self.R_TURN
        pieces = []
        ang = 0.0
        s_cur = self.S[0] - 80
        p = (0.0, -s_cur)  # s = 0 sits at the origin
        for sc, d in corners:
            s_line_end = sc - r * math.pi / 4
            dv = dirv(ang)
            L = s_line_end - s_cur
            pieces.append(dict(type="line", s0=s_cur, s1=s_line_end, x=p[0], z=p[1], a=ang))
            P = (p[0] + dv[0] * L, p[1] + dv[1] * L)
            left = (dv[1], -dv[0])
            perp = left if d == -1 else (-left[0], -left[1])
            C = (P[0] + perp[0] * r, P[1] + perp[1] * r)
            na = ang - d * math.pi / 2
            s_arc_end = s_line_end + r * math.pi / 2
            pieces.append(dict(type="arc", s0=s_line_end, s1=s_arc_end, cx=C[0], cz=C[1], r=r, a0=ang, a1=na, d=d,
                               px=perp[0], pz=perp[1], dx=dv[0], dz=dv[1]))
            p = (C[0] + dv[0] * r, C[1] + dv[1] * r)
            ang = na
            s_cur = s_arc_end
        pieces.append(dict(type="line", s0=s_cur, s1=self.S[-1] + 250, x=p[0], z=p[1], a=ang))

        def path(s):
            for pc in pieces:
                if s <= pc["s1"] or pc is pieces[-1]:
                    if pc["type"] == "line":
                        dv = dirv(pc["a"])
                        L = s - pc["s0"]
                        return pc["x"] + dv[0] * L, pc["z"] + dv[1] * L, pc["a"]
                    u = min(max((s - pc["s0"]) / (pc["s1"] - pc["s0"]), 0.0), 1.0)
                    th = u * math.pi / 2
                    x = pc["cx"] - pc["px"] * pc["r"] * math.cos(th) + pc["dx"] * pc["r"] * math.sin(th)
                    z = pc["cz"] - pc["pz"] * pc["r"] * math.cos(th) + pc["dz"] * pc["r"] * math.sin(th)
                    return x, z, pc["a0"] + (pc["a1"] - pc["a0"]) * u
            raise ValueError

        X, Z, A, Y, R = [], [], [], [], []
        for t, s in zip(self.ts, self.S):
            x, z, a = path(s)
            y = 0.0
            r_ = 0.0
            for e in self.events:
                if e["move"] == "jump":
                    y += jump_arc((t - e["t"]) / JUMP_T)
                elif e["move"] == "duck":
                    y += duck_off(t - e["t"])
                elif e["move"].startswith("turn"):
                    u = (t - e["t"]) / 0.7
                    if 0 <= u <= 1:
                        r_ += (1 if e["move"] == "turnL" else -1) * 0.09 * math.sin(math.pi * u)
            X.append(x)
            Z.append(z)
            A.append(a)
            Y.append(y)
            R.append(r_)

        def pos_at(t):
            i = self.idx(t)
            x, z, a = path(self.S[i] + 0.8)
            return (x, 0.9 + max(Y[i] * 0.95, -0.35), z)

        self.coins = self.make_coins(pos_at)
        obstacles = []
        for hz in hazards:
            o = dict(hz)
            sm = hz["s"] if "s" in hz else (hz["s0"] + hz["s1"]) / 2
            x, z, a = path(sm)
            o.update(x=round(x, 3), z=round(z, 3), a=round(a, 5))
            obstacles.append(o)
        for sc, d in corners:
            x, z, a = path(sc)
            obstacles.append(dict(type="corner", s=round(sc, 3), d=d, x=round(x, 3), z=round(z, 3), a=round(a, 5)))
        rp = [{k: (round(v, 4) if isinstance(v, float) else v) for k, v in pc.items()} for pc in pieces]
        return self.export(dict(track=self.track_dict(X, Y, Z, A, R), obstacles=obstacles, pieces=rp, passes=[]))


def main():
    levels = []
    for i, cfg in enumerate(LEVELS):
        cls = {"lanes": LaneLevel, "skyrail": SkyRail, "temple": Temple}[cfg["kind"]]
        levels.append(cls(i).build())
    out = dict(bpm=BPM, beat=BEAT, bar=BAR, fps=FPS, duration=DURATION, lane_x=LANE_X,
               sections=SECTIONS, levels=levels)
    f0 = sec("finish")["t0"]
    out["finish_cross"] = round(f0 + BEAT, 4)
    out["fireworks"] = [round(f0 + BEAT * k, 4) for k in [3, 4, 5, 5.5, 6, 7, 8, 9, 9.5, 10, 11, 12, 13]]
    out["stars"] = [round(f0 + BEAT * k, 4) for k in [2, 3, 4]]
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web", "timeline.json")
    with open(p, "w") as f:
        json.dump(out, f, separators=(",", ":"))
    for lv in out["levels"]:
        mv = [e["move"] for e in lv["events"]]
        print(f"level {lv['index'] + 1} ({lv['kind']}): {len(mv)} moves {dict(Counter(mv))}")
        print(f"   obstacles={len(lv['obstacles'])} coins={len(lv['coins'])} passes={len(lv['passes'])} length={lv['length']:.0f}m")
    print(f"duration {DURATION:.2f}s ({DURATION / 60:.1f} min), {os.path.getsize(p) / 1e6:.2f} MB")


if __name__ == "__main__":
    main()
