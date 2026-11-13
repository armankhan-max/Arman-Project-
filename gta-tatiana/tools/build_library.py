#!/usr/bin/env python3
"""build_library.py <src.mp4> <tag> [threshold]
Splits a source video into its shots (measured scene changes), cuts every usable shot into
footage/library/<tag>-NNN.mp4 (1920x1080, 30 fps, no sound, a few frames trimmed at each end) and
draws contact sheets footage/library/sheets/<tag>-pK.jpg (one labelled middle frame per shot).
Appends to footage/library/library.json."""
import json, re, subprocess, sys
from pathlib import Path

src = Path(sys.argv[1]).resolve(); tag = sys.argv[2]; th = float(sys.argv[3]) if len(sys.argv) > 3 else 0.3
lib = src.parent.parent / "library"; (lib / "sheets").mkdir(parents=True, exist_ok=True)
dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(src)]))
out = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(src), "-vf", f"select='gt(scene,{th})',showinfo", "-an", "-f", "null", "-"],
                     capture_output=True, text=True).stderr
cuts = [0.0] + [float(m) for m in re.findall(r"pts_time:([\d.]+)", out)] + [dur]
shots = []
for a, b in zip(cuts, cuts[1:]):
    a2, b2 = a + 0.1, b - 0.1
    if b2 - a2 < 0.7:
        continue
    while b2 - a2 > 8.5:  # split long shots into pieces of about 6 s
        shots.append((a2, a2 + 6.0)); a2 += 6.0
    shots.append((a2, b2))
book_p = lib / "library.json"
book = json.loads(book_p.read_text()) if book_p.exists() else {}
names = []
for i, (a, b) in enumerate(shots, 1):
    name = f"{tag}-{i:03d}"
    f = lib / f"{name}.mp4"
    if not f.exists():
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{a:.3f}", "-i", str(src), "-t", f"{b - a:.3f}",
                        "-vf", "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,fps=30,format=yuv420p",
                        "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", str(f)], check=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{(b - a) / 2:.3f}", "-i", str(f), "-frames:v", "1",
                        "-vf", f"scale=384:216,drawtext=text='{name}  {b - a:.1f}s':x=6:y=6:fontsize=20:fontcolor=white:box=1:boxcolor=black@0.7",
                        str(lib / "sheets" / f"_{name}.jpg")], check=True)
    book[name] = {"src": src.name, "a": round(a, 2), "b": round(b, 2), "dur": round(b - a, 2)}
    names.append(name)
book_p.write_text(json.dumps(book, indent=1))
for k in range(0, len(names), 30):
    grp = names[k:k + 30]; page = k // 30 + 1
    inputs = []
    for n in grp:
        inputs += ["-i", str(lib / "sheets" / f"_{n}.jpg")]
    layout = "|".join(f"{(j % 6) * 384}_{(j // 6) * 216}" for j in range(len(grp)))
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex",
                    f"xstack=inputs={len(grp)}:layout={layout}:fill=black" if len(grp) > 1 else "null",
                    str(lib / "sheets" / f"{tag}-p{page}.jpg")], check=True)
print(tag, len(names), "shots", "sheets:", (len(names) + 29) // 30)
