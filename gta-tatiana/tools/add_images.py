#!/usr/bin/env python3
"""add_images.py <part number>: copies the channel owner's own images for that part into the part's
footage pack (parts/partNN/footage/images/) and adds a section about them to its README.md. Run after pack.py."""
import shutil, sys
from pathlib import Path
J = Path(__file__).resolve().parent.parent
IMG = J / "images"
D = {
 "img01": "Jason and Lucia back to back on a Vice City beach at sunset, duffel bags of cash, helicopter, boat",
 "img02": "A PS5 in a dark gamer room, the TV shows a storage bar and a red STORAGE FULL warning",
 "img03": "A man in aviators dropping a roll of cash into a trash bin on a neon Vice City street, police cars behind",
 "img04": "A sports car flying off a ramp on a neon palm-lined Vice City avenue at sunset",
 "img05": "A retro shop: a classic car in a glass case, a pink garage with a classic car, 80s outfits on mannequins",
 "img06": "A neon street at night: a car customization shop and a clothing store both LOCKED with glowing padlocks",
 "img07": "Vice City beach and skyline at sunset, neon art-deco hotels, crowds, cruise ships",
 "img08": "The Leonida Keys: a man on a boat looking at a dock bar, boats, sunset",
 "img09": "An aerial painted map of Leonida: neon city, swamp, sugar refinery, beaches, islands, mountains in the north",
 "img10": "A swamp at dawn: an alligator in the foreground, an airboat in the mangroves",
 "img11": "A worried man clutching his wallet at a run-down motel with a neon sign, empty parking lot",
 "img12": "A mountain cabin in pine woods, muddy road, pickups, a man peering out of a window",
 "img13": "Bikers on motorcycles outside a neon wolf bar, a burning sugar refinery behind",
 "img14": "A couple seen from behind on a rooftop at night holding hands, he looks at a phone message, neon city",
 "img15": "Split screen: Jason driving, Lucia leaning out of the car window aiming a pistol, police cars chasing",
 "img16": "A hooded man swapping clothes from a car trunk in a neon alley, a glowing star, a security camera",
 "img17": "A man with a bag running from police on a neon street: SIX stars above with jacket, car and camera icons",
 "img18": "Aerial night view of Vice City with a big red police search circle, a man hiding by a dumpster outside it",
 "img19": "An open car trunk: folded spare clothes, a cap, a white mask and a duffel bag, neon alley",
 "img21": "A convenience store robbery: masked robber aiming at the clerk, another filling a bag",
 "img22": "A man shooting a police car's tire (sparks) while officers take cover, sunny Vice City",
 "img23": "Split screen: a calm man in a suit walking out of a bank with a bag vs the same bank on fire with a getaway car",
 "img24": "A man picking a car lock in the rain, a glowing phone hacking app with a padlock, a gadget sparking",
 "img25": "A man running out of a bank with a bag full of cash, a glowing safe icon, a police car coming",
}
PARTS = {1: ["img01", "img04"], 2: ["img02"], 3: ["img05", "img06"], 4: ["img09", "img07", "img08"],
 5: ["img10", "img11", "img13", "img12"], 6: ["img09", "img04"], 7: ["img01", "img15"], 8: ["img14"],
 9: ["img17", "img21", "img16", "img19"], 10: ["img18", "img22"], 11: ["img23", "img03"], 12: ["img25", "img24"],
 13: ["img19"], 14: ["img16", "img04"], 15: ["img25", "img03", "img01"]}
n = int(sys.argv[1]); pack = J / "voice-video" / "parts" / f"part{n:02d}" / "footage"
pack.mkdir(parents=True, exist_ok=True); (pack / "images").mkdir(exist_ok=True)
rows = []
for k in PARTS[n]:
    shutil.copy2(IMG / f"{k}.jpg", pack / "images" / f"{k}.jpg")
    rows.append(f"| `images/{k}.jpg` | {D[k]} |")
txt = ("\n## The channel owner's own images (use every one of them in this part)\n\n"
 "Painted GTA 6 / Vice City style images the channel owner made for this video. Show each one where the voice "
 "talks about what it shows, full frame inside the letterbox bars, for about 1.5 to 3 s, with a slow push-in or "
 "pan (Ken Burns) and a short bold English label on top in the style (white, key word in coral). Cut them in among "
 "the footage and animation like footage shots. They are 1672x941: scale to cover 1920x960. Never draw over the "
 "faces. They are allowed to be reused across parts, but do not hold one longer than 3 s.\n\n"
 "| File | What it shows |\n|---|---|\n" + "\n".join(rows) + "\n")
r = pack / "README.md"
old = r.read_text() if r.exists() else "# Footage for this part\n"
if "channel owner's own images" not in old:
    r.write_text(old + txt)
print("images added:", ", ".join(PARTS[n]))
