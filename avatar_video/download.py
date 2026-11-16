import json, os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
p = json.load(open("plan.json"))
ids = sorted({s["clip"] for s in p["scenes"]})
def get(i):
    out = f"clips/{i}.mp4"
    if os.path.exists(out) and os.path.getsize(out) > 10000: return
    for q in ("720", "1080", "360"):
        r = subprocess.run(["curl", "-sSf", "-m", "180", "-o", out + ".part", f"https://assets.mixkit.co/videos/{i}/{i}-{q}.mp4"])
        if r.returncode == 0:
            os.rename(out + ".part", out); return
    print("FAILED", i, flush=True); open("failed.txt", "a").write(f"{i}\n")
with ThreadPoolExecutor(6) as ex: list(ex.map(get, ids))
print("done", len(ids))
