"""A-roll lip-sync. Lip-sync needs a paid avatar service; D-ID is supported here.
Without a key the host picture is shown as a still with a slow camera move.
NOTE: the D-ID path follows their public REST docs but has not been run against a live account yet."""
import os
import time

import requests

API = "https://api.d-id.com"


def lipsync(cfg, image_path, audio_path, out_path, log=lambda m: None):
    """Returns out_path with a talking-head clip, or None to fall back to the still picture."""
    if cfg.get("lipsync_provider") != "d-id" or not cfg.get("did_key") or not os.path.exists(audio_path):
        return None
    if os.path.exists(out_path):
        return out_path
    try:
        h = {"Authorization": "Basic " + cfg["did_key"], "accept": "application/json"}
        with open(image_path, "rb") as f:
            img = requests.post(API + "/images", headers=h, files={"image": (os.path.basename(image_path), f)}, timeout=120)
        img.raise_for_status()
        with open(audio_path, "rb") as f:
            aud = requests.post(API + "/audios", headers=h, files={"audio": (os.path.basename(audio_path), f, "audio/mpeg")}, timeout=120)
        aud.raise_for_status()
        talk = requests.post(API + "/talks", headers=h, timeout=120, json={
            "source_url": img.json()["url"], "script": {"type": "audio", "audio_url": aud.json()["url"]},
            "config": {"stitch": True}})
        talk.raise_for_status()
        tid = talk.json()["id"]
        for _ in range(150):
            time.sleep(4)
            j = requests.get(f"{API}/talks/{tid}", headers=h, timeout=60).json()
            if j.get("status") == "done":
                with requests.get(j["result_url"], timeout=300, stream=True) as r, open(out_path, "wb") as f:
                    for chunk in r.iter_content(1 << 16):
                        f.write(chunk)
                return out_path
            if j.get("status") in ("error", "rejected"):
                raise RuntimeError(str(j)[:200])
        raise RuntimeError("timed out")
    except Exception as e:
        log(f"  Lip-sync failed, using the still host picture instead: {str(e)[:160]}")
        return None
