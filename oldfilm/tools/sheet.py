import sys, glob, os
from PIL import Image, ImageDraw, ImageOps
out = sys.argv[1]; files = sorted(sum([glob.glob(g) for g in sys.argv[2:]], []))
cols = 4; tw, th = 384, 256
rows = (len(files) + cols - 1) // cols
S = Image.new("RGB", (cols * tw, max(1, rows) * (th + 18)), "white"); d = ImageDraw.Draw(S)
for i, f in enumerate(files):
    try:
        im = Image.open(f); im.draft("RGB", (tw * 2, th * 2)); im = ImageOps.exif_transpose(im).convert("RGB")
        im.thumbnail((tw, th))
    except Exception as e:
        continue
    x, y = (i % cols) * tw, (i // cols) * (th + 18)
    S.paste(im, (x + (tw - im.width) // 2, y))
    d.text((x + 4, y + th + 3), os.path.basename(f)[:58], fill="black")
S.save(out, quality=80); print(out, len(files))
