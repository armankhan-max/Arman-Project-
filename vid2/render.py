"""Render 'The Man Who Sold the Eiffel Tower Twice' (1080x1920, 30fps).

  python render.py --still 12.5 out.png
  python render.py --sheet out.png t1 t2 ...       # contact sheet of stills
  python render.py --audio mix.wav --out final.mp4 [--jobs 4]
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

from engine3d import W, H, clamp, ease  # noqa: E402
import scenes as SC  # noqa: E402


def shot_image(fn, t):
    s = skia.Surface(W, H)
    fn(t).render(s.getCanvas())
    return s.makeImageSnapshot()


def render_frame(canvas, t):
    tl = SC.TIMELINE
    idx = max(i for i, s in enumerate(tl) if s[0] <= t or i == 0)
    start, end, fn, d, kind = tl[idx]
    # inside the incoming half of this shot's transition?
    prev = None
    if idx > 0 and d > 0 and t < start + d / 2:
        prev = tl[idx - 1]
    # inside the outgoing half (before next shot starts)?
    nxt = None
    if idx + 1 < len(tl):
        ns, _, nfn, nd, nk = tl[idx + 1]
        if nd > 0 and t >= ns - nd / 2:
            nxt = tl[idx + 1]
    if prev is None and nxt is None:
        fn(t).render(canvas)
    else:
        if nxt is not None:
            a_fn, b_fn, cut, dd, kk = fn, nxt[2], nxt[0], nxt[3], nxt[4]
        else:
            a_fn, b_fn, cut, dd, kk = prev[2], fn, start, d, kind
        x = clamp((t - (cut - dd / 2)) / dd)  # 0..1 across the transition
        A = shot_image(a_fn, t)
        B = shot_image(b_fn, t)
        canvas.clear(skia.ColorBLACK)
        if kk == 'whip':
            sig = 70 * math.sin(x * math.pi) + 0.01
            blur = skia.ImageFilters.Blur(sig, 0.5)
            off = W * 0.35
            pa = skia.Paint(ImageFilter=blur, Alphaf=1 - ease(x))
            pb = skia.Paint(ImageFilter=blur, Alphaf=ease(x))
            canvas.drawImage(A, -off * ease(x), 0, skia.SamplingOptions(), pa)
            canvas.drawImage(B, off * (1 - ease(x)), 0, skia.SamplingOptions(), pb)
        else:
            canvas.drawImage(A, 0, 0)
            canvas.drawImage(B, 0, 0, skia.SamplingOptions(), skia.Paint(Alphaf=ease(x)))
    SC.overlays(canvas, t)


def still(t, out):
    s = skia.Surface(W, H)
    render_frame(s.getCanvas(), t)
    s.makeImageSnapshot().save(out, skia.kPNG)


def sheet(out, times, cols=6, scale=0.25):
    w, h = int(W * scale), int(H * scale)
    rows = math.ceil(len(times) / cols)
    S = skia.Surface(w * cols, h * rows)
    c = S.getCanvas()
    c.clear(skia.ColorBLACK)
    big = skia.Surface(W, H)
    for i, t in enumerate(times):
        render_frame(big.getCanvas(), t)
        img = big.makeImageSnapshot()
        c.drawImageRect(img, skia.Rect((i % cols) * w, (i // cols) * h, (i % cols + 1) * w, (i // cols + 1) * h),
                        skia.SamplingOptions(skia.FilterMode.kLinear))
        c.drawString(f'{t:.2f}', (i % cols) * w + 6, (i // cols) * h + 22, skia.Font(None, 20),
                     skia.Paint(Color=skia.ColorYELLOW))
    S.makeImageSnapshot().save(out, skia.kPNG)


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
        if (f - f0) % 150 == 0:
            print(f"[{os.path.basename(out)}] {f - f0}/{f1 - f0}  {time.time() - t0:.0f}s", flush=True)
    ff.stdin.close()
    ff.wait()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--still", nargs=2)
    ap.add_argument("--sheet", nargs='+')
    ap.add_argument("--audio")
    ap.add_argument("--out", default="final.mp4")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--range", nargs=3)
    a = ap.parse_args()
    if a.still:
        still(float(a.still[0]), a.still[1])
        return
    if a.sheet:
        sheet(a.sheet[0], [float(x) for x in a.sheet[1:]])
        return
    if a.range:
        render_range(int(a.range[0]), int(a.range[1]), a.fps, a.range[2])
        return
    total = int(math.ceil(SC.DUR * a.fps))
    tmp = os.path.splitext(a.out)[0] + "_parts"
    os.makedirs(tmp, exist_ok=True)
    # interleave chunks so heavy shots spread across workers
    chunk = 60
    jobs = [(f, min(total, f + chunk)) for f in range(0, total, chunk)]
    parts = [os.path.join(tmp, f"p{i:03d}.mp4") for i in range(len(jobs))]
    running = []
    for (f0, f1), part in zip(jobs, parts):
        while len(running) >= a.jobs:
            running = [p for p in running if p.poll() is None]
            time.sleep(0.2)
        running.append(subprocess.Popen([sys.executable, __file__, "--fps", str(a.fps), "--range", str(f0), str(f1), part],
                                         stdout=subprocess.DEVNULL))
    for p in running:
        p.wait()
    lst = os.path.join(tmp, "list.txt")
    with open(lst, "w") as fh:
        for p in parts:
            fh.write(f"file '{os.path.abspath(p)}'\n")
    cmd = ["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst]
    if a.audio:
        cmd += ["-i", a.audio, "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest"]
    else:
        cmd += ["-c", "copy"]
    cmd += ["-movflags", "+faststart", a.out]
    subprocess.check_call(cmd)
    print("wrote", a.out)


if __name__ == "__main__":
    main()
