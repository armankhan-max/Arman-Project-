"""Editing-style reference: study a reference video (uploaded file) and/or its transcript, and turn it
into settings the studio can follow: pace, shot length, cut style, colour, script voice and structure.
The result is a style guide that inspires the new video. It never copies the reference."""
import json
import re
import subprocess

import numpy as np

import llm


def _run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def analyse_video(path, max_seconds=600):
    dur = 0.0
    r = _run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=width,height", "-of", "json", path])
    try:
        j = json.loads(r.stdout)
        dur = float(j["format"]["duration"])
        st = next(s for s in j["streams"] if s.get("width"))
        w, h = st["width"], st["height"]
    except Exception:
        w, h = 16, 9
    span = min(dur, max_seconds) or max_seconds
    # hard cuts: big frame differences
    r = _run(["ffmpeg", "-v", "info", "-t", str(span), "-i", path, "-vf", "scale=160:-2,select='gt(scene,0.25)',showinfo", "-an", "-f", "null", "-"])
    cuts = [float(m) for m in re.findall(r"pts_time:([\d.]+)", r.stderr)]
    # soft transitions: medium differences that are not hard cuts
    r2 = _run(["ffmpeg", "-v", "info", "-t", str(span), "-i", path, "-vf", "scale=160:-2,select='between(scene,0.12,0.25)',showinfo", "-an", "-f", "null", "-"])
    soft = len(re.findall(r"pts_time:", r2.stderr))
    # colour: average brightness / saturation of sampled frames
    lum = sat = 0.5
    warm = 0.0
    raw = subprocess.run(["ffmpeg", "-v", "error", "-t", str(span), "-i", path, "-vf", "fps=1/4,scale=64:36", "-f", "rawvideo",
                          "-pix_fmt", "rgb24", "-"], capture_output=True)
    arr = np.frombuffer(raw.stdout, np.uint8)
    if len(arr) >= 3:
        px = arr[: len(arr) // 3 * 3].reshape(-1, 3).astype(np.float32) / 255
        mx, mn = px.max(1), px.min(1)
        lum = float(px.mean())
        sat = float(((mx - mn) / (mx + 1e-6)).mean())
        warm = float((px[:, 0] - px[:, 2]).mean())
    shot = span / (len(cuts) + 1) if span else 5
    return {"duration": round(dur, 1), "aspect": "9:16" if h > w else "16:9", "avg_shot_seconds": round(shot, 1),
            "cuts_per_minute": round(len(cuts) / max(span, 1) * 60, 1), "soft_transition_ratio": round(soft / max(1, soft + len(cuts)), 2),
            "brightness": round(lum, 2), "saturation": round(sat, 2), "warmth": round(warm, 3)}


def analyse_script(transcript, cfg, duration=None):
    words = transcript.split()
    sents = [s for s in re.split(r"(?<=[.!?])\s+", transcript) if s.strip()]
    stats = {"words": len(words), "avg_sentence_words": round(len(words) / max(1, len(sents)), 1),
             "second_person": round(sum(w.lower() in ("you", "your", "you're") for w in words) / max(1, len(words)) * 100, 2),
             "numbers_per_100_words": round(sum(bool(re.search(r"\d", w)) for w in words) / max(1, len(words)) * 100, 2),
             "questions": sum(s.strip().endswith("?") for s in sents)}
    if duration:
        stats["words_per_minute"] = round(len(words) / max(duration, 1) * 60)
    summary = ""
    if llm.provider(cfg) != "none" and len(words) > 40:
        try:
            o = llm._json(llm.chat(cfg, "You analyse YouTube narration style. Return ONLY one JSON object.",
                                   "Study the STYLE of this narration (not its facts) and return "
                                   '{"summary": "2 sentences", "mood": "...", "voice_and_tone": "...", "address": "how it speaks to the viewer", '
                                   '"vocabulary": "...", "structure": "how it opens, builds and ends", "hooks": "techniques that keep people watching", '
                                   '"verbal_signature": "recurring phrasing patterns, described not quoted"}\n\n' + transcript[:9000], 1500))
            summary = o
        except Exception:
            summary = ""
    return stats, summary


def to_settings(video=None, script_stats=None, script_style=None):
    """Turn the analysis into studio settings."""
    out, hints = {}, []
    if video:
        out["shot_seconds"] = max(2.0, min(10.0, video["avg_shot_seconds"]))
        out["transitions"] = ["fade", "dissolve", "fadeblack"] if video["soft_transition_ratio"] > 0.35 else [""]
        grade = []
        if video["brightness"] < 0.32:
            grade.append("eq=brightness=-0.05:contrast=1.12")
        if video["saturation"] < 0.25:
            grade.append("eq=saturation=0.75")
        elif video["saturation"] > 0.45:
            grade.append("eq=saturation=1.2")
        if video["warmth"] > 0.06:
            grade.append("colorbalance=rs=0.06:bs=-0.05")
        elif video["warmth"] < -0.04:
            grade.append("colorbalance=rs=-0.04:bs=0.08")
        out["grade"] = ",".join(grade)
        hints.append(f"Pacing: about {video['cuts_per_minute']} cuts per minute.")
    if script_stats:
        if script_stats.get("words_per_minute"):
            out["words_per_minute"] = max(110, min(190, script_stats["words_per_minute"]))
        hints.append(f"Sentences average {script_stats['avg_sentence_words']} words.")
    if isinstance(script_style, dict):
        hints.append("Match this narration style (inspired by a reference, never copy its wording): "
                     + "; ".join(f"{k.replace('_', ' ')}: {v}" for k, v in script_style.items() if v and k != "summary"))
    out["script_hint"] = " ".join(hints)
    return out
