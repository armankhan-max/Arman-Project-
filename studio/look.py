"""Every video gets its own 'look': fonts, colours, caption style, grade, transitions, camera moves,
music key and progression. Picked from the title + format with a seed, so two videos never look the
same, and fully editable afterwards in the editor."""
import hashlib
import random

FONTS = {  # ASS family name -> file in fonts/ (for thumbnails / PIL)
    "Inter ExtraBold": "Inter-ExtraBold.otf",
    "Anton": "Anton-Regular.ttf",
    "Bebas Neue": "BebasNeue-Regular.ttf",
    "Bangers": "Bangers-Regular.ttf",
    "Poppins": "Poppins-ExtraBold.ttf",
    "Archivo Black": "ArchivoBlack-Regular.ttf",
    "DejaVu Serif": "DejaVuSerif-Bold.ttf",
    "Liberation Sans": "LiberationSans-Bold.ttf",
}
FONT_FIT = {  # which fonts suit which mood
    "serious": ["Inter ExtraBold", "Archivo Black", "DejaVu Serif", "Liberation Sans", "Bebas Neue"],
    "bold": ["Anton", "Bebas Neue", "Archivo Black", "Poppins", "Inter ExtraBold"],
    "fun": ["Bangers", "Poppins", "Archivo Black", "Anton"],
    "calm": ["Poppins", "DejaVu Serif", "Liberation Sans", "Inter ExtraBold"],
}
PALETTES = ["#FFD400", "#FF8A3D", "#35E0A1", "#4FC3FF", "#FF3B5C", "#B98CFF", "#FFB347", "#7CFF6B", "#00E5FF", "#FF6EC7",
            "#F4D35E", "#E8C27A", "#9FB4FF", "#FF5E3A", "#2F80ED"]
CAPTION_STYLES = {
    "karaoke": "Word-by-word highlight",
    "single": "One big word at a time",
    "bar": "Subtitle bar",
    "classic": "Classic white subtitles",
    "boxed": "Highlighted word in a box",
}
FILTERS = {
    "none": "",
    "warm": "colorbalance=rs=0.08:gs=0.02:bs=-0.08",
    "cool": "colorbalance=rs=-0.06:gs=0.0:bs=0.1",
    "teal_orange": "colorbalance=rs=0.08:bs=-0.06:rh=-0.04:bh=0.08,eq=saturation=1.1",
    "vibrant": "eq=saturation=1.35:contrast=1.06",
    "muted": "eq=saturation=0.7:contrast=1.04",
    "bw": "hue=s=0,eq=contrast=1.12",
    "sepia": "colorchannelmixer=.393:.769:.189:0:.349:.686:.168:0:.272:.534:.131",
    "vintage": "curves=preset=vintage",
    "high_contrast": "eq=contrast=1.28:saturation=1.15",
    "dark_moody": "eq=brightness=-0.08:contrast=1.15:saturation=0.8,vignette=PI/3",
    "dreamy": "gblur=sigma=1.4,eq=brightness=0.05:saturation=1.1",
    "film_grain": "noise=alls=16:allf=t",
    "vignette": "vignette=PI/3.2",
    "night_vision": "hue=s=0,colorbalance=gs=0.4:rs=-0.2:bs=-0.2,noise=alls=12:allf=t",
}
GRADES = ["", "warm", "cool", "teal_orange", "vibrant", "muted", "high_contrast", "dark_moody"]
TRANSITIONS = ["cut", "fade", "fadeblack", "fadewhite", "dissolve", "slideleft", "slideright", "slideup", "smoothleft",
               "smoothright", "smoothup", "circleopen", "circleclose", "wipeleft", "wiperight", "zoomin", "radial",
               "hblur", "pixelize", "distance", "diagtl", "rectcrop"]
CALM_TRANS = ["fade", "dissolve", "fadeblack", "hblur", "distance"]
ENERGY_TRANS = ["slideleft", "smoothleft", "smoothright", "zoomin", "circleopen", "wipeleft", "slideup", "radial", "rectcrop", "diagtl"]
MOVES = ["push_in", "pull_out", "pan_left", "pan_right", "tilt_up", "diag", "orbit", "parallax", "zoom_punch", "static", "handheld"]
TITLE_STYLES = ["tag", "center_big", "lower_third", "none"]
FLAVORS = ["shot on 35mm film, natural grain", "aerial drone perspective where it fits", "macro close-up details", "golden hour light",
           "soft overcast light", "dramatic low-key lighting", "wide-angle lens, deep focus", "telephoto compression, shallow depth of field",
           "moody blue hour", "high-key bright and clean", "documentary handheld feel", "symmetrical composition"]


def mood_of(style_key, style):
    if style_key in ("animated", "stickman", "top10", "facts"):
        return "fun" if style_key in ("animated", "stickman") else "bold"
    if style_key in ("sleep", "motivation", "avatar", "avatar_captions"):
        return "calm"
    return "serious" if style_key in ("history", "documentary", "news", "mystery", "space_ocean") else "bold"


def generate(title, style_key, style, seed=None):
    seed = seed if seed is not None else int(hashlib.md5(f"{title}|{style_key}".encode()).hexdigest()[:8], 16)
    rnd = random.Random(seed)
    mood = mood_of(style_key, style)
    base_tr = [t for t in (style.get("transitions") or []) if t] or ["fade"]
    pool = list(dict.fromkeys(base_tr + (CALM_TRANS if mood in ("serious", "calm") else ENERGY_TRANS)))
    trans = rnd.sample(pool, k=min(len(pool), rnd.randint(3, 5)))
    if not any(style.get("transitions") or ["x"]):  # format wants hard cuts (avatar)
        trans = ["cut"]
    base_mv = style.get("moves") or MOVES
    extra = [m for m in MOVES if m not in ("handheld", "static") and m not in base_mv]
    moves = list(base_mv) + rnd.sample(extra, k=min(2, len(extra)))
    rnd.shuffle(moves)
    cap_choices = ["karaoke", "single", "bar", "boxed", "classic"] if mood in ("bold", "fun") else ["karaoke", "bar", "classic", "boxed"]
    return {
        "seed": seed,
        "font": rnd.choice(FONT_FIT[mood]),
        "accent": style.get("accent") if rnd.random() < 0.3 else rnd.choice(PALETTES),
        "caption_style": rnd.choice(cap_choices),
        "caption_pos": rnd.choice(["bottom", "bottom", "lower", "middle"]) if mood in ("bold", "fun") else "bottom",
        "grade": "" if style_key.startswith("avatar") else rnd.choice(GRADES),
        "transitions": trans,
        "moves": moves,
        "title_style": rnd.choice(TITLE_STYLES[:3]),
        "atmosphere": "none" if style_key in ("avatar", "avatar_captions", "stickman", "news") else rnd.choice(
            {"serious": ["dust", "dust", "fog", "light_leak", "none"], "calm": ["dust", "light_leak", "bokeh", "none"],
             "fun": ["none", "bokeh", "dust"], "bold": ["dust", "light_leak", "none", "embers"]}[mood]
            if style_key not in ("mystery", "sleep", "space_ocean") else {"mystery": ["fog", "dust", "rain"], "sleep": ["dust", "bokeh", "snow"],
                                                                          "space_ocean": ["dust", "bokeh", "fog"]}[style_key]),
        "living": True,
        "flavor": "" if style_key.startswith("avatar") or style_key == "stickman" else rnd.choice(FLAVORS),
        "music_seed": rnd.randint(0, 10 ** 6),
        "music_volume": None,
        "voice_volume": 1.0,
        "sfx_volume": 1.0,
    }


def font_file(name):
    return FONTS.get(name, "Inter-ExtraBold.otf")
