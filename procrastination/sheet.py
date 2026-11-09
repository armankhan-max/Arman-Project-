"""Contact sheet of stills: python sheet.py out.png t1 t2 ..."""
import sys, skia
from kit import W, H
from loop_scenes import render_frame
ts = [float(x) for x in sys.argv[2:]]
cols = 4; rows = (len(ts) + cols - 1) // cols
sw, sh = 480, 270
out = skia.Surface(sw * cols, sh * rows)
oc = out.getCanvas()
s = skia.Surface(W, H)
for i, t in enumerate(ts):
    render_frame(s.getCanvas(), t)
    img = s.makeImageSnapshot()
    oc.drawImageRect(img, skia.Rect.MakeXYWH((i % cols) * sw, (i // cols) * sh, sw, sh), skia.SamplingOptions(skia.FilterMode.kLinear))
    f = skia.Font(None, 18); oc.drawString(f"{t:.1f}", (i % cols) * sw + 6, (i // cols) * sh + 20, f, skia.Paint(Color=skia.ColorYELLOW))
out.makeImageSnapshot().save(sys.argv[1], skia.kPNG)
