import json, sys, wave
import numpy as np
from faster_whisper import WhisperModel

with wave.open(sys.argv[1]) as w:
    audio = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0

m = WhisperModel("small", device="cpu", compute_type="int8", cpu_threads=4)
segs, info = m.transcribe(audio, word_timestamps=True, vad_filter=True)
out = {"language": info.language, "segments": []}
for s in segs:
    out["segments"].append({"start": s.start, "end": s.end, "text": s.text,
        "words": [{"w": w.word, "s": w.start, "e": w.end} for w in s.words]})
    print(f"{s.start:7.1f} {s.text}", flush=True)
json.dump(out, open(sys.argv[2], "w"), indent=1)
