"""The automatic editor: camera moves, transitions, motion graphics, grading, sound mix -> one MP4."""
import os
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor

import store

FPS = 30
SIZES = {"16:9": (1920, 1080), "9:16": (1080, 1920), "1:1": (1080, 1080)}
PREVIEW = {"16:9": (1280, 720), "9:16": (720, 1280), "1:1": (720, 720)}
T = 0.5  # transition length in seconds
MOVES = ["push_in", "pan_right", "pull_out", "diag", "parallax", "pan_left", "tilt_up", "orbit"]


def run(cmd, cwd=None):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("ffmpeg failed: " + r.stderr[-700:])


def probe_duration(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                       capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def frames(d):
    return max(2, round(d * FPS))


# ---------------- one shot ----------------
def render_shot(asset, out, dur, w, h, grade, move, slowmo=False):
    """An image with a cinematic camera move, or a stock clip cropped to frame (optionally slow motion)."""
    n = frames(dur)
    enc = ["-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "17", "-pix_fmt", "yuv420p", "-r", str(FPS),
           "-frames:v", str(n), out]
    g = ("," + grade) if grade else ""
    if asset["type"] == "split":
        hw = w // 2 // 2 * 2
        bpath = asset["b"] if os.path.isabs(asset["b"]) else os.path.join(asset["root"], asset["b"])
        bin_ = ["-stream_loop", "-1", "-i", bpath] if asset.get("btype") == "video" else ["-loop", "1", "-i", bpath]
        fc = (f"[0]scale={hw}:{h}:force_original_aspect_ratio=increase,crop={hw}:{h},fps={FPS},tpad=stop_mode=clone:stop_duration=10,setsar=1[a];"
              f"[1]scale={int(hw * 1.12)}:{int(h * 1.12)}:force_original_aspect_ratio=increase,crop={int(hw * 1.12)}:{int(h * 1.12)},fps={FPS},"
              f"crop={hw}:{h}:x='(iw-ow)*t/{n / FPS:.3f}':y='(ih-oh)/2',setsar=1[b];"
              f"[a][b]hstack=inputs=2,pad={w}:{h}:(ow-iw)/2:0{g}")
        run(["ffmpeg", "-y", "-v", "error", "-ss", f"{float(asset.get('ss', 0)):.3f}", "-i", asset["path"]] + bin_
            + ["-filter_complex", fc] + enc)
        return
    if asset["type"] == "video":
        speed = "setpts=1.25*PTS," if slowmo else ""
        vf = f"{speed}scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},fps={FPS},setsar=1{g}"
        if asset.get("ss") is not None:  # a slice of the avatar's own recording, so lips stay in sync with the voice
            vf = vf.replace(f"fps={FPS}", f"fps={FPS},tpad=stop_mode=clone:stop_duration=10")
            run(["ffmpeg", "-y", "-v", "error", "-ss", f"{float(asset['ss']):.3f}", "-i", asset["path"], "-vf", vf] + enc)
            return
        run(["ffmpeg", "-y", "-v", "error", "-stream_loop", "-1", "-i", asset["path"], "-vf", vf] + enc)
        return
    D = n / FPS
    if move == "handheld":  # phone-on-the-table / candid iPhone feel for the host
        sw, sh = int(w * 1.1) // 2 * 2, int(h * 1.1) // 2 * 2
        vf = (f"scale={sw}:{sh}:force_original_aspect_ratio=increase,crop={sw}:{sh},fps={FPS},"
              f"crop={w}:{h}:x='(iw-ow)/2+{w * 0.012:.1f}*sin(2*PI*t*0.31)+{w * 0.004:.1f}*sin(2*PI*t*1.37)':"
              f"y='(ih-oh)/2+{h * 0.012:.1f}*sin(2*PI*t*0.23+1)+{h * 0.004:.1f}*sin(2*PI*t*1.71)',setsar=1{g}")
        run(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-i", asset["path"], "-vf", vf] + enc)
        return
    if move == "parallax":  # photo floating over its own blurred copy: depth of field + parallax drift
        fw, fh = int(w * 0.80) // 2 * 2, int(h * 0.80) // 2 * 2
        fc = (f"[0]scale={int(w * 1.25)}:{int(h * 1.25)}:force_original_aspect_ratio=increase,crop={int(w * 1.25)}:{int(h * 1.25)},"
              f"fps={FPS},crop={w}:{h}:x='(iw-ow)*t/{D:.3f}':y='(ih-oh)/2',gblur=sigma={w / 60:.0f},eq=brightness=-0.08[bg];"
              f"[0]scale={fw}:{fh}:force_original_aspect_ratio=increase,crop={fw}:{fh},fps={FPS},"
              f"pad={fw + 12}:{fh + 12}:6:6:white[fg];"
              f"[bg][fg]overlay=x='(W-w)/2+{w * 0.035:.0f}-{w * 0.07:.0f}*t/{D:.3f}':y='(H-h)/2',setsar=1{g}")
        run(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-i", asset["path"], "-filter_complex", fc] + enc)
        return
    # zoompan family on a 2x canvas for smooth sub-pixel motion
    bw, bh = w * 2, h * 2
    e = f"(on/{n})"
    ease = f"({e}*{e}*(3-2*{e}))"
    cx, cy = "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
    z = {"push_in": f"1+0.16*{ease}", "pull_out": f"1.16-0.16*{ease}", "pan_left": "1.15", "pan_right": "1.15",
         "tilt_up": "1.15", "diag": f"1.06+0.12*{ease}", "orbit": f"1.08+0.08*{ease}"}.get(move, f"1+0.14*{ease}")
    x = {"pan_left": f"(iw-iw/zoom)*(1-{ease})", "pan_right": f"(iw-iw/zoom)*{ease}",
         "diag": f"(iw-iw/zoom)*(0.25+0.5*{ease})"}.get(move, cx)
    y = {"tilt_up": f"(ih-ih/zoom)*(1-{ease})", "diag": f"(ih-ih/zoom)*(0.7-0.4*{ease})"}.get(move, cy)
    ow, oh = (int(w * 1.08) // 2 * 2, int(h * 1.08) // 2 * 2) if move == "orbit" else (w, h)
    vf = (f"scale={bw}:{bh}:force_original_aspect_ratio=increase,crop={bw}:{bh},"
          f"zoompan=z='{z}':x='{x}':y='{y}':d={n}:s={ow}x{oh}:fps={FPS}")
    if move == "orbit":  # slow rotation + push reads like an orbiting camera
        vf += f",rotate=a='-0.022+0.044*t/{D:.3f}',crop={w}:{h}"
    vf += f",setsar=1{g}"
    run(["ffmpeg", "-y", "-v", "error", "-i", asset["path"], "-vf", vf] + enc)


# ---------------- joining shots with transitions ----------------
def join(files, durs, trans, out, cwd):
    """files[i] lasts durs[i] seconds. trans[i] is the transition INTO shot i (None = hard cut).
    Shots before a transition were rendered T seconds longer, so the timeline length stays exact."""
    BATCH = 16
    groups, cur = [], [0]
    for i in range(1, len(files)):
        if len(cur) >= BATCH and not trans[i]:
            groups.append(cur)
            cur = []
        cur.append(i)
    groups.append(cur)
    parts = []
    for gi, g in enumerate(groups):
        if len(g) == 1:
            parts.append(files[g[0]])
            continue
        cmd = ["ffmpeg", "-y", "-v", "error"]
        for i in g:
            cmd += ["-i", files[i]]
        fc = [f"[{k}]fps={FPS},settb=1/{FPS},format=yuv420p[s{k}]" for k in range(len(g))]
        acc, acc_d = "s0", frames(durs[g[0]]) / FPS
        for k in range(1, len(g)):
            i = g[k]
            d = frames(durs[i]) / FPS
            o = f"j{k}"
            if trans[i]:
                fc.append(f"[{acc}][s{k}]xfade=transition={trans[i]}:duration={T}:offset={acc_d - T:.4f}[{o}]")
                acc_d += d - T
            else:
                fc.append(f"[{acc}][s{k}]concat=n=2:v=1:a=0,settb=1/{FPS}[{o}]")
                acc_d += d
            acc = o
        part = f"part{gi:03d}.mp4"
        run(cmd + ["-filter_complex", ";".join(fc), "-map", f"[{acc}]", "-c:v", "libx264", "-preset", "veryfast", "-crf", "17",
                   "-pix_fmt", "yuv420p", "-r", str(FPS), part], cwd=cwd)
        parts.append(part)
    with open(os.path.join(cwd, "parts.txt"), "w") as f:
        f.writelines(f"file '{p}'\n" for p in parts)
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", "parts.txt", "-c", "copy", out], cwd=cwd)


# ---------------- motion graphics + captions (ASS) ----------------
def _ass_color(hexcol):
    c = hexcol.lstrip("#")
    return f"&H00{c[4:6]}{c[2:4]}{c[0:2]}".upper()


def _ts(t):
    t = max(0, t)
    return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"


def _esc(s):
    return s.replace("\\", "").replace("{", "(").replace("}", ")").replace("\n", " ")


NUM = re.compile(r"(\d[\d,]*(?:\.\d+)?)")


def build_ass(path, scenes, w, h, style, captions, title=None, hindi=False, outro_at=None, total=None, credits=()):
    accent = _ass_color(style.get("accent", "#FFD400"))
    font = "FreeSans" if hindi else "Inter ExtraBold"
    upper = style.get("caption_upper") and not hindi
    land = w > h
    cs, ts = int(min(w, h) * (0.062 if land else 0.07)), int(min(w, h) * 0.105)
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {w}
PlayResY: {h}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,{font},{cs},&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,-1,0,0,0,100,100,0,0,1,{cs * 0.09:.1f},{cs * 0.04:.1f},2,{int(w * 0.08)},{int(w * 0.08)},{int(h * (0.09 if land else 0.2))},1
Style: Big,{font},{ts},&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,-1,0,0,0,100,100,0,0,1,{ts * 0.08:.1f},{ts * 0.05:.1f},5,{int(w * 0.06)},{int(w * 0.06)},0,1
Style: Tag,{font},{int(cs * 0.8)},&H00101010,&H00FFFFFF,{accent},{accent},-1,0,0,0,100,100,1,0,3,{cs * 0.22:.1f},0,7,{int(w * 0.05)},0,{int(h * 0.07)},1
Style: Small,{font},{int(cs * 0.55)},&H00DDDDDD,&H00FFFFFF,&H00000000,&H96000000,0,0,0,0,100,100,0,0,1,2,0,2,{int(w * 0.08)},{int(w * 0.08)},{int(h * 0.12)},1
Style: Box,{font},10,{accent},{accent},{accent},{accent},0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ev = []
    if title:
        ev.append(f"Dialogue: 2,{_ts(0.4)},{_ts(4.2)},Tag,,0,0,0,,{{\\fad(250,300)\\move({-int(w * 0.3)},{int(h * 0.07)},{int(w * 0.05)},{int(h * 0.07)},0,350)}}"
                  + _esc(title.upper() if not hindi else title))
    y_big = int(h * (0.3 if captions else 0.45))
    for k, sc in enumerate(scenes):
        s0, s1 = sc["start"], sc["start"] + sc["dur"]
        txt = (sc.get("text") or "").strip()
        if txt:
            a, b = s0 + 0.25, min(s1 - 0.1, s0 + 4.0)
            show = _esc(txt.upper() if not hindi else txt)
            m = NUM.search(show)
            if m:  # stat card: number counts up, accent bar slides in under it
                val = float(m.group(1).replace(",", ""))
                dec = len(m.group(1).split(".")[1]) if "." in m.group(1) else 0
                steps = 14
                for i in range(steps + 1):
                    v = val * (1 - (1 - i / steps) ** 3)
                    vs = f"{v:,.{dec}f}" if "," in m.group(1) else f"{v:.{dec}f}"
                    t0, t1 = a + i * 0.06, (a + (i + 1) * 0.06) if i < steps else b
                    shown = show[:m.start()] + f"{{\\c{accent}&}}{vs}{{\\c&HFFFFFF&}}" + show[m.end():]
                    fx = "\\fad(80,0)" if i == 0 else ""
                    if i == steps:
                        fx = "\\fad(0,220)\\t(0,120,\\fscx106\\fscy106)\\t(120,240,\\fscx100\\fscy100)"
                    ev.append(f"Dialogue: 1,{_ts(t0)},{_ts(t1)},Big,,0,0,0,,{{\\an5\\pos({w // 2},{y_big}){fx}}}" + shown)
                bw2, bh2 = int(w * 0.22), max(6, int(h * 0.012))
                ev.append(f"Dialogue: 0,{_ts(a + 0.1)},{_ts(b)},Box,,0,0,0,,{{\\an7\\pos({w // 2 - bw2 // 2},{y_big + int(ts * 0.62)})"
                          f"\\clip(0,0,{w // 2 - bw2 // 2},{h})\\t(0,500,\\clip(0,0,{w},{h}))\\fad(0,220)\\p1}}m 0 0 l {bw2} 0 {bw2} {bh2} 0 {bh2}{{\\p0}}")
            elif k % 2 == 0:  # big centre pop
                words = show.split()
                if len(words) > 1:
                    words[-1] = f"{{\\c{accent}&}}{words[-1]}"
                ev.append(f"Dialogue: 1,{_ts(a)},{_ts(b)},Big,,0,0,0,,{{\\an5\\pos({w // 2},{y_big})\\fad(80,220)\\fscx60\\fscy60"
                          f"\\t(0,180,\\fscx108\\fscy108)\\t(180,300,\\fscx100\\fscy100)}}" + " ".join(words))
            else:  # callout / lower-third style label that slides in from the left
                yy = int(h * 0.62) if not captions else int(h * 0.58)
                ev.append(f"Dialogue: 1,{_ts(a)},{_ts(b)},Tag,,0,0,0,,{{\\an4\\fs{int(cs * 1.05)}\\move({-int(w * 0.4)},{yy},{int(w * 0.06)},{yy},0,320)\\fad(0,220)}}▶ " + show)
        if not captions:
            continue
        chunk = []
        words = sc.get("words") or []
        for i, wd in enumerate(words):
            chunk.append(wd)
            joined = " ".join(x[2] for x in chunk)
            last = i == len(words) - 1
            pause = not last and words[i + 1][0] - wd[1] > 0.35
            if last or pause or len(chunk) >= 4 or len(joined) > 20 or wd[2][-1:] in ".?!,":
                for j, cw in enumerate(chunk):
                    a = s0 + cw[0]
                    b = s0 + (chunk[j + 1][0] if j + 1 < len(chunk) else min(cw[1] + 0.25, words[i + 1][0] if not last else cw[1] + 0.25))
                    parts = []
                    for m2, x in enumerate(chunk):
                        t = _esc(x[2].upper() if upper else x[2])
                        parts.append(f"{{\\c{accent}&}}{t}{{\\c&HFFFFFF&}}" if m2 == j else t)
                    popfx = "{\\fscx88\\fscy88\\t(0,90,\\fscx100\\fscy100)}" if j == 0 else ""
                    ev.append(f"Dialogue: 0,{_ts(a)},{_ts(b)},Cap,,0,0,0,,{popfx}" + " ".join(parts))
                chunk = []
    if outro_at is not None and total:
        end_txt = "धन्यवाद" if hindi else "THANKS FOR WATCHING"
        ev.append(f"Dialogue: 2,{_ts(outro_at + 0.2)},{_ts(total)},Big,,0,0,0,,{{\\an5\\pos({w // 2},{int(h * 0.42)})\\fad(300,500)"
                  f"\\fscx80\\fscy80\\t(0,400,\\fscx100\\fscy100)}}" + end_txt)
        ev.append(f"Dialogue: 2,{_ts(outro_at + 0.6)},{_ts(total)},Tag,,0,0,0,,{{\\an5\\pos({w // 2},{int(h * 0.56)})\\fad(300,500)}}"
                  + ("SUBSCRIBE FOR MORE" if not hindi else "और वीडियो के लिए सब्सक्राइब करें"))
        if credits:
            cr = "Footage & images: " + "  ·  ".join(_esc(c) for c in list(credits)[:6])
            ev.append(f"Dialogue: 2,{_ts(outro_at + 0.8)},{_ts(total)},Small,,0,0,0,,{{\\fad(300,500)}}" + cr[:220])
    with open(path, "w", encoding="utf-8") as f:
        f.write(head + "\n".join(ev) + "\n")


# ---------------- the whole edit ----------------
def render(p, shots, narration_wav, music_wav, sfx_wav, out, progress=lambda f: None, preview=False, grain=4):
    """shots: [{asset, dur, grade, move, trans, slowmo}] in order. trans = transition INTO the shot."""
    d = store.pdir(p["id"])
    w, h = (PREVIEW if preview else SIZES).get(p.get("aspect", "16:9"), SIZES["16:9"])
    sdir = os.path.join(d, "shots")
    os.makedirs(sdir, exist_ok=True)
    for f in os.listdir(sdir):
        os.remove(os.path.join(sdir, f))
    for f in os.listdir(d):
        if f.startswith("part") and f.endswith(".mp4"):
            os.remove(os.path.join(d, f))
    # a shot followed by a transition is rendered T longer (the overlap)
    rdur = [s["dur"] + (T if i + 1 < len(shots) and shots[i + 1].get("trans") else 0) for i, s in enumerate(shots)]
    done = [0]

    def one(i):
        s = shots[i]
        out_i = os.path.join(sdir, f"{i:04d}.mp4")
        try:
            render_shot(s["asset"], out_i, rdur[i], w, h, s["grade"], s.get("move", "push_in"), s.get("slowmo", False))
        except Exception:
            import media  # a broken download must never kill the whole video
            fb = media.procedural(os.path.join(sdir, f"fb{i}.jpg"), w, h, i)
            render_shot({"path": fb, "type": "image"}, out_i, rdur[i], w, h, s["grade"], "push_in")
        done[0] += 1
        progress(done[0] / len(shots) * 0.7)

    with ThreadPoolExecutor(max_workers=int(os.environ.get("RENDER_WORKERS") or max(1, min(4, (os.cpu_count() or 2) - 1)))) as ex:
        list(ex.map(one, range(len(shots))))
    join([f"shots/{i:04d}.mp4" for i in range(len(shots))], rdur, [s.get("trans") for s in shots], "joined.mp4", d)
    progress(0.82)

    total = sum(s["dur"] for s in shots)
    fonts = os.path.relpath(store.FONTS, d).replace("\\", "/")
    vf = (f"[0:v]ass=subs.ass:fontsdir={fonts}" + (f",noise=alls={grain}:allf=t" if grain else "")
          + f",fade=t=in:st=0:d=0.35,fade=t=out:st={max(0, total - 0.8):.2f}:d=0.8[v]")
    # voice chain: clean low rumble, tame "s" sounds, even out levels, add presence
    vo = ("[1:a]highpass=f=75,deesser=i=0.4,acompressor=threshold=-21dB:ratio=3:attack=6:release=120:makeup=2.5,"
          "equalizer=f=3200:t=q:w=1.2:g=2,equalizer=f=250:t=q:w=1:g=-1.5,"
          f"apad=whole_dur={total:.3f},atrim=0:{total:.3f}[vo]")
    fc = [vf, vo]
    mix = ["[vo1]"]
    n_in = 2
    inputs = ["-i", os.path.basename(narration_wav)]
    if music_wav or sfx_wav:
        fc[-1] = vo.replace("[vo]", "[vo0]")
        fc.append("[vo0]asplit=2[vo1][vkey]")
    else:
        fc[-1] = vo.replace("[vo]", "[vo1]")
    if music_wav:
        vol = float(store.get_settings().get("music_volume", 0.2))
        inputs += ["-i", os.path.basename(music_wav)]
        # music ducks under the narration and swells back in the pauses
        fc.append(f"[{n_in}:a]volume={vol * 2.2:.3f}[m0];[m0][vkey]sidechaincompress=threshold=0.03:ratio=7:attack=40:release=650[m]")
        mix.append("[m]")
        n_in += 1
    elif sfx_wav:
        fc[-1] = "[vo0]anull[vo1]"
    if sfx_wav:
        inputs += ["-i", os.path.basename(sfx_wav)]
        fc.append(f"[{n_in}:a]apad=whole_dur={total:.3f},atrim=0:{total:.3f}[s]")
        mix.append("[s]")
    fc.append(f"{''.join(mix)}amix=inputs={len(mix)}:duration=longest:normalize=0,"
              "loudnorm=I=-14:TP=-1.5:LRA=11,alimiter=limit=0.89,aresample=48000[a]")
    cmd = (["ffmpeg", "-y", "-v", "error", "-i", "joined.mp4"] + inputs
           + ["-filter_complex", ";".join(fc), "-map", "[v]", "-map", "[a]",
              "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
              "-ar", "48000", "-t", f"{total:.2f}", "-movflags", "+faststart", os.path.basename(out)])
    run(cmd, cwd=d)
    for f in os.listdir(d):
        if f.startswith("part") or f == "joined.mp4":
            os.remove(os.path.join(d, f))
    progress(1.0)
    return total
