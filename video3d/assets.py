"""Generate 2D textures used on 3D props (phone screen, generic banknote)."""
import os, math, random
from PIL import Image, ImageDraw, ImageFilter, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "assets")
F = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"

def screen(path, w=680, h=1460):
    im = Image.new("RGB", (w, h))
    px = im.load()
    for y in range(h):
        for x in range(w):
            t = y / h; u = x / w
            r = int(40 + 120 * (1 - t) * u + 60 * t)
            g = int(30 + 60 * (1 - u) * t)
            b = int(120 + 120 * (1 - t))
            px[x, y] = (min(255, r), g, min(255, b))
    im = im.filter(ImageFilter.GaussianBlur(2))
    d = ImageDraw.Draw(im)
    # soft blobs in wallpaper
    over = Image.new("RGBA", (w, h), (0, 0, 0, 0)); od = ImageDraw.Draw(over)
    od.ellipse((-200, 700, 500, 1400), fill=(255, 120, 200, 70)); od.ellipse((300, -100, 900, 500), fill=(90, 200, 255, 70))
    over = over.filter(ImageFilter.GaussianBlur(60)); im = Image.alpha_composite(im.convert("RGBA"), over)
    d = ImageDraw.Draw(im)
    fb = ImageFont.truetype(F, 150); fs = ImageFont.truetype(F, 34)
    d.text((w / 2, 230), "9:41", font=fb, fill=(255, 255, 255), anchor="mm")
    d.text((w / 2, 340), "Saturday, October 31", font=fs, fill=(235, 235, 255), anchor="mm")
    cols = [(255, 90, 90), (255, 190, 60), (80, 210, 120), (70, 160, 255), (180, 110, 255), (255, 120, 190),
            (60, 220, 220), (255, 150, 80), (120, 200, 90), (230, 230, 240), (90, 120, 255), (250, 80, 140)]
    s = 120; gap = (w - 4 * s) / 5
    for i, c in enumerate(cols):
        r_, cidx = divmod(i, 4)
        x = gap + cidx * (s + gap); y = 520 + r_ * (s + 70)
        d.rounded_rectangle((x, y, x + s, y + s), 30, fill=c)
        d.rounded_rectangle((x + 30, y + 30, x + s - 30, y + s - 30), 14, outline=(255, 255, 255), width=8)
    d.rounded_rectangle((40, h - 210, w - 40, h - 50), 50, fill=(255, 255, 255, 60))
    for i, c in enumerate([(80, 210, 120), (70, 160, 255), (255, 190, 60), (255, 90, 90)]):
        x = gap + i * (s + gap)
        d.rounded_rectangle((x, h - 190, x + s, h - 70), 30, fill=c)
    d.rounded_rectangle((w / 2 - 110, 22, w / 2 + 110, 72), 25, fill=(0, 0, 0))  # pill notch
    # rounded corners
    mask = Image.new("L", (w, h), 0); ImageDraw.Draw(mask).rounded_rectangle((0, 0, w, h), 70, fill=255)
    bg = Image.new("RGB", (w, h), (0, 0, 0)); bg.paste(im.convert("RGB"), mask=mask)
    bg.save(path)

def banknote(path, w=1560, h=660):
    rnd = random.Random(3)
    im = Image.new("RGB", (w, h), (196, 214, 180)); d = ImageDraw.Draw(im)
    for i in range(0, w, 6):
        d.line((i, 0, i + 80 * math.sin(i / 70), h), fill=(180, 200, 165), width=1)
    d.rectangle((30, 30, w - 30, h - 30), outline=(40, 80, 60), width=10)
    d.rectangle((52, 52, w - 52, h - 52), outline=(70, 110, 80), width=3)
    d.ellipse((w / 2 - 210, h / 2 - 230, w / 2 + 210, h / 2 + 230), fill=(170, 195, 160), outline=(40, 80, 60), width=8)
    for k in range(18):
        a = k / 18 * 2 * math.pi
        d.ellipse((w / 2 + 150 * math.cos(a) - 40, h / 2 + 170 * math.sin(a) - 40, w / 2 + 150 * math.cos(a) + 40, h / 2 + 170 * math.sin(a) + 40), outline=(60, 100, 70), width=3)
    f = ImageFont.truetype(F, 200); f2 = ImageFont.truetype(F, 60)
    d.text((w / 2, h / 2), "1", font=ImageFont.truetype(F, 300), fill=(40, 80, 60), anchor="mm")
    for (x, y) in ((150, 140), (w - 150, 140), (150, h - 140), (w - 150, h - 140)):
        d.text((x, y), "1", font=f, fill=(40, 80, 60), anchor="mm")
    d.text((w / 2, 90), "ONE", font=f2, fill=(40, 80, 60), anchor="mm")
    d.text((w / 2, h - 90), "MONEY NOTE", font=f2, fill=(40, 80, 60), anchor="mm")
    im = im.filter(ImageFilter.GaussianBlur(0.8))
    # grime
    over = Image.new("RGBA", (w, h), (0, 0, 0, 0)); od = ImageDraw.Draw(over)
    for _ in range(40):
        x, y, r = rnd.randint(0, w), rnd.randint(0, h), rnd.randint(20, 120)
        od.ellipse((x - r, y - r, x + r, y + r), fill=(90, 80, 40, rnd.randint(10, 35)))
    over = over.filter(ImageFilter.GaussianBlur(25))
    Image.alpha_composite(im.convert("RGBA"), over).convert("RGB").save(path)

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    screen(os.path.join(OUT, "screen.png")); banknote(os.path.join(OUT, "bill.png")); print("ok")
