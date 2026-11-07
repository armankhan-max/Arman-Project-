import json, subprocess, numpy as np
from faster_whisper import WhisperModel
m = WhisperModel("/tmp/claude-0/wm/model", device="cpu", compute_type="int8")
segs, info = m.transcribe(np.frombuffer(subprocess.run(["ffmpeg","-v","error","-i","assets/voice_raw.mp3","-ac","1","-ar","16000","-f","f32le","-"],capture_output=True).stdout,np.float32), word_timestamps=True, language="en")
out=[]
for s in segs:
    out.append({"start":round(s.start,2),"end":round(s.end,2),"text":s.text.strip(),
      "words":[{"w":w.word,"s":round(w.start,2),"e":round(w.end,2)} for w in s.words]})
    print(f"{s.start:6.2f}-{s.end:6.2f} {s.text}")
json.dump(out,open("transcript.json","w"),indent=1)
