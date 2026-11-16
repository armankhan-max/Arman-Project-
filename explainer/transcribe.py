import json, sys
from faster_whisper import WhisperModel
m = WhisperModel(sys.argv[2] if len(sys.argv)>2 else "small", device="cpu", compute_type="int8", cpu_threads=4)
import numpy as np
audio=np.fromfile("voice16k.f32",dtype=np.float32)
segs, info = m.transcribe(audio, word_timestamps=True, vad_filter=False, beam_size=1)
print("LANG", info.language, info.language_probability, flush=True)
out=[]
for s in segs:
    out.append({"start":round(s.start,2),"end":round(s.end,2),"text":s.text.strip(),
      "words":[{"w":w.word,"s":round(w.start,2),"e":round(w.end,2)} for w in s.words]})
    print(f"[{s.start:7.2f}-{s.end:7.2f}] {s.text.strip()}", flush=True)
json.dump(out, open("transcript.json","w"), ensure_ascii=False, indent=1)
print("DONE")
