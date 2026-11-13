"""Blender 3D Agent: validated parameters → fixed template script → headless Cycles render → MP4 + .blend."""
import json
import os
import re
import shutil
import subprocess
import threading
import time

from fda.config import get_settings
from fda.providers.base import ProviderError
from fda.services import assets
from fda.storage.store import scratch_dir

_one_at_a_time = threading.Semaphore(1)  # Blender already uses every core; parallel renders only thrash
SCRIPT = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tools", "blender", "scene_builder.py")
FRAME = re.compile(r"^Fra:(\d+) ")
HEX = re.compile(r"^#[0-9a-fA-F]{6}$")
MOVES = ("orbit", "push_in", "pull_out", "flyby")
TEMPLATES = {
    "planet": {"desc": "a planet or moon", "params": {"color": "hex", "color2": "hex", "bands": (1, 40), "rings": "bool", "ring_color": "hex", "atmosphere": "bool", "atmo_color": "hex", "sun": (0.5, 10)}},
    "solar_system": {"desc": "a star with orbiting planets", "params": {"planets": (2, 8)}},
    "black_hole": {"desc": "a black hole with an accretion disk", "params": {"color": "hex"}},
    "molecule": {"desc": "a ball-and-stick molecule", "params": {"atoms": "atoms"}},
    "dna": {"desc": "a rotating DNA double helix", "params": {"color": "hex", "color2": "hex"}},
    "terrain": {"desc": "a landscape flyover", "params": {"color": "hex", "color2": "hex", "height": (0.5, 8), "background": "hex", "sun_color": "hex"}},
    "title3d": {"desc": "3D extruded title text", "params": {"text": "text"}},
}


def available():
    return bool(shutil.which(get_settings().blender_bin))


def template_doc():
    return "; ".join("%s (%s; params %s; move one of %s)" % (k, v["desc"], ", ".join(v["params"]), "/".join(MOVES)) for k, v in TEMPLATES.items())


def clean_params(template, params):
    if template not in TEMPLATES:
        raise ProviderError("Unknown Blender template '%s'" % template, retryable=False)
    spec = TEMPLATES[template]["params"]
    out = {}
    for k, v in (params or {}).items():
        t = spec.get(k)
        if t == "hex" and isinstance(v, str) and HEX.match(v):
            out[k] = v
        elif t == "bool":
            out[k] = bool(v)
        elif isinstance(t, tuple):
            try:
                out[k] = max(t[0], min(t[1], float(v)))
            except (TypeError, ValueError):
                pass
        elif t == "text":
            out[k] = re.sub(r"[^\w .,!?'-]", "", str(v))[:40]
        elif t == "atoms" and isinstance(v, list):
            atoms = []
            for a in v[:60]:
                if isinstance(a, (list, tuple)) and len(a) == 4 and str(a[0]).isalpha():
                    try:
                        atoms.append([str(a[0])[:2], float(a[1]), float(a[2]), float(a[3])])
                    except (TypeError, ValueError):
                        pass
            if atoms:
                out[k] = atoms
    mv = (params or {}).get("move")
    if mv in MOVES:
        out["move"] = mv
    return out


def render(db, project_id, template, params, duration, width=1280, height=720, fps=24, samples=None, seed=1, timeout=3000, engine=None, progress=None):
    engine = engine or os.environ.get("FDA_BLENDER_ENGINE", "EEVEE")
    s = get_settings()
    if not available():
        raise ProviderError("Blender is not installed or not on PATH (FDA_BLENDER_BIN)", retryable=False, code="not_configured")
    work = scratch_dir(project_id, "blender", "%s_%d" % (template, seed))
    P = dict(clean_params(template, params), engine=engine, template=template, duration=max(1.0, min(30.0, float(duration))), width=int(width), height=int(height), fps=int(fps),
             samples=int(samples or (32 if engine == "EEVEE" else 28)), seed=int(seed), out=os.path.join(work, "render.mp4"), blend=os.path.join(work, "scene.blend"))
    pj = os.path.join(work, "params.json")
    json.dump(P, open(pj, "w"))
    scale = float(os.environ.get("FDA_BLENDER_SCALE", "0.75"))
    P["width"], P["height"] = int(width * scale) // 2 * 2, int(height * scale) // 2 * 2
    json.dump(P, open(pj, "w"))
    nframes = max(2, int(round(P["fps"] * P["duration"])))
    log, t0, last = [], time.time(), [-1]
    with _one_at_a_time:
        proc = subprocess.Popen([s.blender_bin, "-b", "--factory-startup", "-noaudio", "-P", SCRIPT, "--", pj], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                env=dict(os.environ, BLENDER_USER_SCRIPTS=work), text=True, errors="ignore")
        try:
            for line in proc.stdout:
                log.append(line)
                del log[:-80]
                m_ = FRAME.match(line)
                if m_ and progress and int(m_.group(1)) != last[0]:
                    last[0] = int(m_.group(1))
                    progress(min(0.99, int(m_.group(1)) / nframes), "Blender %s: frame %s/%d (%s)" % (template, m_.group(1), nframes, P["engine"]))
                if time.time() - t0 > timeout:
                    proc.kill()
                    raise ProviderError("Blender render timed out after %ds" % timeout, retryable=True, code="timeout")
        finally:
            proc.wait()

    class R:
        returncode = proc.returncode
        stdout = "".join(log).encode()
    r = R()
    outp = P["out"]
    if not os.path.exists(outp):  # Blender appends frame range to FFMPEG output names
        cands = [os.path.join(work, f) for f in os.listdir(work) if f.startswith("render") and f.endswith(".mp4")]
        outp = cands[0] if cands else outp
    if (r.returncode != 0 or not os.path.exists(outp) or os.path.getsize(outp) < 2000) and engine == "EEVEE":
        # EEVEE needs an OpenGL context; fall back to CPU path tracing when the machine cannot provide one
        return render(db, project_id, template, params, duration, width, height, fps, None, seed, timeout, engine="CYCLES", progress=progress)
    if r.returncode != 0 or not os.path.exists(outp) or os.path.getsize(outp) < 2000:
        raise ProviderError("Blender render failed: %s" % r.stdout.decode("utf-8", "ignore")[-700:], retryable=True)
    vid = assets.register(db, outp, project_id, "scene", "blender", "blender_%s.mp4" % template, origin="blender", provider="blender",
                          settings={k: v for k, v in P.items() if k not in ("out", "blend")}, license="Original render (own work)", commercial_use="yes")
    blend = assets.register(db, P["blend"], project_id, "blender_project", "blender", "%s.blend" % template, origin="blender", provider="blender",
                            settings={"template": template}, license="Own work", commercial_use="yes", parent_id=vid.id, kind="blend")
    return vid, blend
