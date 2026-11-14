#!/usr/bin/env python3
"""Fast simple edit for parts 4-15: real footage with labels, the owner's images (Ken Burns),
navy text-animation cards. Then joins with the finished parts 1-3 and the full voiceover."""
import json, random, re, subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

G = Path("/home/user/Arman-Project-/gta-tatiana"); J = G / "voice-video"; F = G / "fast"
FONT = str(F / "Montserrat-XB.ttf"); FPS = 30
SEG = F / "seg"; SEG.mkdir(exist_ok=True)
words = json.load(open(J / "analysis/words.json"))
parts = json.load(open(J / "parts.json"))
T0 = parts[3]["start"]; TEND = parts[-1]["end"]
random.seed(7)

STOP = set("""a an the and or but if so to of in on at by for with from as is are was were be been it its it's this that
these those you your you're i i'll me my we our they them their he him his she her who what which when where why how
not no yes just only even also too very more most much many some any all every one can could will would should may might
do does did done have has had get got go going there here then than up down out over into about like make made know
let's let thing things way really because before after while until again still yet now first second third
""".split())

def clean(w):
    return re.sub(r"[^A-Za-z0-9$.%'+-]", "", w).strip(".'-")

# ---- shots: phrases of 1.2 to 3.2 s
ws = [w for w in words if w["s"] >= T0 - 0.05 and w["s"] < TEND]
shots, cur = [], []
for k, w in enumerate(ws):
    cur.append(w)
    dur = w["e"] - cur[0]["s"]
    nxt = ws[k + 1] if k + 1 < len(ws) else None
    gap = (nxt["s"] - w["e"]) if nxt else 9
    end_sent = w["w"].rstrip().endswith((".", "?", "!", ","))
    if nxt is None or (dur >= 1.2 and (end_sent or gap > 0.3)) or dur >= 3.0:
        shots.append(cur); cur = []
bounds = []
for i, s in enumerate(shots):
    a = T0 if i == 0 else bounds[-1][1]
    b = TEND if i == len(shots) - 1 else shots[i + 1][0]["s"]
    bounds.append((a, b, " ".join(w["w"] for w in s)))

def keywords(text, n=3):
    toks = [clean(t) for t in text.split()]
    toks = [t for t in toks if t]
    nums = [t for t in toks if re.search(r"\d|\$", t)]
    content = [t for t in toks if t.lower() not in STOP and len(t) > 2]
    pick = nums[:2] if nums else []
    for t in sorted(content, key=lambda x: -len(x)):
        if len(pick) >= n: break
        if t not in pick: pick.append(t)
    order = [t for t in toks if t in pick]
    seen, out = set(), []
    for t in order:
        if t.lower() not in seen: seen.add(t.lower()); out.append(t)
    return [o.upper() for o in out[:n]]

# ---- assets
lib = json.load(open(J / "footage/library/library.json"))
used = set()
for n in (1, 2, 3):
    p = J / f"parts/part{n:02d}/run/used-clips.txt"
    if p.exists(): used |= set(p.read_text().split())
pool = [k for k in lib if k not in used and (J / f"footage/library/{k}.mp4").exists()]
random.shuffle(pool)
IMGMAP = {4: ["img09", "img07", "img08"], 5: ["img10", "img11", "img13", "img12"], 6: ["img09", "img04"],
          7: ["img01", "img15"], 8: ["img14"], 9: ["img17", "img21", "img16", "img19"], 10: ["img18", "img22"],
          11: ["img23", "img03"], 12: ["img25", "img24"], 13: ["img19"], 14: ["img16", "img04"], 15: ["img25", "img03", "img01"]}

def part_of(t):
    for p in parts:
        if p["start"] <= t < p["end"]: return p["part"]
    return 15

# decide type per shot: images spread evenly in each part, otherwise footage/card pattern
types = ["F"] * len(bounds)
by_part = {}
for i, (a, b, _) in enumerate(bounds): by_part.setdefault(part_of(a), []).append(i)
img_for = {}
for p, idx in by_part.items():
    imgs = IMGMAP.get(p, [])
    for j, im in enumerate(imgs):
        k = idx[int((j + 0.5) * len(idx) / max(1, len(imgs)))]
        types[k] = "I"; img_for[k] = im
pattern = ["F", "F", "T", "F", "F", "T", "F", "T"]
c = 0
for i in range(len(types)):
    if types[i] == "I": continue
    types[i] = pattern[c % len(pattern)]; c += 1
    if any(ch.isdigit() or ch == "$" for ch in bounds[i][2]) and types[i] == "F": types[i] = "T"

def esc(s): return s.replace("\\", "\\\\").replace(":", "\\:").replace("'", "’").replace("%", "\\%")
LB = "drawbox=x=0:y=0:w=iw:h=60:color=black:t=fill,drawbox=x=0:y=ih-60:w=iw:h=60:color=black:t=fill"

def label_filters(kw, big=96, small=54, y0=None, center=False):
    if not kw: return ""
    line2 = kw[-1]; line1 = " ".join(kw[:-1])
    x = "(w-text_w)/2" if center else "110"
    yb = y0 if y0 is not None else "h-150-text_h"
    al = "if(lt(t,0.25),t/0.25,1)"
    sl = "(1-if(lt(t,0.25),t/0.25,1))*40"
    f = []
    if line1:
        f.append(f"drawtext=fontfile={FONT}:text='{esc(line1)}':fontsize={small}:fontcolor=white:x={x}:y='{yb}-{big+14}+{sl}':alpha='{al}':shadowcolor=black@0.6:shadowx=3:shadowy=3")
    f.append(f"drawtext=fontfile={FONT}:text='{esc(line2)}':fontsize={big}:fontcolor=0xe8574e:x={x}:y='{yb}+{sl}':alpha='{al}':shadowcolor=black@0.6:shadowx=3:shadowy=3")
    return "," + ",".join(f)

def nframes(a, b): return round((b - T0) * FPS) - round((a - T0) * FPS)

def render(i):
    a, b, text = bounds[i]; N = nframes(a, b); d = N / FPS; out = SEG / f"{i:04d}.mp4"
    if out.exists(): return
    kw = keywords(text)
    enc = ["-frames:v", str(N), "-r", "30", "-pix_fmt", "yuv420p", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-an", str(out)]
    if types[i] == "F":
        clip = clip_for[i]
        vf = (f"scale=2040:1148,crop=1920:1080:x='60*t/{d:.3f}':y=34,setpts=PTS-STARTPTS,fps=30,"
              f"tpad=stop_mode=clone:stop_duration=5,{LB}" + (label_filters(kw[-2:]) if i % 3 != 2 else ""))
        cmd = ["ffmpeg", "-v", "error", "-y", "-i", str(J / f"footage/library/{clip}.mp4"), "-vf", vf] + enc
    elif types[i] == "I":
        img = G / f"images/{img_for[i]}.jpg"
        vf = (f"scale=3840:2160,zoompan=z='1+0.10*on/{N}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={N}:s=1920x1080:fps=30,"
              f"{LB}" + label_filters(kw[-2:]))
        cmd = ["ffmpeg", "-v", "error", "-y", "-loop", "1", "-i", str(img), "-vf", vf] + enc
    else:
        vf = (f"scale=1920:1080,{LB}" + label_filters(kw, big=150, small=64, y0="h/2-20", center=True) +
              f",drawbox=x=(iw-360)/2:y=ih/2+170:w='360*min(t/0.4,1)':h=8:color=0xe8574e:t=fill")
        cmd = ["ffmpeg", "-v", "error", "-y", "-loop", "1", "-i", str(F / "navy.png"), "-vf", vf] + enc
    subprocess.run(cmd, check=True)

# footage assignment: a clip at least as long as the shot, else the longest left
clip_for = {}
for i, t in enumerate(types):
    if t != "F": continue
    need = (bounds[i][1] - bounds[i][0])
    pick = next((k for k in pool if lib[k]["dur"] >= need), None) or max(pool, key=lambda k: lib[k]["dur"])
    pool.remove(pick); clip_for[i] = pick
    if not pool:
        pool = [k for k in lib if (J / f"footage/library/{k}.mp4").exists()]; random.shuffle(pool)

if not (F / "navy.png").exists():
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=0x2e3c61:s=1920x1080:d=1", "-vf",
                    "vignette=angle=PI/3.2", "-frames:v", "1", str(F / "navy.png")], check=True)
json.dump({"shots": len(bounds), "types": "".join(types)}, open(F / "plan.json", "w"))
with ThreadPoolExecutor(4) as ex:
    import os; L = int(os.environ.get("LIMIT", len(bounds)))
    list(ex.map(render, range(min(L, len(bounds)))))
    if L < len(bounds): raise SystemExit("test")
with open(F / "list.txt", "w") as fl:
    for i in range(len(bounds)): fl.write(f"file '{SEG}/{i:04d}.mp4'\n")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(F / "list.txt"), "-c", "copy", str(F / "rest.mp4")], check=True)
print("rest done", len(bounds), "shots")
