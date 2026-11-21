import wave, numpy as np, json, sys
from faster_whisper import WhisperModel
k, n = int(sys.argv[1]), int(sys.argv[2])
with wave.open('clean16k.wav') as w:
    x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
m = WhisperModel("small.en", device="cpu", compute_type="int8", cpu_threads=1)
L = 30; res = []
starts = list(range(0, int(len(x) / 16000), L))[k::n]
for a in starts:
    seg = x[a * 16000:(a + L + 1) * 16000]
    segs, _ = m.transcribe(seg, word_timestamps=True, language="en", beam_size=1,
                           initial_prompt="The narrator sometimes says the word dot, like: risk dot for, stocks dot maintaining.")
    words = [w for s in segs for w in s.words]
    for i, w in enumerate(words):
        if w.word.strip().lower().strip('.,') == 'dot':
            prev = words[i - 1].word.strip() if i else ''
            nxt = words[i + 1].word.strip() if i + 1 < len(words) else ''
            res.append([a + w.start, a + w.end, prev, nxt]); print(round(a + w.start, 2), prev, '| dot |', nxt, flush=True)
json.dump(res, open(f'dots_{k}.json', 'w'))
print("DONE")
