import wave, numpy as np, json
from faster_whisper import WhisperModel
with wave.open('clean16k.wav') as w:
    x=np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(np.float32)/32768
m=WhisperModel("small",device="cpu",compute_type="int8",cpu_threads=3)
segs,_=m.transcribe(x, word_timestamps=True, initial_prompt="The narrator sometimes says the word dot, like: risk dot for, stocks dot maintaining.")
res=[]
for s in segs:
    for w in s.words:
        if 'dot' in w.word.lower(): res.append([w.start,w.end,w.word]); print(round(w.start,2), w.word, '|', s.text, flush=True)
json.dump(res,open('dots.json','w'))
print("DONE")
