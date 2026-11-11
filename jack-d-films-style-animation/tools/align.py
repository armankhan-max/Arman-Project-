"""Force-align the script to the voiceover with PocketSphinx -> src/data/words.json"""
import json, re, sys
from pocketsphinx import Decoder

raw, script, out = sys.argv[1:4]
text = open(script).read()
tokens = re.findall(r"[A-Za-z']+", text)
dec = Decoder(samprate=16000)
known = [t for t in tokens if dec.lookup_word(t.lower())]
missing = [t for t in tokens if not dec.lookup_word(t.lower())]
print("MISSING", missing)
dec.set_align_text(" ".join(t.lower() for t in known))
dec.start_utt(); dec.process_raw(open(raw, "rb").read(), full_utt=True); dec.end_utt()
segs = [(s.word, s.start_frame / 100, (s.end_frame + 1) / 100) for s in dec.seg() if not s.word.startswith("<") and s.word != "(NULL)"]
print(len(segs), len(known))
json.dump([{"w": w, "s": s, "e": e} for w, s, e in segs], open(out, "w"))
for w, s, e in segs: print(f"{s:6.2f} {e:6.2f} {w}")
