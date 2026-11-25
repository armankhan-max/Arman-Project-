"""Crop scanned-negative borders (black frame + edge numbers). usage: autocrop.py indir outdir"""
import sys, os, glob, numpy as np, cv2
ind, outd = sys.argv[1], sys.argv[2]; os.makedirs(outd, exist_ok=True)
for f in sorted(glob.glob(os.path.join(ind, "*.jpg"))):
    o = os.path.join(outd, os.path.basename(f))
    if os.path.exists(o): continue
    im = cv2.imread(f, cv2.IMREAD_GRAYSCALE)
    if im is None: continue
    h, w = im.shape
    def span(a, axis_len):
        good = np.where(a > 0.6)[0]
        if len(good) < axis_len * 0.4: return 0, axis_len
        return good[0], good[-1] + 1
    b = im > 45
    rows = b[:, int(w*0.2):int(w*0.8)].mean(1); cols = b[int(h*0.2):int(h*0.8), :].mean(0)
    y0, y1 = span(rows, h); x0, x1 = span(cols, w)
    ih, iw = y1 - y0, x1 - x0
    ins = 0.035
    y0 += int(ih*ins); y1 -= int(ih*ins); x0 += int(iw*0.065); x1 -= int(iw*0.065)
    c = im[y0:y1, x0:x1]
    if c.size < 0.25 * im.size: c = im
    cv2.imwrite(o, c, [cv2.IMWRITE_JPEG_QUALITY, 93])
print("done")
