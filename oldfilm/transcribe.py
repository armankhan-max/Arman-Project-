import json, sys
from faster_whisper import WhisperModel
m = WhisperModel("small", device="cpu", compute_type="int8", cpu_threads=4)
import numpy as np, wave
wf=wave.open(sys.argv[1]); a=np.frombuffer(wf.readframes(wf.getnframes()),np.int16).astype(np.float32)/32768
segs, info = m.transcribe(a, word_timestamps=True, vad_filter=True, beam_size=1)
print(info.language, info.duration, flush=True)
out=[]
for s in segs:
    out.append({"start":round(s.start,2),"end":round(s.end,2),"text":s.text.strip(),
                "words":[{"w":w.word,"s":round(w.start,2),"e":round(w.end,2)} for w in s.words]})
    print(f"[{s.start:7.1f}] {s.text.strip()}", flush=True)
json.dump(out, open("transcript.json","w"), indent=1, ensure_ascii=False)
print("DONE")
