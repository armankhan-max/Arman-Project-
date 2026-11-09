"""Word-timestamped transcript of the voiceover (sherpa-onnx zipformer, offline)."""
import json, subprocess, sys
import numpy as np, sherpa_onnx
audio, mdir = sys.argv[1], sys.argv[2]
pcm = subprocess.run(["ffmpeg","-v","error","-i",audio,"-ac","1","-ar","16000","-f","s16le","-"],capture_output=True).stdout
x = np.frombuffer(pcm, np.int16).astype(np.float32)/32768
sr = 16000
rec = sherpa_onnx.OfflineRecognizer.from_transducer(
    encoder=f"{mdir}/encoder-epoch-99-avg-1.int8.onnx", decoder=f"{mdir}/decoder-epoch-99-avg-1.onnx",
    joiner=f"{mdir}/joiner-epoch-99-avg-1.int8.onnx", tokens=f"{mdir}/tokens.txt", num_threads=4)
# split on pauses (>=0.35s of low energy), chunks <= 25s
hop = 160; e = np.sqrt(np.convolve(x**2, np.ones(400)/400, 'same')[::hop]); thr = max(0.01, np.percentile(e, 20)*2.5)
quiet = e < thr
cuts, run = [0], 0
for i, q in enumerate(quiet):
    run = run+1 if q else 0
    t = i*hop
    if (run >= 35 and t-cuts[-1] > 4*sr) or t-cuts[-1] > 25*sr:
        cuts.append(t - run*hop//2); run = -10**9 if False else 0
cuts.append(len(x))
segs = []
for a, b in zip(cuts[:-1], cuts[1:]):
    st = rec.create_stream(); st.accept_waveform(sr, x[a:b]); rec.decode_stream(st)
    r = st.result
    if not r.tokens: continue
    words, cur = [], None
    for tok, ts in zip(r.tokens, r.timestamps):
        t = a/sr + ts
        if tok.startswith(("▁", " ")) or cur is None:
            if cur: words.append(cur)
            cur = {"w": tok.replace("▁"," "), "s": round(t,2)}
        else: cur["w"] += tok
    words.append(cur)
    for i, w in enumerate(words):
        w["e"] = round(min(words[i+1]["s"] if i+1 < len(words) else b/sr, w["s"]+0.8), 2)
    segs.append({"start": words[0]["s"], "end": words[-1]["e"], "text": "".join(w["w"] for w in words).strip().lower(), "words": words})
    print(f"[{segs[-1]['start']:7.2f}] {segs[-1]['text']}", flush=True)
json.dump(segs, open("transcript.json","w"), indent=1)
