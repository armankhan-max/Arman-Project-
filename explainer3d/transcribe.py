import json, sys
from faster_whisper import WhisperModel
m = WhisperModel(sys.argv[3], device="cpu", compute_type="int8")
segs, info = m.transcribe(sys.argv[1], word_timestamps=True, language="en")
out = []
for s in segs:
    out.append({"start": round(s.start,2), "end": round(s.end,2), "text": s.text.strip(),
                "words": [{"w": w.word, "s": round(w.start,2), "e": round(w.end,2)} for w in s.words]})
    print(f"[{s.start:6.2f}-{s.end:6.2f}] {s.text.strip()}", flush=True)
json.dump(out, open(sys.argv[2], "w"), indent=1)
