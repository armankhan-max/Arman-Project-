import sys, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
src = sys.argv[1]; out = sys.argv[2]
W, H = 1920, 1080
im = cv2.imread(src, cv2.IMREAD_GRAYSCALE).astype(np.float32) / 255
h, w = im.shape; s = max(W / w, H / h)
im = cv2.resize(im, (int(w * s) + 1, int(h * s) + 1), interpolation=cv2.INTER_CUBIC)
y0 = (im.shape[0] - H) // 2; x0 = (im.shape[1] - W) // 2
im = im[y0:y0 + H, x0:x0 + W]
lo, hi = np.percentile(im, [1, 99.5]); im = np.clip((im - lo) / (hi - lo), 0, 1)
im = np.clip((im - 0.5) * 1.15 + 0.5, 0, 1)
bl = cv2.GaussianBlur(im, (0, 0), 2.5); im = np.clip(im + 0.6 * (im - bl), 0, 1)
v = np.arange(256) / 255
rgb = np.stack([im * 0.95 + 0.05, im * 0.87 + 0.03, im * 0.72 + 0.02], -1)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
vig = 1 - 0.5 * np.clip(np.sqrt(((xx - W / 2) / W) ** 2 + ((yy - H / 2) / H) ** 2) * 1.7 - 0.25, 0, 1)
rgb *= vig[..., None]
rgb += np.random.default_rng(1).normal(0, 0.025, (H, W, 1))
img = Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8))
f = ImageFont.truetype("fonts/Playfair.ttf", 250)
try: f.set_variation_by_name("Black")
except Exception: pass
txt = "1934"
d = ImageDraw.Draw(img)
tx, ty = W // 2, H - 60
sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ds = ImageDraw.Draw(sh)
ds.text((tx + 8, ty + 10), txt, font=f, fill=(0, 0, 0, 230), anchor="ms")
sh = sh.filter(ImageFilter.GaussianBlur(14))
img = img.convert("RGBA"); img.alpha_composite(sh)
d = ImageDraw.Draw(img)
d.text((tx, ty), txt, font=f, fill=(250, 244, 230), anchor="ms", stroke_width=6, stroke_fill=(20, 16, 12))
img = img.convert("RGB")
img.save(out, quality=94)
img.resize((1280, 720), Image.LANCZOS).save(out.replace(".jpg", "_1280x720.jpg"), quality=92)
print(out)
