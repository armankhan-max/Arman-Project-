"""Scratch the 'circle with one short vertical line' mark into a stone photo.
usage: python carve.py in.png out.png [cx cy r]   (fractions; auto-detect if omitted)"""
import sys, numpy as np, cv2
src, dst = sys.argv[1], sys.argv[2]
im = cv2.imread(src, cv2.IMREAD_GRAYSCALE).astype(np.float32) / 255
H, W = im.shape
if len(sys.argv) >= 6:
    cx, cy, r = float(sys.argv[3]) * W, float(sys.argv[4]) * H, float(sys.argv[5]) * W
else:
    # stone = smooth region near the centre that differs from the surroundings
    bl = cv2.GaussianBlur(im, (0, 0), 6)
    c = bl[int(H * .35):int(H * .65), int(W * .35):int(W * .65)].mean()
    m = (np.abs(bl - c) < 0.08).astype(np.uint8)
    n, lab, st, cen = cv2.connectedComponentsWithStats(m)
    k = lab[H // 2, W // 2]
    if k == 0:
        k = 1 + np.argmax(st[1:, cv2.CC_STAT_AREA])
    x, y, w, h = st[k, :4]
    cx, cy = x + w / 2, y + h / 2
    r = 0.22 * min(w, h)
rng = np.random.default_rng(3)
groove = np.zeros_like(im)
th = np.linspace(0, 2 * np.pi * 1.04, 240)
rr = r * (1 + 0.025 * np.cumsum(rng.normal(0, 1, 240)) / 6)
pts = np.stack([cx + rr * np.cos(th), cy + rr * 0.93 * np.sin(th)], 1).astype(np.int32)
wid = max(2, int(r * 0.07))
cv2.polylines(groove, [pts], False, 1.0, wid, cv2.LINE_AA)
cv2.line(groove, (int(cx + rng.normal(0, 1)), int(cy - r * 0.62)), (int(cx + rng.normal(0, 2)), int(cy + r * 0.62)), 1.0, wid, cv2.LINE_AA)
# rough edges
groove *= np.clip(0.75 + 0.5 * rng.random(groove.shape).astype(np.float32), 0, 1)
groove = cv2.GaussianBlur(groove, (0, 0), max(0.8, wid * 0.25))
# carved look: dark inside, light rim on the lower-right edge (light from top-left)
sh = np.roll(np.roll(groove, -max(1, wid // 2), 0), -max(1, wid // 2), 1)
hi = np.roll(np.roll(groove, max(1, wid // 2), 0), max(1, wid // 2), 1)
out = im * (1 - 0.55 * groove) + 0.10 * np.clip(hi - groove, 0, 1) - 0.05 * np.clip(sh - groove, 0, 1)
cv2.imwrite(dst, np.clip(out * 255, 0, 255).astype(np.uint8))
print(dst, int(cx), int(cy), int(r))
