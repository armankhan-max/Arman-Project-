#!/usr/bin/env python3
"""Word-level transcript of a voiceover (faster-whisper small.en, CPU).

    pip install faster-whisper
    python3 tools/transcribe.py voice.mp3 out_dir
Writes out_dir/transcript.txt ([start-end] sentence) and out_dir/transcript.json (with word times).
Use these ORIGINAL times in project.py / text_cues.py.
"""
import json, subprocess, sys
import numpy as np
from faster_whisper import WhisperModel

src, out = sys.argv[1], sys.argv[2]
raw = subprocess.check_output(["ffmpeg", "-v", "error", "-i", src, "-f", "s16le", "-ac", "1", "-ar", "16000", "-"])
audio = np.frombuffer(raw, np.int16).astype(np.float32) / 32768   # avoids the PyAV open() bug
m = WhisperModel("small.en", device="cpu", compute_type="int8", cpu_threads=4)
segs, _ = m.transcribe(audio, word_timestamps=True)
rows, lines = [], []
for s in segs:
    rows.append({"s": s.start, "e": s.end, "t": s.text.strip(), "w": [(w.start, w.end, w.word) for w in s.words]})
    lines.append(f"[{s.start:7.2f}-{s.end:7.2f}] {s.text.strip()}")
    print(lines[-1], flush=True)
json.dump(rows, open(f"{out}/transcript.json", "w"))
open(f"{out}/transcript.txt", "w").write("\n".join(lines) + "\n")
print("duration:", len(audio) / 16000)
