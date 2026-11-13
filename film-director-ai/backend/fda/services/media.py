"""FFmpeg/ffprobe helpers. Only fixed argument lists are executed; nothing from an LLM reaches a shell."""
import json
import re
import subprocess

from fda.config import get_settings


class MediaError(RuntimeError):
    pass


def run(args, timeout=None):
    p = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
    if p.returncode != 0:
        raise MediaError("%s failed: %s" % (args[0], p.stderr.decode("utf-8", "ignore")[-800:]))
    return p


def probe(path) -> dict:
    s = get_settings()
    try:
        p = run([s.ffprobe_bin, "-v", "error", "-print_format", "json", "-show_format", "-show_streams", path], timeout=60)
    except MediaError as e:
        raise MediaError("Unreadable or corrupted media file") from e
    j = json.loads(p.stdout.decode() or "{}")
    fmt = j.get("format") or {}
    out = {"duration": float(fmt.get("duration") or 0), "format": fmt.get("format_name", ""), "size": int(fmt.get("size") or 0), "video": None, "audio": None}
    for st in j.get("streams", []):
        if st.get("codec_type") == "video" and out["video"] is None and st.get("disposition", {}).get("attached_pic") != 1:
            fr = st.get("avg_frame_rate") or st.get("r_frame_rate") or "0/1"
            try:
                a, b = fr.split("/")
                fps = float(a) / float(b) if float(b) else 0
            except Exception:
                fps = 0
            out["video"] = {"codec": st.get("codec_name"), "width": st.get("width"), "height": st.get("height"), "fps": round(fps, 3),
                            "frames": int(st.get("nb_frames") or 0), "pix_fmt": st.get("pix_fmt")}
        if st.get("codec_type") == "audio" and out["audio"] is None:
            out["audio"] = {"codec": st.get("codec_name"), "sample_rate": int(st.get("sample_rate") or 0), "channels": st.get("channels")}
    return out


def detect(path, video=True, audio=True, duration=None):
    """Black frames, frozen frames, silences and peak level in one decode pass each."""
    s = get_settings()
    res = {"black": [], "freeze": [], "silence": [], "peak_db": None, "integrated_lufs": None}
    if video:
        p = subprocess.run([s.ffmpeg_bin, "-v", "info", "-i", path, "-an", "-vf", "fps=6,scale=320:-2,blackdetect=d=0.4:pix_th=0.06,freezedetect=n=0.002:d=3",
                            "-f", "null", "-"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=3600)
        log = p.stderr.decode("utf-8", "ignore")
        for m in re.finditer(r"black_start:([\d.]+) black_end:([\d.]+)", log):
            res["black"].append([float(m.group(1)), float(m.group(2))])
        starts = [float(x) for x in re.findall(r"freeze_start: ([\d.]+)", log)]
        ends = [float(x) for x in re.findall(r"freeze_end: ([\d.]+)", log)]
        for i, st in enumerate(starts):
            res["freeze"].append([st, ends[i] if i < len(ends) else duration or st])
    if audio:
        p = subprocess.run([s.ffmpeg_bin, "-v", "info", "-i", path, "-vn", "-af", "silencedetect=n=-45dB:d=1.5,astats=metadata=0:reset=0,ebur128=peak=true",
                            "-f", "null", "-"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=3600)
        log = p.stderr.decode("utf-8", "ignore")
        st = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", log)]
        en = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", log)]
        for i, a in enumerate(st):
            res["silence"].append([max(0.0, a), en[i] if i < len(en) else duration or a])
        pk = re.findall(r"Peak level dB: (-?[\d.]+|-inf)", log)
        if pk:
            vals = [float(x) for x in pk if x != "-inf"]
            res["peak_db"] = max(vals) if vals else None
        m = re.findall(r"I:\s+(-?[\d.]+) LUFS", log)
        if m:
            res["integrated_lufs"] = float(m[-1])
    return res
