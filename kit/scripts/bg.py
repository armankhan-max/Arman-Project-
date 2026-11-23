"""Build the continuous b-roll background track (bg.mp4) from plan.json."""
import os as _os
KIT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
import json, os, subprocess
from concurrent.futures import ThreadPoolExecutor

FPS = 30
p = json.load(open("plan.json"))
os.makedirs("bgseg", exist_ok=True)


def dur(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                       capture_output=True, text=True)
    try: return float(r.stdout.strip())
    except ValueError: return 0


def seg(i):
    sc = p["scenes"][i]
    n = round(sc["e"] * FPS) - round(sc["s"] * FPS)
    out = f"bgseg/{i:04d}.mp4"
    if os.path.exists(out): return
    src = f"{KIT}/clips/{sc['clip']}.mp4"
    d = dur(src)
    need = n / FPS
    off = 0.4 if d > need + 1.0 else 0
    loop = ["-stream_loop", "-1"] if d < need + off else []
    vf = ("scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,setsar=1,"
          f"fps={FPS},eq=saturation=1.05:contrast=1.04:brightness=-0.02,"
          "colorchannelmixer=rr=0.55:gg=0.55:bb=0.55,vignette=angle=PI/4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", *loop, "-ss", str(off), "-i", src, "-an", "-vf", vf,
                    "-frames:v", str(n), "-c:v", "libx264", "-preset", "veryfast", "-crf", "17",
                    "-pix_fmt", "yuv420p", "-g", "60", out + ".tmp.mp4"], check=True)
    os.rename(out + ".tmp.mp4", out)


with ThreadPoolExecutor(4) as ex:
    list(ex.map(seg, range(len(p["scenes"]))))
with open("bgseg/list.txt", "w") as f:
    for i in range(len(p["scenes"])): f.write(f"file '{i:04d}.mp4'\n")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", "bgseg/list.txt", "-c", "copy", "bg.mp4"],
               check=True)
print("bg.mp4 done")
