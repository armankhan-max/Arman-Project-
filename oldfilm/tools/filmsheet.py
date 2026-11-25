import sys, os, subprocess, glob
from PIL import Image, ImageDraw
f = sys.argv[1]; step = float(sys.argv[2]); outp = sys.argv[3]
tmp = outp + "_frames"; os.makedirs(tmp, exist_ok=True)
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", f, "-vf", f"fps=1/{step},scale=224:168", "-q:v", "4", f"{tmp}/%05d.jpg"], check=True)
fr = sorted(glob.glob(f"{tmp}/*.jpg")); cols, per = 8, 64
for p in range(0, len(fr), per):
    chunk = fr[p:p + per]; rows = (len(chunk) + cols - 1) // cols
    S = Image.new("RGB", (cols * 224, rows * 182), "white"); d = ImageDraw.Draw(S)
    for i, x in enumerate(chunk):
        k = p + i; t = k * step + step / 2
        S.paste(Image.open(x), ((i % cols) * 224, (i // cols) * 182))
        d.text(((i % cols) * 224 + 3, (i // cols) * 182 + 169), f"{int(t//60)}:{t%60:04.1f} ({t:.0f}s)", fill="black")
    S.save(f"{outp}_{p//per:02d}.jpg", quality=75)
print(len(fr))
