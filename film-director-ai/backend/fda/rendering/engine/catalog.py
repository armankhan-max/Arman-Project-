"""Everything the wizard lets you choose from: formats, looks, voices, motion graphics, music, captions."""

LANGUAGES = [
    ("en", "English"), ("hi", "Hindi"), ("hinglish", "Hinglish (Hindi in Latin script)"), ("es", "Spanish"), ("pt", "Portuguese"),
    ("fr", "French"), ("de", "German"), ("it", "Italian"), ("ar", "Arabic"), ("ur", "Urdu"), ("bn", "Bengali"),
    ("ta", "Tamil"), ("te", "Telugu"), ("mr", "Marathi"), ("gu", "Gujarati"), ("id", "Indonesian"), ("tr", "Turkish"),
    ("ru", "Russian"), ("ja", "Japanese"), ("ko", "Korean"), ("zh", "Chinese"), ("nl", "Dutch"), ("pl", "Polish"),
    ("vi", "Vietnamese"), ("th", "Thai"), ("fil", "Filipino"),
]
LANG_NAME = dict(LANGUAGES)
LANG_LOCALE = {"en": "en-US", "hi": "hi-IN", "hinglish": "hi-IN", "es": "es-MX", "pt": "pt-BR", "fr": "fr-FR", "de": "de-DE",
               "it": "it-IT", "ar": "ar-SA", "ur": "ur-PK", "bn": "bn-IN", "ta": "ta-IN", "te": "te-IN", "mr": "mr-IN",
               "gu": "gu-IN", "id": "id-ID", "tr": "tr-TR", "ru": "ru-RU", "ja": "ja-JP", "ko": "ko-KR", "zh": "zh-CN",
               "nl": "nl-NL", "pl": "pl-PL", "vi": "vi-VN", "th": "th-TH", "fil": "fil-PH"}

# ------------------------------------------------------------------ looks (themes)
# grade: sat, contrast, (r,g,b) gain, lift ; fonts: display, body, mono
THEMES = {
    "abyss": dict(name="Deep Abyss", desc="Dark teal sonar HUD, thin mono type. Ocean, war, deep-dive investigations.",
                  bg="#06121c", bg2="#0c2231", ink="#e9f3f7", dim="#7fa0ad", accent="#f29a2e", accent2="#45d0c1",
                  display="SpaceMono-Bold", body="Inter-Medium", mono="SpaceMono-Regular",
                  grade=(0.82, 1.12, (0.94, 1.02, 1.08), 0.01), grain=0.07, vignette=0.55, hud=True, bars=0.0,
                  transitions=["fade", "dip", "zoom", "glitch", "fade", "wipe"]),
    "casefile": dict(name="Case File", desc="Black, paper white and evidence red. True crime and investigations.",
                     bg="#101012", bg2="#1d1d21", ink="#f4f1ea", dim="#9a958b", accent="#d7263d", accent2="#f2c14e",
                     display="SpecialElite-Regular", body="Inter-Medium", mono="SpaceMono-Regular",
                     grade=(0.55, 1.2, (1.03, 0.99, 0.95), 0.0), grain=0.11, vignette=0.7, hud=False, bars=0.06,
                     transitions=["dip", "flash", "fade", "glitch", "push", "fade"]),
    "archive": dict(name="Old Archive", desc="Sepia film, serif titles, burn transitions. History and biographies.",
                    bg="#17120c", bg2="#2a2116", ink="#f3e9d2", dim="#a8987a", accent="#d9a441", accent2="#b5533c",
                    display="PlayfairDisplay", body="Inter-Medium", mono="SpecialElite-Regular",
                    grade=(0.6, 1.1, (1.07, 1.0, 0.88), 0.02), grain=0.12, vignette=0.65, hud=False, bars=0.0,
                    transitions=["burn", "fade", "dip", "fade", "zoom", "wipe"]),
    "clean": dict(name="Clean Explainer", desc="Bright, friendly, bold sans and color blocks. Explainers and education.",
                  bg="#f4f6fb", bg2="#e2e8f5", ink="#101828", dim="#5b6577", accent="#3b5bfd", accent2="#ff6b4a",
                  display="Poppins-ExtraBold", body="Poppins-Medium", mono="SpaceMono-Regular",
                  grade=(1.08, 1.04, (1.0, 1.0, 1.0), 0.0), grain=0.0, vignette=0.12, hud=False, bars=0.0,
                  transitions=["push", "wipe", "zoom", "fade", "slide", "pop"]),
    "neon": dict(name="Neon Tech", desc="Black glass with electric magenta and cyan. Tech, AI, gaming, future.",
                 bg="#07070d", bg2="#131325", ink="#f2f4ff", dim="#8a8fb3", accent="#00e5ff", accent2="#ff3df2",
                 display="ArchivoBlack-Regular", body="Inter-Medium", mono="SpaceMono-Regular",
                 grade=(1.15, 1.14, (0.97, 1.0, 1.1), 0.0), grain=0.04, vignette=0.5, hud=True, bars=0.0,
                 transitions=["glitch", "zoom", "push", "flash", "fade", "wipe"]),
    "earth": dict(name="Wild Earth", desc="Natural greens and warm light, calm motion. Nature, travel, food.",
                  bg="#0e1711", bg2="#1c2b20", ink="#f3f6ee", dim="#9fb09a", accent="#f4b942", accent2="#7ed087",
                  display="Montserrat", body="Inter-Medium", mono="SpaceMono-Regular",
                  grade=(1.12, 1.06, (1.03, 1.02, 0.95), 0.0), grain=0.03, vignette=0.35, hud=False, bars=0.0,
                  transitions=["fade", "fade", "zoom", "slide", "dip", "wipe"]),
    "gold": dict(name="Black & Gold", desc="Luxury black with gold serif. Money, business, power, biographies.",
                 bg="#0b0b0c", bg2="#1a1814", ink="#f6efe0", dim="#a39a85", accent="#e0b450", accent2="#ffffff",
                 display="Cinzel", body="Inter-Medium", mono="SpaceMono-Regular",
                 grade=(0.9, 1.15, (1.04, 1.0, 0.93), 0.0), grain=0.05, vignette=0.6, hud=False, bars=0.05,
                 transitions=["fade", "dip", "zoom", "wipe", "fade", "flash"]),
    "midnight": dict(name="Midnight Story", desc="Deep navy with rim-lit figures. 2D stories, what-if, mystery.",
                     bg="#0b1220", bg2="#16233a", ink="#eef4ff", dim="#8ea3c4", accent="#ffb347", accent2="#5bd6ff",
                     display="BebasNeue-Regular", body="Inter-Medium", mono="SpaceMono-Regular",
                     grade=(0.95, 1.1, (0.96, 1.0, 1.08), 0.0), grain=0.06, vignette=0.6, hud=False, bars=0.0,
                     transitions=["dip", "fade", "zoom", "push", "flash", "fade"]),
    "paper": dict(name="Notebook Paper", desc="Grid paper, taped photos, marker notes. Case studies and science.",
                  bg="#ecebe6", bg2="#d9d7cf", ink="#1b1b1f", dim="#6c6a63", accent="#d43d2a", accent2="#1f6feb",
                  display="PatrickHand-Regular", body="Inter-Medium", mono="SpecialElite-Regular",
                  grade=(0.98, 1.05, (1.0, 1.0, 0.98), 0.0), grain=0.04, vignette=0.2, hud=False, bars=0.0,
                  transitions=["slide", "push", "fade", "wipe", "pop", "fade"]),
    "home": dict(name="Warm Home", desc="Soft daylight, phone-camera feel, friendly labels. Avatar and lifestyle.",
                 bg="#1c1712", bg2="#2d251c", ink="#fff8ec", dim="#c2b39b", accent="#ffd23f", accent2="#ff7a59",
                 display="Anton-Regular", body="Inter-SemiBold", mono="SpaceMono-Regular",
                 grade=(1.06, 1.03, (1.03, 1.0, 0.96), 0.01), grain=0.03, vignette=0.22, hud=False, bars=0.0,
                 transitions=["cut", "cut", "fade", "zoom", "cut", "push"]),
    "horror": dict(name="Dread", desc="Crushed blacks, cold green, flicker. Horror, paranormal, dark mysteries.",
                   bg="#050706", bg2="#0f1512", ink="#dfe8e1", dim="#73857a", accent="#b3122a", accent2="#8fd3a8",
                   display="SpecialElite-Regular", body="Inter-Medium", mono="SpaceMono-Regular",
                   grade=(0.5, 1.28, (0.94, 1.03, 0.97), -0.01), grain=0.14, vignette=0.85, hud=False, bars=0.08,
                   transitions=["flash", "glitch", "dip", "fade", "dip", "zoom"]),
    "comic": dict(name="Pop Comic", desc="Loud colors, halftone, punchy captions. Kids, fun facts, countdowns.",
                  bg="#ffd23f", bg2="#ff9f1c", ink="#14110f", dim="#4a4035", accent="#e63946", accent2="#1d7cf2",
                  display="Bangers-Regular", body="Poppins-Bold", mono="SpaceMono-Bold",
                  grade=(1.2, 1.08, (1.0, 1.0, 1.0), 0.0), grain=0.0, vignette=0.1, hud=False, bars=0.0,
                  transitions=["pop", "push", "zoom", "slide", "wipe", "flash"]),
}

# ------------------------------------------------------------------ editing formats
# mix = default share of (stock video, real photo/archive, ai image, motion graphic)
FORMATS = {
    "documentary": dict(name="Cinematic Documentary", icon="film", theme="abyss", music="cinematic", captions="clean",
                        pace=4.5, mix=(0.3, 0.3, 0.25, 0.15), desc="Timeline-driven storytelling with maps, timestamps and archive footage."),
    "history": dict(name="History & Archive", icon="scroll", theme="archive", music="emotional", captions="clean",
                    pace=5.0, mix=(0.1, 0.5, 0.25, 0.15), desc="Old photographs, dates, maps and a slow, serious voice."),
    "truecrime": dict(name="True Crime / Case File", icon="search", theme="casefile", music="suspense", captions="clean",
                      pace=4.5, mix=(0.25, 0.3, 0.3, 0.15), desc="Evidence boards, timelines, locations and tension."),
    "last24": dict(name="Final 24 Hours", icon="clock", theme="casefile", music="suspense", captions="clean",
                   pace=4.5, mix=(0.25, 0.35, 0.2, 0.2), desc="Minute-by-minute reconstruction of one day, with clock cards and route maps."),
    "explainer": dict(name="Explainer", icon="bulb", theme="clean", music="upbeat", captions="highlight",
                      pace=4.0, mix=(0.3, 0.15, 0.25, 0.3), desc="Clear how-it-works videos with charts, lists and callouts."),
    "avatar": dict(name="AI Avatar (Talking Head)", icon="user", theme="home", music="warm", captions="highlight",
                   pace=4.5, mix=(0.35, 0.15, 0.4, 0.1), desc="A realistic host talks to camera (A-roll) with matching B-roll cut in."),
    "anim2d": dict(name="2D Animation (Stick Figures)", icon="pen", theme="midnight", music="curious", captions="pop",
                   pace=4.0, mix=(0.0, 0.0, 0.55, 0.45), desc="Rim-lit stick characters acting out the story over illustrated sets."),
    "listicle": dict(name="Top 10 / Countdown", icon="list", theme="comic", music="upbeat", captions="pop",
                     pace=3.8, mix=(0.4, 0.15, 0.25, 0.2), desc="Numbered cards, fast cuts, one idea per item."),
    "science": dict(name="Science & Space", icon="atom", theme="neon", music="ambient", captions="clean",
                    pace=4.5, mix=(0.3, 0.25, 0.25, 0.2), desc="Diagrams, scale comparisons and wonder."),
    "whatif": dict(name="What If…", icon="spark", theme="midnight", music="curious", captions="highlight",
                   pace=4.0, mix=(0.25, 0.1, 0.4, 0.25), desc="Hypothetical scenarios escalated step by step."),
    "biography": dict(name="Biography", icon="id", theme="gold", music="emotional", captions="clean",
                      pace=5.0, mix=(0.15, 0.45, 0.25, 0.15), desc="A life told through photos, quotes and milestones."),
    "finance": dict(name="Business & Money", icon="chart", theme="gold", music="tension", captions="highlight",
                    pace=4.0, mix=(0.35, 0.15, 0.2, 0.3), desc="Charts, numbers and company stories."),
    "tech": dict(name="Tech & AI", icon="chip", theme="neon", music="tension", captions="highlight",
                 pace=3.8, mix=(0.35, 0.1, 0.3, 0.25), desc="Product stories and future tech with a sharp look."),
    "mystery": dict(name="Mystery & Horror", icon="ghost", theme="horror", music="dark", captions="clean",
                    pace=5.0, mix=(0.25, 0.2, 0.45, 0.1), desc="Slow dread, flicker, unsettling stills."),
    "nature": dict(name="Nature & Travel", icon="leaf", theme="earth", music="ambient", captions="clean",
                   pace=5.0, mix=(0.6, 0.2, 0.15, 0.05), desc="Footage-first, calm pacing, place names and maps."),
    "motivation": dict(name="Motivational", icon="fire", theme="gold", music="epic", captions="pop",
                       pace=3.5, mix=(0.5, 0.1, 0.3, 0.1), desc="Big words on screen, rising music, strong footage."),
    "news": dict(name="News Report", icon="news", theme="neon", music="tension", captions="clean",
                 pace=4.0, mix=(0.4, 0.3, 0.1, 0.2), desc="Lower thirds, tickers, maps and stats."),
    "casestudy": dict(name="Case Study / Notebook", icon="book", theme="paper", music="curious", captions="highlight",
                      pace=4.5, mix=(0.15, 0.35, 0.25, 0.25), desc="Taped photos on grid paper, hand-drawn arrows and notes."),
    "kids": dict(name="Kids Story", icon="star", theme="comic", music="playful", captions="pop",
                 pace=4.5, mix=(0.0, 0.0, 0.8, 0.2), desc="Bright illustrated scenes with simple words."),
    "sports": dict(name="Sports Story", icon="ball", theme="neon", music="epic", captions="highlight",
                   pace=3.8, mix=(0.45, 0.25, 0.15, 0.15), desc="Careers, records and rivalries with stat cards."),
    "typography": dict(name="Kinetic Typography", icon="type", theme="clean", music="upbeat", captions="none",
                       pace=3.0, mix=(0.1, 0.0, 0.2, 0.7), desc="The words are the visuals: animated text, numbers and shapes."),
    "shorts": dict(name="Vertical Short (9:16)", icon="phone", theme="neon", music="upbeat", captions="pop",
                   pace=2.8, mix=(0.5, 0.1, 0.3, 0.1), desc="Under 60 seconds, big captions, very fast cuts.", aspect="9:16"),
}

MOTION_GRAPHICS = [
    ("title", "Chapter Title Card"), ("lower_third", "Lower Third / Name Tag"), ("stat", "Animated Number"),
    ("timeline", "Timeline"), ("bar_chart", "Bar Chart"), ("compare", "Comparison (A vs B)"),
    ("line_chart", "Line Chart"), ("ring", "Percentage Ring"), ("world_map", "World Map + Marker"),
    ("route_map", "Route / Conflict Map"), ("quote", "Quote Card"), ("list", "Step / List Cards"),
    ("callout", "Circle + Arrow Callout"), ("clock", "Time Stamp Card"), ("keywords", "Kinetic Keywords"),
    ("icon_grid", "Circle Icon Grid"), ("character_card", "Character Card"), ("document", "Document / Evidence"),
    ("counter", "Price / Count Badge"), ("diagram", "Labelled Diagram"), ("credits", "Sources & Credits"),
]

MOTIONS = ["push_in", "pull_out", "pan_left", "pan_right", "pan_up", "pan_down", "drift", "orbit", "tilt",
           "parallax", "focus_pull", "ramp_push", "handheld", "card", "polaroid", "split", "static"]
TRANSITIONS = ["cut", "fade", "dip", "flash", "zoom", "push", "slide", "wipe", "glitch", "burn", "pop"]
FILTERS = ["none", "cinematic", "bw", "sepia", "cold", "warm", "vivid", "faded", "noir", "dream"]

CAPTION_STYLES = [("clean", "Clean subtitles"), ("highlight", "Word highlight"), ("pop", "Big pop words"),
                  ("box", "Boxed lines"), ("none", "No captions")]

MUSIC_MOODS = [("cinematic", "Cinematic documentary"), ("suspense", "Suspense"), ("emotional", "Emotional piano"),
               ("ambient", "Atmospheric ambient"), ("tension", "Tension building"), ("upbeat", "Upbeat explainer"),
               ("curious", "Curious / playful marimba"), ("warm", "Warm & homely"), ("epic", "Epic rise"),
               ("dark", "Dark drone"), ("playful", "Kids / playful"), ("none", "No music")]

DURATIONS = [1, 3, 5, 8, 10, 12, 15, 20, 25, 30, 45, 60]

# ------------------------------------------------------------------ voices
# Free neural voices with hand-tuned delivery presets so each one sounds distinct.
# (id, label, base voice, gender, age, accent, style, rate%, pitchHz, description)
VOICES = [
    ("andrew_doc", "Andrew · Documentary", "en-US-AndrewMultilingualNeural", "male", "middle", "American", "narration", -4, -2, "Warm, confident, natural pauses. The safe pick for documentaries."),
    ("brian_calm", "Brian · Calm Storyteller", "en-US-BrianMultilingualNeural", "male", "middle", "American", "story", -6, -3, "Relaxed and sincere, like a late-night story."),
    ("ava_bright", "Ava · Expressive", "en-US-AvaMultilingualNeural", "female", "young", "American", "explainer", 0, 0, "Bright, caring and very human. Great for explainers."),
    ("emma_host", "Emma · Friendly Host", "en-US-EmmaMultilingualNeural", "female", "middle", "American", "host", -2, -1, "Cheerful, clear and conversational."),
    ("guy_trailer", "Marcus · Deep Trailer", "en-US-GuyNeural", "male", "middle", "American", "dramatic", -10, -14, "Low and heavy for crime, war and mystery."),
    ("chris_news", "Christopher · Authority", "en-US-ChristopherNeural", "male", "middle", "American", "news", -3, -6, "Reliable newsreader tone."),
    ("eric_coach", "Eric · Straight Talk", "en-US-EricNeural", "male", "middle", "American", "motivation", 2, -2, "Direct and rational, good for business and motivation."),
    ("roger_old", "Walter · Grandfather", "en-US-RogerNeural", "male", "old", "American", "avatar", -12, -16, "Slow, gravelly, lived-in. Old craftsman / farmer avatars."),
    ("steffan_teen", "Jake · Young Guy", "en-US-SteffanNeural", "male", "young", "American", "casual", 6, 8, "Quick and casual for gaming, tech and shorts."),
    ("andrew_teen", "Leo · Teen", "en-US-AndrewNeural", "male", "teen", "American", "casual", 8, 16, "Light, energetic teenage read."),
    ("jenny_soft", "Jenny · Soft Narrator", "en-US-JennyNeural", "female", "middle", "American", "narration", -5, -2, "Considerate and comforting."),
    ("aria_news", "Aria · Confident", "en-US-AriaNeural", "female", "middle", "American", "news", 0, -2, "Positive, crisp, newsroom-ready."),
    ("michelle_old", "Dorothy · Grandmother", "en-US-MichelleNeural", "female", "old", "American", "avatar", -13, -12, "Unhurried kitchen-table warmth for grandmother avatars."),
    ("ava_teen", "Mia · Teen Girl", "en-US-AvaNeural", "female", "teen", "American", "casual", 7, 14, "Young, upbeat and quick."),
    ("ana_kid", "Ana · Child", "en-US-AnaNeural", "female", "child", "American", "kids", 0, 0, "A real child voice for kids stories."),
    ("ryan_brit", "Oliver · British Documentary", "en-GB-RyanNeural", "male", "middle", "British", "narration", -6, -4, "Classic British nature-film gravitas."),
    ("thomas_brit", "Arthur · Old British", "en-GB-ThomasNeural", "male", "old", "British", "story", -11, -10, "Elderly, bookish, a little dry."),
    ("sonia_brit", "Charlotte · British", "en-GB-SoniaNeural", "female", "middle", "British", "narration", -4, -2, "Polished and calm."),
    ("libby_brit", "Lily · Young British", "en-GB-LibbyNeural", "female", "young", "British", "casual", 2, 4, "Friendly and modern."),
    ("maisie_kid", "Maisie · British Child", "en-GB-MaisieNeural", "female", "child", "British", "kids", 0, 0, "Storybook child voice."),
    ("william_au", "Jack · Australian", "en-AU-WilliamMultilingualNeural", "male", "middle", "Australian", "story", -3, -2, "Easygoing outdoors narrator."),
    ("natasha_au", "Ruby · Australian", "en-AU-NatashaNeural", "female", "middle", "Australian", "host", -2, 0, "Sunny and direct."),
    ("connor_ie", "Finn · Irish", "en-IE-ConnorNeural", "male", "middle", "Irish", "story", -4, -2, "Soft Irish lilt for folklore and travel."),
    ("emily_ie", "Niamh · Irish", "en-IE-EmilyNeural", "female", "middle", "Irish", "story", -4, 0, "Gentle and lyrical."),
    ("liam_ca", "Ethan · Canadian", "en-CA-LiamNeural", "male", "young", "Canadian", "explainer", 0, 0, "Neutral, clean, approachable."),
    ("clara_ca", "Clara · Canadian", "en-CA-ClaraNeural", "female", "middle", "Canadian", "explainer", -2, 0, "Clear teacher-like delivery."),
    ("luke_za", "Luke · South African", "en-ZA-LukeNeural", "male", "middle", "South African", "narration", -4, -4, "Distinct, grounded, good for wildlife."),
    ("prabhat_in", "Arjun · Indian English", "en-IN-PrabhatNeural", "male", "middle", "Indian", "explainer", -2, -2, "Clear Indian-English explainer."),
    ("neerja_in", "Priya · Indian English", "en-IN-NeerjaExpressiveNeural", "female", "young", "Indian", "host", 0, 0, "Expressive, lively Indian English."),
    ("madhur_hi", "Madhur · Hindi", "hi-IN-MadhurNeural", "male", "middle", "Hindi", "narration", -4, -2, "Natural Hindi narrator."),
    ("madhur_old", "Dadaji · Hindi Elder", "hi-IN-MadhurNeural", "male", "old", "Hindi", "story", -14, -18, "Slow, deep Hindi storyteller."),
    ("swara_hi", "Swara · Hindi", "hi-IN-SwaraNeural", "female", "young", "Hindi", "host", -2, 0, "Warm and clear Hindi female."),
    ("swara_old", "Dadi Maa · Hindi Elder", "hi-IN-SwaraNeural", "female", "old", "Hindi", "avatar", -14, -14, "Grandmotherly Hindi delivery."),
    ("jorge_mx", "Jorge · Mexican Spanish", "es-MX-JorgeNeural", "male", "middle", "Spanish", "narration", -4, -2, "Narrador mexicano cálido."),
    ("dalia_mx", "Dalia · Mexican Spanish", "es-MX-DaliaNeural", "female", "middle", "Spanish", "host", -2, 0, "Voz mexicana clara y cercana."),
    ("alvaro_es", "Álvaro · Spain", "es-ES-AlvaroNeural", "male", "middle", "Spanish", "narration", -3, -2, "Castellano serio."),
    ("antonio_br", "Antônio · Brazilian", "pt-BR-AntonioNeural", "male", "middle", "Portuguese", "narration", -3, -2, "Narrador brasileiro."),
    ("francisca_br", "Francisca · Brazilian", "pt-BR-FranciscaNeural", "female", "middle", "Portuguese", "host", -2, 0, "Voz brasileira amigável."),
    ("remy_fr", "Rémy · French", "fr-FR-RemyMultilingualNeural", "male", "middle", "French", "narration", -3, -2, "Narrateur français naturel."),
    ("vivienne_fr", "Vivienne · French", "fr-FR-VivienneMultilingualNeural", "female", "middle", "French", "host", -2, 0, "Voix française élégante."),
    ("florian_de", "Florian · German", "de-DE-FlorianMultilingualNeural", "male", "middle", "German", "narration", -3, -2, "Natürlicher deutscher Sprecher."),
    ("seraphina_de", "Seraphina · German", "de-DE-SeraphinaMultilingualNeural", "female", "middle", "German", "host", -2, 0, "Klare deutsche Stimme."),
    ("giuseppe_it", "Giuseppe · Italian", "it-IT-GiuseppeMultilingualNeural", "male", "middle", "Italian", "narration", -3, -2, "Narratore italiano."),
    ("hamed_ar", "Hamed · Arabic", "ar-SA-HamedNeural", "male", "middle", "Arabic", "narration", -3, -2, "Arabic narrator."),
    ("asad_ur", "Asad · Urdu", "ur-PK-AsadNeural", "male", "middle", "Urdu", "narration", -3, -2, "Urdu narrator."),
    ("uzma_ur", "Uzma · Urdu", "ur-PK-UzmaNeural", "female", "middle", "Urdu", "host", -2, 0, "Urdu female voice."),
    ("ardi_id", "Ardi · Indonesian", "id-ID-ArdiNeural", "male", "middle", "Indonesian", "narration", -2, -2, "Indonesian narrator."),
    ("keita_ja", "Keita · Japanese", "ja-JP-KeitaNeural", "male", "middle", "Japanese", "narration", -2, -2, "Japanese narrator."),
    ("nanami_ja", "Nanami · Japanese", "ja-JP-NanamiNeural", "female", "young", "Japanese", "host", 0, 0, "Japanese female voice."),
    ("dmitry_ru", "Dmitry · Russian", "ru-RU-DmitryNeural", "male", "middle", "Russian", "narration", -2, -2, "Russian narrator."),
    ("yunxi_zh", "Yunxi · Chinese", "zh-CN-YunxiNeural", "male", "young", "Chinese", "narration", 0, 0, "Mandarin narrator."),
    ("injoon_ko", "InJoon · Korean", "ko-KR-InJoonNeural", "male", "middle", "Korean", "narration", -2, -2, "Korean narrator."),
]
VOICE_KEYS = ["id", "name", "base", "gender", "age", "accent", "style", "rate", "pitch", "desc"]
MULTILINGUAL = {"en-US-AndrewMultilingualNeural", "en-US-BrianMultilingualNeural", "en-US-AvaMultilingualNeural",
                "en-US-EmmaMultilingualNeural", "en-AU-WilliamMultilingualNeural", "fr-FR-RemyMultilingualNeural",
                "fr-FR-VivienneMultilingualNeural", "de-DE-FlorianMultilingualNeural", "de-DE-SeraphinaMultilingualNeural",
                "it-IT-GiuseppeMultilingualNeural"}


def voice_list():
    return [dict(zip(VOICE_KEYS, v), provider="neural") for v in VOICES]


def voice_by_id(vid):
    for v in VOICES:
        if v[0] == vid:
            return dict(zip(VOICE_KEYS, v), provider="neural")
    return None


TIPS = [
    ("Write a prompt, not just a title", "Give the title, the angle, 3 to 6 beats you want covered and the feeling. The AI writes the script, but a clear brief gives a far better video."),
    ("The first 30 seconds decide everything", "Open inside the most dramatic moment. No greeting, no logo. Promise the payoff, then rewind."),
    ("One idea, one picture", "Every 4 to 5 seconds the picture should change. If a scene feels slow in the editor, split it and give the second half a new visual."),
    ("Mix your visual sources", "Real footage builds trust, archive photos give proof, AI images fill the gaps where no footage exists, and motion graphics explain numbers and places."),
    ("Let the music breathe", "Keep music about 20 dB under the voice. Drop it out completely before a big reveal, then bring it back."),
    ("Sound effects on the important moves only", "A whoosh on a transition, a hit on a title, a tick on a timestamp. Silence between them makes them land."),
    ("Thumbnails add to the title", "Use 2 to 4 words that the title does not say. One face or object, one arrow or circle, high contrast."),
    ("Check facts before you publish", "AI scripts can be wrong. Open the editor, read each scene, and fix anything you cannot confirm."),
    ("Tell YouTube when the host is AI", "For realistic avatar videos answer YES to 'Altered or synthetic content' when uploading."),
    ("Add free stock keys for real footage", "Add free Pexels and Pixabay keys in Owner Settings and the engine will cut in real, watermark-free stock video automatically."),
]
