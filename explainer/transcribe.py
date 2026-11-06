"""Transcribe the voiceover with word timestamps (sherpa-onnx, offline).
VAD splits speech into chunks -> zipformer transducer gives token times -> words,
then a punctuation model restores sentence punctuation. Output: transcript.json"""
import json, sys, os
import numpy as np, soundfile as sf, sherpa_onnx

M = sys.argv[3]
wav, sr = sf.read(sys.argv[1], dtype="float32")
asr = sherpa_onnx.OfflineRecognizer.from_transducer(
    encoder=f"{M}/sherpa-onnx-zipformer-en-2023-06-26/encoder-epoch-99-avg-1.int8.onnx",
    decoder=f"{M}/sherpa-onnx-zipformer-en-2023-06-26/decoder-epoch-99-avg-1.onnx",
    joiner=f"{M}/sherpa-onnx-zipformer-en-2023-06-26/joiner-epoch-99-avg-1.int8.onnx",
    tokens=f"{M}/sherpa-onnx-zipformer-en-2023-06-26/tokens.txt", num_threads=4, decoding_method="modified_beam_search")
pc = sherpa_onnx.OfflinePunctuation(sherpa_onnx.OfflinePunctuationConfig(
    model=sherpa_onnx.OfflinePunctuationModelConfig(
        ct_transformer=f"{M}/sherpa-onnx-punct-ct-transformer-zh-en-vocab272727-2024-04-12/model.onnx")))
vc = sherpa_onnx.VadModelConfig()
vc.silero_vad.model = f"{M}/vad.onnx"; vc.silero_vad.min_silence_duration = 0.35
vc.silero_vad.max_speech_duration = 20; vc.sample_rate = sr
vad = sherpa_onnx.VoiceActivityDetector(vc, buffer_size_in_seconds=60)
chunks = []
ws = vc.silero_vad.window_size
for i in range(0, len(wav), ws):
    vad.accept_waveform(wav[i:i + ws])
    while not vad.empty():
        chunks.append((vad.front.start / sr, np.array(vad.front.samples))); vad.pop()
vad.flush()
while not vad.empty():
    chunks.append((vad.front.start / sr, np.array(vad.front.samples))); vad.pop()
out = []
for t0, samples in chunks:
    st = asr.create_stream(); st.accept_waveform(sr, samples); asr.decode_stream(st)
    r = st.result
    words = []
    dur = len(samples) / sr
    for tok, ts in zip(r.tokens, r.timestamps):
        if tok.startswith(("▁", " ")) or not words:
            words.append({"w": tok.replace("▁", "").strip().lower(), "s": round(t0 + ts, 2)})
        else:
            words[-1]["w"] += tok.lower()
    words = [w for w in words if w["w"]]
    for i, w in enumerate(words):
        w["e"] = round(min(words[i + 1]["s"], w["s"] + 0.8) if i + 1 < len(words) else min(t0 + dur, w["s"] + 0.8), 2)
    if not words:
        continue
    text = pc.add_punctuation(" ".join(w["w"] for w in words))
    for a, b in (("，", ", "), ("。", ". "), ("？", "? "), ("！", "! "), ("、", ", ")):
        text = text.replace(a, b)
    text = " ".join(text.split())
    # map punctuated tokens back onto words (same count, split on spaces)
    pt = text.split()
    if len(pt) == len(words):
        for w, p in zip(words, pt):
            w["w"] = p
    out.append({"start": words[0]["s"], "end": words[-1]["e"], "text": text, "words": words})
    print(f"{t0:7.2f} {text}", flush=True)
json.dump(out, open(sys.argv[2], "w"), indent=1)
