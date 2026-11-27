import re, json, numpy as np, soundfile as sf, sys
from kokoro_onnx import Kokoro
k = Kokoro("tts/kokoro-v1.0.onnx", "tts/voices-v1.0.bin")
NUM = {0:"oh",1:"one",2:"two",3:"three",4:"four",5:"five",6:"six",7:"seven",8:"eight",9:"nine",10:"ten",11:"eleven",12:"twelve",15:"fifteen",19:"nineteen",20:"twenty",30:"thirty",31:"thirty one",40:"forty",52:"fifty two",15:"fifteen"}
def t2w(m):
    h, mm = int(m.group(1)), int(m.group(2))
    def w(n):
        if n in NUM: return NUM[n]
        tens = ["","","twenty","thirty","forty","fifty"][n//10]; return tens + ("" if n%10==0 else " " + NUM[n%10])
    return w(h) + (" o'clock" if mm == 0 else (" oh " + w(mm) if mm < 10 else " " + w(mm)))
rows = []
for f in ["plan/script1.txt", "plan/script2.txt", "plan/script3.txt", "plan/script4.txt"]:
    for line in open(f):
        if not line.strip() or line.startswith("#"): continue
        parts = [p.strip() for p in line.rstrip("\n").split("|")]
        while len(parts) < 3: parts.append("")
        rows.append({"pool": parts[0], "text": parts[1], "ov": parts[2]})
SR = 24000
audio = []; t = 0.0
for i, r in enumerate(rows):
    if not r["text"]:
        n = int(1.3 * SR); audio.append(np.zeros(n, np.float32)); r["start"] = t; t += n / SR; r["end"] = t; continue
    txt = re.sub(r"\b(\d{1,2}):(\d{2})\b", t2w, r["text"])
    s, sr = k.create(txt, voice="am_michael", speed=0.92, lang="en-us")
    s = s.astype(np.float32)
    # trim leading/trailing silence
    nz = np.where(np.abs(s) > 0.01)[0]
    if len(nz): s = s[max(0, nz[0] - 600): nz[-1] + 1200]
    r["start"] = t; audio.append(s); t += len(s) / SR; r["end"] = t
    gap = 0.45 if not rows[i + 1:i + 2] or rows[i + 1]["text"] else 0.2
    audio.append(np.zeros(int(gap * SR), np.float32)); t += gap
    if i % 20 == 0: print(i, len(rows), round(t / 60, 1), flush=True)
sf.write("voice.wav", np.concatenate(audio), SR)
json.dump(rows, open("plan/timeline.json", "w"), indent=0)
print("DONE", round(t / 60, 2))
