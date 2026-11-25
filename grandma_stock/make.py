#!/usr/bin/env python3
"""One-command builder for the grandma stock-footage video style.

    python3 make.py projects/<name>            # full build -> <work>/<OUT_NAME>.mp4
    python3 make.py projects/<name> --frames 26 120 484   # preview frames only

Steps: download missing Mixkit clips/music -> render every shot (Ken Burns / push-in,
colour grade, grain) -> build ASS text animations -> mix voice (slowed + light reverb),
ducked music, SFX, ambience -> crossfade all shots, burn text, encode (<400 MB).
"""
import argparse, importlib.util, json, os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

KIT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, f"{KIT}/lib")
import vtext                       # noqa: E402
from mixlib import mix             # noqa: E402

FPS, T = 30, 0.4                   # frame rate, crossfade length
GRADE = "eq=contrast=1.04:saturation=1.06:gamma=0.98,vignette=angle=PI/5,noise=alls=3:allf=t"


def load_project(path):
    spec = importlib.util.spec_from_file_location("project", f"{path}/project.py")
    p = importlib.util.module_from_spec(spec); spec.loader.exec_module(p)
    p.DIR = os.path.abspath(path)
    s = p.SPD
    p.TOTAL = p.VO_DURATION / s
    p.SHOTS_S = [(round(a / s, 3), b, c) for a, b, c in p.SHOTS]
    p.FLASH_S = {round(a / s, 3) for a in p.FLASH_CUTS}
    return p


def fetch(url, dst):
    if not os.path.exists(dst) or os.path.getsize(dst) == 0:
        subprocess.run(["curl", "-sf", "-m", "120", "-o", dst, url], check=False)
    return os.path.exists(dst) and os.path.getsize(dst) > 0


def download_assets(p, work):
    os.makedirs(f"{work}/clips", exist_ok=True); os.makedirs(f"{work}/music", exist_ok=True)
    ids = {src[2:].split("@")[0] for _, src, _ in p.SHOTS if src.startswith("V:")}
    for cid in sorted(ids):
        dst = f"{work}/clips/{cid}.mp4"
        if not fetch(f"https://assets.mixkit.co/videos/{cid}/{cid}-1080.mp4", dst):
            fetch(f"https://assets.mixkit.co/videos/{cid}/{cid}-720.mp4", dst)
    for mid in p.MUSIC:
        fetch(f"https://assets.mixkit.co/music/{mid}/{mid}.mp3", f"{work}/music/{mid}.mp3")


def zp(motion, n, strength):
    e = f"(0.5-0.5*cos(PI*min(on/{max(n-1,1)}\\,1)))"          # cosine ease
    cx, cy = "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
    if motion == "in":
        z, x, y = f"1.0+{strength}*{e}", cx, cy
    elif motion == "out":
        z, x, y = f"{1+strength}-{strength}*{e}", cx, cy
    elif motion == "left":
        z, x, y = f"{1+strength*0.85:.3f}", f"(iw-iw/zoom)*(1-{e})", cy
    else:
        z, x, y = f"{1+strength*0.85:.3f}", f"(iw-iw/zoom)*{e}", cy
    return f"zoompan=z='{z}':x='{x}':y='{y}':d=1:s=1920x1080:fps={FPS}"


def shot_jobs(p, work):
    os.makedirs(f"{work}/segs", exist_ok=True)
    jobs, segs = [], []
    S = p.SHOTS_S
    for i, (st, src, mot) in enumerate(S):
        en = S[i + 1][0] if i + 1 < len(S) else p.TOTAL
        d = en - st
        L = d + (T if i + 1 < len(S) else 0)
        n = int(round(L * FPS))
        out = f"{work}/segs/{i:03d}.mp4"
        segs.append((out, d, L))
        if src.startswith("I:"):
            img = os.path.join(p.IMG_DIR, p.IMG_PATTERN.format(id=src[2:]))
            vf = (f"scale=3840:2160:force_original_aspect_ratio=increase:flags=lanczos,crop=3840:2160,"
                  f"{zp(mot, n, 0.16)},{GRADE},format=yuv420p")
            cmd = ["ffmpeg", "-v", "error", "-y", "-loop", "1", "-framerate", str(FPS), "-i", img]
        else:
            cid, off = src[2:].split("@"); off = float(off)
            clip = f"{work}/clips/{cid}.mp4"
            dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                                 "-of", "csv=p=0", clip]))
            avail = dur - off - 0.1
            if avail < L:
                off, avail = 0.0, dur - 0.1
            speed = min(1.0, avail / L)                         # slow a short clip instead of freezing
            vf = (f"setpts=PTS/{speed:.4f},fps={FPS},scale=3840:2160:force_original_aspect_ratio=increase,"
                  f"crop=3840:2160,{zp(mot, n, 0.08)},{GRADE},format=yuv420p")
            cmd = ["ffmpeg", "-v", "error", "-y", "-ss", str(off), "-i", clip]
        cmd += ["-vf", vf, "-frames:v", str(n), "-c:v", "libx264", "-preset", "veryfast", "-crf", "17", "-an", out]
        jobs.append(cmd)
    return jobs, segs


def assemble(p, work, segs, out):
    args = ["ffmpeg", "-v", "error", "-stats", "-y"]
    for s in segs:
        args += ["-i", s[0]]
    args += ["-i", f"{work}/mix.wav"]
    parts, prev, acc = [], "[0:v]", 0.0
    for i in range(1, len(segs)):
        acc += segs[i - 1][1]
        tr = "fadewhite" if p.SHOTS_S[i][0] in p.FLASH_S else ("smoothleft" if i % 4 == 0 else "fade")
        parts.append(f"{prev}[{i}:v]xfade=transition={tr}:duration={T}:offset={acc:.4f}[x{i}]")
        prev = f"[x{i}]"
    parts.append(f"{prev}ass={work}/text.ass:fontsdir={KIT}/fonts,fade=t=in:st=0:d=0.3,"
                 f"fade=t=out:st={p.TOTAL-1.2}:d=1.2,format=yuv420p[v]")
    open(f"{work}/graph.txt", "w").write(";\n".join(parts))
    args += ["-filter_complex_script", f"{work}/graph.txt", "-map", "[v]", "-map", f"{len(segs)}:a",
             "-c:v", "libx264", "-preset", "fast", "-crf", "21", "-maxrate", "4800k", "-bufsize", "9600k",
             "-r", str(FPS), "-c:a", "aac", "-b:a", "192k", "-t", f"{p.TOTAL:.3f}", "-movflags", "+faststart", out]
    subprocess.run(args, check=True)


def build_text(p, work):
    vtext.SPD = p.SPD
    vtext.reset()
    code = open(f"{p.DIR}/text_cues.py").read()
    exec(compile(code, f"{p.DIR}/text_cues.py", "exec"), vtext.__dict__)
    return vtext.save(f"{work}/text.ass", f"{work}/sfx_text.json")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--work", default=None, help="work dir (default: <project>/_work)")
    ap.add_argument("--frames", nargs="*", type=float, help="only render preview frames at these output times")
    a = ap.parse_args()
    p = load_project(a.project)
    work = os.path.abspath(a.work or f"{p.DIR}/_work"); os.makedirs(work, exist_ok=True)
    download_assets(p, work)
    print("text:", build_text(p, work))
    jobs, segs = shot_jobs(p, work)
    if a.frames:
        os.makedirs(f"{work}/frames", exist_ok=True)
        for t in a.frames:
            k = max(i for i, s in enumerate(p.SHOTS_S) if s[0] <= t)
            subprocess.run(jobs[k], check=True)
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t - p.SHOTS_S[k][0]:.3f}", "-i", segs[k][0],
                            "-frames:v", "1", "-vf", f"setpts=PTS+{t}/TB,ass={work}/text.ass:fontsdir={KIT}/fonts",
                            f"{work}/frames/{t:.1f}.jpg"], check=True)
        print("frames in", f"{work}/frames"); return
    with ThreadPoolExecutor(max_workers=os.cpu_count() or 4) as ex:
        list(ex.map(lambda c: subprocess.run(c, check=True), jobs))
    mix(p, work, KIT)
    out = f"{work}/{p.OUT_NAME}.mp4"
    assemble(p, work, segs, out)
    print("DONE ->", out)


if __name__ == "__main__":
    main()
