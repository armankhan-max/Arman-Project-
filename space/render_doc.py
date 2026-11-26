"""Render the space documentary.

Usage:
  python render.py --still 12.5 out.png
  python render.py --sheet out.png t1 t2 ...       # contact sheet of frames
  python render.py --audio voice.mp3 --out video.mp4 [--jobs 4] [--fps 30]
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

from cosmos import W, H  # noqa: E402
from doc_scenes import render_frame  # noqa: E402


def still(t, out):
    s = skia.Surface(W, H)
    render_frame(s.getCanvas(), t)
    s.makeImageSnapshot().save(out, skia.kPNG)


def sheet(times, out, cols=4):
    tw, th = 480, 270
    rows = math.ceil(len(times) / cols)
    big = skia.Surface(tw * cols, th * rows)
    bc = big.getCanvas()
    s = skia.Surface(W, H)
    for i, t in enumerate(times):
        render_frame(s.getCanvas(), t)
        img = s.makeImageSnapshot()
        bc.drawImageRect(img, skia.Rect.MakeXYWH((i % cols) * tw, (i // cols) * th, tw, th),
                         skia.SamplingOptions(skia.FilterMode.kLinear))
        f = skia.Font(None, 18)
        bc.drawString(f"{t:.1f}", (i % cols) * tw + 6, (i // cols) * th + 20, f, skia.Paint(Color=skia.ColorYELLOW))
    big.makeImageSnapshot().save(out, skia.kPNG)


def render_range(f0, f1, fps, out):
    surface = skia.Surface(W, H)
    c = surface.getCanvas()
    cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}", "-r", str(fps),
           "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-tune", "animation",
           "-pix_fmt", "yuv420p", out]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    t0 = time.time()
    for f in range(f0, f1):
        render_frame(c, f / fps)
        arr = surface.makeImageSnapshot().toarray(colorType=skia.kBGRA_8888_ColorType)
        ff.stdin.write(arr.tobytes())
        if (f - f0) % 600 == 0:
            print(f"[{os.path.basename(out)}] {f - f0}/{f1 - f0}  {time.time() - t0:.0f}s", flush=True)
    ff.stdin.close()
    ff.wait()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--still", nargs=2)
    ap.add_argument("--sheet", nargs="+")
    ap.add_argument("--audio")
    ap.add_argument("--out", default="video.mp4")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--range", nargs=3)
    a = ap.parse_args()
    if a.still:
        still(float(a.still[0]), a.still[1])
        return
    if a.sheet:
        sheet([float(x) for x in a.sheet[1:]], a.sheet[0])
        return
    if a.range:
        render_range(int(a.range[0]), int(a.range[1]), a.fps, a.range[2])
        return
    dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                                         "csv=p=0", a.audio]).strip())
    total = int(math.ceil(dur * a.fps))
    nparts = a.jobs * 4
    per = math.ceil(total / nparts)
    tmp = os.path.splitext(a.out)[0] + "_parts"
    os.makedirs(tmp, exist_ok=True)
    jobs = []
    for j in range(nparts):
        f0, f1 = j * per, min(total, (j + 1) * per)
        jobs.append((f0, f1, os.path.join(tmp, f"part{j:03d}.mp4")))
    running = []
    pending = [jb for jb in jobs if not os.path.exists(jb[2] + ".done")]
    while pending or running:
        while pending and len(running) < a.jobs:
            f0, f1, part = pending.pop(0)
            p = subprocess.Popen([sys.executable, __file__, "--fps", str(a.fps), "--range", str(f0), str(f1), part])
            running.append((p, part))
        for p, part in list(running):
            if p.poll() is not None:
                if p.returncode != 0:
                    sys.exit("worker failed: " + part)
                open(part + ".done", "w").close()
                running.remove((p, part))
        time.sleep(1)
    lst = os.path.join(tmp, "list.txt")
    with open(lst, "w") as fh:
        for _, _, part in jobs:
            fh.write(f"file '{os.path.abspath(part)}'\n")
    subprocess.check_call(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy",
                           "-movflags", "+faststart", a.out])
    print("wrote", a.out)


if __name__ == "__main__":
    main()
