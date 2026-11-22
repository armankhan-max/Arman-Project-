import os, numpy as np
from PIL import Image, ImageFilter
from concurrent.futures import ProcessPoolExecutor
W, H = 1600, 900
def autocrop(im):
    g = np.asarray(im.convert("L")).astype(np.float32); h, w = g.shape
    def edge(arr):
        n = 0
        for row in arr:
            if (row.mean() > 225 or row.mean() < 28) and row.std() < 30: n += 1
            else: break
        return n
    t = edge(g); b = edge(g[::-1]); l = edge(g.T); r = edge(g.T[::-1])
    m = 0.03
    box = (l + int(w * m), t + int(h * m), w - r - int(w * m), h - b - int(h * m))
    return im.crop(box) if box[2] - box[0] > w * 0.4 and box[3] - box[1] > h * 0.4 else im
def proc(k):
    rng = np.random.default_rng(abs(hash(k)) % 2**32)
    im = Image.open(f"dl/{k}.jpg").convert("RGB")
    if not k.startswith("g_"): im = autocrop(im)
    w, h = im.size; t = 16 / 9
    if w / h > t: nw = int(h * t); im = im.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
    else: nh = int(w / t); y0 = int((h - nh) * 0.4); im = im.crop((0, y0, w, y0 + nh))
    im = im.resize((680, 383), Image.LANCZOS).filter(ImageFilter.GaussianBlur(0.5)).resize((W, H), Image.BICUBIC)
    a = np.asarray(im).astype(np.float32) / 255
    L = a[..., 0] * .30 + a[..., 1] * .59 + a[..., 2] * .11
    lo, hi = np.percentile(L, 1), np.percentile(L, 99.5); L = np.clip((L - lo) / max(hi - lo, 0.1), 0, 1)
    L = L ** 0.95; L = 0.5 + (L - 0.5) * 0.84; L = 0.06 + L * 0.84
    hl = Image.fromarray((np.clip(L - 0.6, 0, 1) * 255 / 0.4).astype(np.uint8)).filter(ImageFilter.GaussianBlur(14))
    L = L + np.asarray(hl).astype(np.float32) / 255 * 0.08
    yy, xx = np.mgrid[0:H, 0:W] / np.array([H, W])[:, None, None]
    L = L * np.clip(1 - 0.35 * (((xx - .5) ** 2 * 1.1 + (yy - .5) ** 2 * 1.6) * 2.4), 0.5, 1)
    g = rng.normal(0, 1, (H // 2, W // 2)).astype(np.float32)
    g = np.asarray(Image.fromarray(((g * 40) + 128).clip(0, 255).astype(np.uint8)).resize((W, H), Image.BICUBIC)).astype(np.float32) / 255 - 0.5
    L = np.clip(L + g * 0.04, 0, 1)
    s = rng.choice([0.2, 0.4, 0.6])
    out = np.stack([L * (1 + 0.10 * s), L * (1 + 0.03 * s), L * (1 - 0.12 * s)], -1).clip(0, 1)
    Image.fromarray((out * 255).astype(np.uint8)).save(f"img/c_{k}.jpg", quality=90); return k
if __name__ == "__main__":
    os.makedirs("img", exist_ok=True)
    ks = open(__import__("sys").argv[1]).read().split(); ks = [k for k in ks if os.path.exists(f"dl/{k}.jpg")]
    with ProcessPoolExecutor(4) as ex: print(len(list(ex.map(proc, ks))))
