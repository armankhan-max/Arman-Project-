import json,sys
from faster_whisper import WhisperModel
m=WhisperModel("base.en",device="cpu",compute_type="int8",cpu_threads=3)
import numpy as np
a=np.fromfile("audio16.raw",dtype=np.float32)
segs,info=m.transcribe(a,beam_size=1,vad_filter=True)
out=[]
for s in segs:
    out.append({"s":round(s.start,2),"e":round(s.end,2),"t":s.text.strip()})
    print(f"{s.start:.1f} {s.text.strip()}",flush=True)
json.dump(out,open("transcript.json","w"),indent=0)
