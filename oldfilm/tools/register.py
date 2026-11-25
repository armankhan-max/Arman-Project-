import numpy as np, cv2, sys
def page(seed, out, marks_rows, big_mark=False):
    r = np.random.default_rng(seed)
    W, H = 2200, 1400
    p = 0.78 + 0.06 * cv2.GaussianBlur(r.normal(0, 1, (H, W)).astype(np.float32), (0, 0), 40)
    p += 0.02 * r.normal(0, 1, (H, W)).astype(np.float32)
    # foxing stains
    for _ in range(25):
        x, y, rad = r.integers(0, W), r.integers(0, H), r.integers(4, 22)
        cv2.circle(p, (int(x), int(y)), int(rad), float(p.mean() - 0.05), -1)
    p = cv2.GaussianBlur(p, (0, 0), 3)
    ink = np.zeros_like(p)
    top, step = 120, 58
    mx = 330
    cv2.line(ink, (mx - 30, 0), (mx - 30, H), 0.5, 2, cv2.LINE_AA)
    for k in range(int((H - top) / step)):
        y = top + k * step
        cv2.line(ink, (60, y + 18), (W - 60, y + 18), 0.22, 1, cv2.LINE_AA)
        # illegible handwriting strokes (no real letters)
        x = mx + int(r.integers(0, 40))
        for word in range(int(r.integers(3, 8))):
            wl = int(r.integers(60, 220))
            xs = np.arange(x, x + wl)
            ph = r.uniform(0, 6)
            ys = y + 2 + 9 * np.sin(xs * r.uniform(0.18, 0.32) + ph) * np.abs(np.sin(xs * 0.05 + ph)) + r.normal(0, 1.2, len(xs))
            pts = np.stack([xs, ys], 1).astype(np.int32)
            cv2.polylines(ink, [pts], False, 0.95, 3, cv2.LINE_AA)
            for _ in range(int(r.integers(0, 3))):  # ascenders
                ax = int(r.integers(x, x + wl))
                cv2.line(ink, (ax, y + 4), (ax + int(r.integers(-6, 7)), y - 16), 0.8, 2, cv2.LINE_AA)
            x += wl + int(r.integers(25, 60))
            if x > W - 300: break
        # date column scribble
        cv2.polylines(ink, [np.array([[80, y + 4], [110, y - 6], [140, y + 6], [175, y - 4], [205, y + 3]], np.int32)], False, 0.7, 2, cv2.LINE_AA)
        if k in marks_rows:
            c = (250, y)
            rad = 17 if not big_mark else 40
            cv2.circle(ink, c, rad, 1.0, 3, cv2.LINE_AA)
            cv2.line(ink, (c[0], c[1] - rad + 4), (c[0], c[1] + rad - 4), 1.0, 3, cv2.LINE_AA)
    ink = cv2.GaussianBlur(ink, (0, 0), 0.8)
    img = p * (1 - 0.92 * np.clip(ink, 0, 1))
    # depth of field: sharp band around the marks, soft elsewhere
    blur = cv2.GaussianBlur(img, (0, 0), 6)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    fy = top + (marks_rows[len(marks_rows) // 2] if marks_rows else 10) * step
    f = np.clip(np.sqrt(((xx - 250) / 900) ** 2 + ((yy - fy) / 380) ** 2) - 0.25, 0, 1)
    img = img * (1 - f) + blur * f
    vig = 1 - 0.45 * np.clip(np.sqrt(((xx - W / 2) / W) ** 2 + ((yy - H / 2) / H) ** 2) * 1.6 - 0.2, 0, 1)
    img *= vig
    cv2.imwrite(out, np.clip(img * 255, 0, 255).astype(np.uint8))
page(1, "comp/register_mark_1.png", [3, 7, 12])
page(2, "comp/register_mark_2.png", [2, 5, 9, 15])
page(3, "comp/register_mark_3.png", [6, 10])
page(4, "comp/register_plain_1.png", [])
print("ok")
