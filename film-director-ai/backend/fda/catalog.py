"""Production modes, looks and creative vocabularies shared by the agents and the UI."""
from fda.rendering.engine import catalog as eng

LOOKS = {k: {"name": v["name"], "desc": v["desc"], "bg": v["bg"], "accent": v["accent"], "accent2": v["accent2"], "ink": v["ink"]} for k, v in eng.THEMES.items()}

# visual preference: what the storyboard agent should favour for this mode (it still chooses per scene)
MODES = {
    "documentary": dict(name="Cinematic documentary", look="abyss", music="cinematic", captions="clean", pace=4.5,
                        prefer=["stock_video", "archive", "ai_image", "motion_graphic", "blender", "ai_video"]),
    "historical": dict(name="Historical documentary", look="archive", music="emotional", captions="clean", pace=5.0,
                       prefer=["archive", "stock_video", "motion_graphic", "ai_image"]),
    "faceless": dict(name="Faceless narration", look="midnight", music="ambient", captions="highlight", pace=4.0,
                     prefer=["stock_video", "ai_image", "motion_graphic", "archive"]),
    "educational": dict(name="Educational explainer", look="clean", music="curious", captions="highlight", pace=4.0,
                        prefer=["motion_graphic", "stock_video", "ai_image", "blender"]),
    "science": dict(name="Science & technology", look="neon", music="ambient", captions="clean", pace=4.5,
                    prefer=["blender", "stock_video", "motion_graphic", "ai_image", "archive", "ai_video"]),
    "realistic": dict(name="Realistic cinematic", look="earth", music="cinematic", captions="clean", pace=5.0,
                      prefer=["ai_video", "stock_video", "ai_image"]),
    "avatar": dict(name="AI avatar host", look="home", music="warm", captions="highlight", pace=4.5,
                   prefer=["avatar", "ai_image", "motion_graphic"]),
    "anim2d": dict(name="2D animation", look="midnight", music="curious", captions="pop", pace=4.0, prefer=["ai_image", "motion_graphic"]),
    "blender3d": dict(name="Blender 3D animation", look="neon", music="ambient", captions="clean", pace=5.0, prefer=["blender", "motion_graphic"]),
    "motion_graphics": dict(name="2D motion graphics", look="clean", music="upbeat", captions="highlight", pace=3.5, prefer=["motion_graphic", "ai_image"]),
    "hybrid": dict(name="Hybrid (Director chooses per scene)", look="abyss", music="cinematic", captions="clean", pace=4.5,
                   prefer=["stock_video", "blender", "archive", "motion_graphic", "ai_image", "ai_video", "avatar"]),
    "short": dict(name="Short (vertical)", look="neon", music="upbeat", captions="pop", pace=2.8, prefer=["stock_video", "ai_image", "motion_graphic"]),
}

MOVEMENTS = ["static", "push_in", "pull_out", "pan_left", "pan_right", "tilt_up", "tilt_down", "tracking", "orbit", "handheld", "drone", "dolly_zoom", "crane"]
# how a camera direction is realised on a still or footage in the compositor
MOVE_TO_ENGINE = {"static": "static", "push_in": "push_in", "pull_out": "pull_out", "pan_left": "pan_left", "pan_right": "pan_right", "tilt_up": "pan_up",
                  "tilt_down": "pan_down", "tracking": "drift", "orbit": "orbit", "handheld": "handheld", "drone": "pull_out", "dolly_zoom": "ramp_push",
                  "crane": "pan_up"}
TRANSITIONS = eng.TRANSITIONS
CAPTION_STYLES = [c[0] for c in eng.CAPTION_STYLES]
MUSIC_MOODS = [mm[0] for mm in eng.MUSIC_MOODS]
MG_TYPES = [t for t, _ in eng.MOTION_GRAPHICS]
LANGUAGES = {"en": "English", "hi": "Hindi", "hinglish": "Hinglish"}
DEFAULT_VOICES = {"en": "en-US-AndrewMultilingualNeural", "hi": "hi-IN-MadhurNeural", "hinglish": "hi-IN-MadhurNeural"}
RESOLUTIONS = {"16:9": [(1920, 1080), (1280, 720), (3840, 2160)], "9:16": [(1080, 1920), (720, 1280)], "1:1": [(1080, 1080), (720, 720)]}


def default_style(mode, language="en"):
    md = MODES.get(mode) or MODES["documentary"]
    return {"look": md["look"], "music": md["music"], "music_volume": 0.5, "sfx": True, "sfx_volume": 0.7, "captions": md["captions"], "pace": md["pace"],
            "voice": DEFAULT_VOICES.get(language, DEFAULT_VOICES["en"]), "voice_rate": -4, "voice_pitch": -2, "voice_enhance": True,
            "sources": {"stock_video": True, "stock_image": True, "archive": True, "ai_image": True, "ai_video": False, "blender": True, "avatar": mode == "avatar"},
            "blocklist": "", "aspect": "9:16" if mode == "short" else "16:9", "avatar_image_asset": None}
