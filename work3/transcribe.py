import json,sys
from faster_whisper import WhisperModel
m=WhisperModel("base.en",device="cpu",compute_type="int8",cpu_threads=4)
import wave,numpy as np
w=wave.open(sys.argv[1]);audio=np.frombuffer(w.readframes(w.getnframes()),dtype=np.int16).astype(np.float32)/32768
segs,_=m.transcribe(audio,word_timestamps=True,vad_filter=False)
out=[]
for s in segs:
    out.append({"start":s.start,"end":s.end,"text":s.text,"words":[[w.start,w.end,w.word] for w in s.words]})
    print(f"{s.start:.1f}-{s.end:.1f} {s.text}",flush=True)
json.dump(out,open("transcript.json","w"))
