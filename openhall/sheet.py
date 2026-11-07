"""Contact sheet of stills: python sheet.py out.png t1 t2 ..."""
import sys
import skia
from scenes_wi import render_frame
from pgfx import W, H
ts = [float(x) for x in sys.argv[2:]]
cols = 4
rows = (len(ts) + cols - 1) // cols
sw, sh = W // 4, H // 4
out = skia.Surface(sw * cols, sh * rows)
oc = out.getCanvas()
s = skia.Surface(W, H)
for i, t in enumerate(ts):
    render_frame(s.getCanvas(), t)
    img = s.makeImageSnapshot()
    oc.drawImageRect(img, skia.Rect.MakeXYWH((i % cols) * sw, (i // cols) * sh, sw, sh),
                     skia.SamplingOptions(skia.FilterMode.kLinear))
    oc.drawString(f"{t:.1f}", (i % cols) * sw + 8, (i // cols) * sh + 30, skia.Font(None, 26),
                  skia.Paint(Color=skia.ColorRED))
out.makeImageSnapshot().save(sys.argv[1], skia.kPNG)
