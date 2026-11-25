#!/usr/bin/env python3
"""Text-animation toolkit (ASS/libass) for the grandma stock-footage video style.

Usage (done by make.py): set SPD, exec a project's text_cues.py with these helpers
in scope, then call save(). Cue times are written in ORIGINAL voiceover seconds
(as Whisper reports them); SPD rescales them to the slowed voice automatically.

Text markup: put [brackets] around words to colour them warm yellow.
"""
import json

SPD = 1.0          # voice speed factor (0.93 = 7% slower); set by make.py
SFX_TRIM_DB = -6   # global trim applied to every text-driven SFX

Y = "&H004DD3FF&"   # warm yellow
W = "&H00FFFFFF&"
R = "&H003539E5&"   # red
DARK = "&H00141414&"

HEAD = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Big,Anton,118,&H00FFFFFF,&H00FFFFFF,&H00101010,&H96000000,0,0,0,0,100,100,2,0,1,6,5,5,60,60,60,1
Style: Huge,Anton,190,&H004DD3FF,&H00FFFFFF,&H00101010,&H96000000,0,0,0,0,100,100,3,0,1,8,6,5,60,60,60,1
Style: Lower,Montserrat ExtraBold,66,&H00FFFFFF,&H00FFFFFF,&H64000000,&H00000000,0,0,0,0,100,100,0,0,3,18,0,1,110,110,90,1
Style: Tag,Montserrat ExtraBold,50,&H00141414,&H00FFFFFF,&H004DD3FF,&H00000000,0,0,0,0,100,100,2,0,3,14,0,7,110,110,110,1
Style: Item,Anton,132,&H00FFFFFF,&H00FFFFFF,&H00101010,&H96000000,0,0,0,0,100,100,2,0,1,6,5,7,110,110,190,1
Style: Info,Montserrat ExtraBold,66,&H00FFFFFF,&H00FFFFFF,&H00101010,&H96000000,0,0,0,0,100,100,0,0,1,4,3,7,118,110,330,1
Style: Panel,Montserrat ExtraBold,62,&H00FFFFFF,&H00FFFFFF,&H00101010,&H00000000,0,0,0,0,100,100,0,0,1,3,0,7,0,0,0,1
Style: Box,Montserrat ExtraBold,10,&H50000000,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1
Style: Btn,Montserrat ExtraBold,54,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,1,0,1,0,0,5,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

ev = []
sfx = []   # (time, name, gain_db)


def ts(t):
    t = max(0, t) / SPD
    h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def hl(text):
    # [word] -> yellow
    return text.replace("[", "{\\c" + Y + "}").replace("]", "{\\c" + W + "}")


def add(st, en, style, text, layer=1):
    ev.append(f"Dialogue: {layer},{ts(st)},{ts(en)},{style},,0,0,0,,{text}")


def big(st, en, text, y=540, style="Big", s=True):
    """Center pop-in with overshoot, fade out."""
    add(st, en, style, f"{{\\an5\\pos(960,{y})\\fad(0,220)\\fscx35\\fscy35\\alpha&HFF&"
        f"\\t(0,170,\\fscx112\\fscy112\\alpha&H00&)\\t(170,290,\\fscx100\\fscy100)}}" + hl(text), 3)
    if s:
        sfx.append((st, "pop", -15))


def words(st, en, text, y=540, gap=0.22, style="Big"):
    """Word-by-word reveal, centered."""
    ws = text.split(" ")
    out = ""
    for i, w in enumerate(ws):
        t0 = int(i * gap * 1000)
        out += f"{{\\alpha&HFF&\\t({t0},{t0+120},\\alpha&H00&)}}" + hl(w) + " "
    add(st, en, style, f"{{\\an5\\pos(960,{y})\\fad(0,220)}}" + out.strip(), 3)
    sfx.append((st, "pop", -17))


def lower(st, en, text):
    """Lower-third box sliding in from the left."""
    add(st, en, "Lower", f"{{\\an1\\move(-700,990,110,990,0,280)\\fad(0,250)}}" + hl(text), 4)
    sfx.append((st, "swoosh", -18))


def item(st, en, num, name, amount, label="ITEM"):
    """Item card: yellow ITEM tag + big name + amount, top-left."""
    add(st, en, "Tag", f"{{\\an7\\move(-500,110,110,110,0,250)\\fad(0,250)}}{label} #{num}", 5)
    add(st + 0.25, en, "Item", f"{{\\an7\\pos(110,190)\\fad(180,250)\\fscx60\\fscy60\\t(0,200,\\fscx104\\fscy104)\\t(200,300,\\fscx100\\fscy100)}}" + hl(name), 5)
    if amount:
        add(st + 0.6, en, "Info", f"{{\\an7\\move(118,400,118,370,0,250)\\fad(200,250)}}" + hl(amount), 5)
    sfx.append((st, "whoosh", -12))
    sfx.append((st + 0.25, "hit", -14))


def count(st, en, target, suffix="", y=540, prefix="", dur=1.0, style="Huge", label=None):
    """Count-up number, then hold."""
    steps = int(dur * 15)
    for k in range(steps):
        p = (k + 1) / steps
        v = target * (1 - (1 - p) ** 3)
        t0 = st + k * dur / steps
        add(t0, t0 + dur / steps + 0.01, style,
            f"{{\\an5\\pos(960,{y})}}{prefix}{int(round(v)):,}{suffix}", 3)
    add(st + dur, en, style, f"{{\\an5\\pos(960,{y})\\fad(0,250)\\t(0,120,\\fscx108\\fscy108)\\t(120,240,\\fscx100\\fscy100)}}{prefix}{target:,}{suffix}", 3)
    if label:
        add(st + 0.2, en, "Big", f"{{\\an5\\pos(960,{y+175})\\fad(250,250)\\fs70}}" + hl(label), 3)
    sfx.append((st, "tick", -16))
    sfx.append((st + dur, "ding", -15))


def panel(st, en, x, y, w, rows, gap, title=None):
    """Dark rounded panel with rows appearing one after another at given times."""
    h = 50 + len(rows) * 88 + (100 if title else 0)
    add(st, en, "Box", f"{{\\an7\\pos({x},{y})\\fad(250,250)\\p1}}m 0 0 l {w} 0 {w} {h} 0 {h}{{\\p0}}", 2)
    yy = y + 30
    if title:
        add(st, en, "Panel", f"{{\\an7\\pos({x+40},{yy})\\fad(250,250)\\c{Y}\\fs70}}{title}", 3)
        yy += 100
    for i, (t, txt) in enumerate(rows):
        add(t, en, "Panel", f"{{\\an7\\move({x-40},{yy},{x+40},{yy},0,220)\\fad(200,250)}}" + hl(txt), 3)
        sfx.append((t, "pop", -19))
        yy += 88


def warn(st, en, text, y=190):
    add(st, en, "Box", f"{{\\an7\\pos(0,{y-70})\\fad(200,250)\\1c{R}\\1a&H20&\\p1}}m 0 0 l 1920 0 1920 140 0 140{{\\p0}}", 2)
    add(st, en, "Big", f"{{\\an5\\pos(960,{y})\\fad(200,250)\\fs76}}" + text, 3)
    sfx.append((st, "alert", -14))


def subscribe(st, en, x=960, y=880):
    """Animated subscribe button + click."""
    w, h = 470, 110
    click = 1.4
    add(st, st + click, "Box", f"{{\\an7\\pos({x-w//2},{y-h//2})\\1c{R}\\1a&H00&\\fscx40\\fscy40\\t(0,200,\\fscx100\\fscy100)\\p1}}m 18 0 l {w-18} 0 b {w} 0 {w} 0 {w} 18 l {w} {h-18} b {w} {h} {w} {h} {w-18} {h} l 18 {h} b 0 {h} 0 {h} 0 {h-18} l 0 18 b 0 0 0 0 18 0{{\\p0}}", 6)
    add(st, st + click, "Btn", f"{{\\an5\\pos({x},{y})\\alpha&HFF&\\t(150,300,\\alpha&H00&)}}SUBSCRIBE", 7)
    add(st + click, en, "Box", f"{{\\an7\\pos({x-w//2},{y-h//2})\\1c&H00555555&\\fad(0,300)\\p1}}m 18 0 l {w-18} 0 b {w} 0 {w} 0 {w} 18 l {w} {h-18} b {w} {h} {w} {h} {w-18} {h} l 18 {h} b 0 {h} 0 {h} 0 {h-18} l 0 18 b 0 0 0 0 18 0{{\\p0}}", 6)
    add(st + click, en, "Btn", f"{{\\an5\\pos({x},{y})\\fad(0,300)}}SUBSCRIBED", 7)
    # cursor (arrow) moving in and clicking
    cur = "m 0 0 l 0 60 l 15 46 l 27 72 l 37 67 l 25 42 l 44 42 l 0 0"
    add(st + 0.5, st + click + 0.8, "Box", f"{{\\an7\\move({x+380},{y+200},{x+110},{y+5},0,800)\\1c&H00FFFFFF&\\3c&H00000000&\\bord3\\1a&H00&\\t(850,950,\\fscx85\\fscy85)\\t(950,1050,\\fscx100\\fscy100)\\fad(0,250)\\p1}}{cur}{{\\p0}}", 8)
    sfx.append((st, "swoosh", -16))
    sfx.append((st + click, "click", -8))
    sfx.append((st + click + 0.15, "bell", -12))




def reset():
    ev.clear(); sfx.clear()


def save(ass_path, sfx_json_path):
    open(ass_path, "w").write(HEAD + "\n".join(ev) + "\n")
    json.dump(sorted((a / SPD, n, g + SFX_TRIM_DB) for a, n, g in sfx), open(sfx_json_path, "w"))
    return len(ev), len(sfx)
