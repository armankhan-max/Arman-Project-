import sys, subprocess
# python3 sheet.py out.jpg dir f1 f2 ... (up to 10, 5 per row)
out, d, *fs = sys.argv[1:]
ins = sum([["-i", f"{d}/f{f}.jpg"] for f in fs], [])
n = len(fs); cols = min(5, n)
fc = "".join(f"[{i}]scale=360:640,drawtext=text='{fs[i]}':x=8:y=8:fontsize=28:fontcolor=red:box=1[a{i}];" for i in range(n))
lay = "|".join(f"{(i%cols)*360}_{(i//cols)*640}" for i in range(n))
fc += "".join(f"[a{i}]" for i in range(n)) + (f"xstack=inputs={n}:layout={lay}[o]" if n > 1 else "copy[o]")
subprocess.run(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", fc, "-map", "[o]", out], check=True)
