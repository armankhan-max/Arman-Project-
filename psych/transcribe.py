import json, sys
from faster_whisper import WhisperModel
m = WhisperModel("small", device="cpu", compute_type="int8", cpu_threads=4)
segs, info = m.transcribe(__import__("numpy").frombuffer(open(sys.argv[1],"rb").read()[44:], dtype="int16").astype("float32")/32768, word_timestamps=True, beam_size=5, language="en")
out = []
for s in segs:
    out.append({"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip(),
                "words": [{"w": w.word, "s": round(w.start, 2), "e": round(w.end, 2)} for w in s.words]})
    print(f"{s.start:7.2f} {s.end:7.2f} {s.text.strip()}", flush=True)
json.dump(out, open(sys.argv[2], "w"), indent=1)
