"""Render the 2D animated video for the voiceover.

Usage:
  python render.py --still 12.5 out.png          # preview a single frame
  python render.py --audio voice.mp3 --out final.mp4 [--jobs 4] [--fps 30]
"""
import argparse
import math
import os
import subprocess
import sys
import time

import skia

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from pgfx import W, H  # noqa: E402
from scenes_wi import render_frame  # noqa: E402


def still(t, out):
    s = skia.Surface(W, H)
    render_frame(s.getCanvas(), t)
    s.makeImageSnapshot().save(out, skia.kPNG)


def render_range(f0, f1, fps, out):
    surface = skia.Surface(W, H)
    c = surface.getCanvas()
    cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}", "-r", str(fps),
           "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-tune", "animation",
           "-pix_fmt", "yuv420p", out]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    t0 = time.time()
    for f in range(f0, f1):
        render_frame(c, f / fps)
        arr = surface.makeImageSnapshot().toarray(colorType=skia.kBGRA_8888_ColorType)
        ff.stdin.write(arr.tobytes())
        if (f - f0) % 300 == 0:
            print(f"[{out}] frame {f - f0}/{f1 - f0}  {time.time() - t0:.0f}s", flush=True)
    ff.stdin.close()
    ff.wait()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--still", nargs=2)
    ap.add_argument("--audio")
    ap.add_argument("--out", default="final.mp4")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--range", nargs=3)  # internal: f0 f1 out
    a = ap.parse_args()
    if a.still:
        still(float(a.still[0]), a.still[1])
        return
    if a.range:
        render_range(int(a.range[0]), int(a.range[1]), a.fps, a.range[2])
        return
    dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                                         "csv=p=0", a.audio]).strip())
    total = int(math.ceil(dur * a.fps))
    per = math.ceil(total / a.jobs)
    tmp = os.path.splitext(a.out)[0] + "_parts"
    os.makedirs(tmp, exist_ok=True)
    procs, parts = [], []
    for j in range(a.jobs):
        f0, f1 = j * per, min(total, (j + 1) * per)
        part = os.path.join(tmp, f"part{j}.mp4")
        parts.append(part)
        procs.append(subprocess.Popen([sys.executable, __file__, "--fps", str(a.fps), "--range", str(f0), str(f1),
                                       part]))
    for p in procs:
        if p.wait() != 0:
            sys.exit("worker failed")
    lst = os.path.join(tmp, "list.txt")
    with open(lst, "w") as fh:
        for p in parts:
            fh.write(f"file '{os.path.abspath(p)}'\n")
    subprocess.check_call(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst, "-i", a.audio,
                           "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k",
                           "-shortest", "-movflags", "+faststart", a.out])
    print("wrote", a.out)


if __name__ == "__main__":
    main()
