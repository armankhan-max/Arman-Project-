"""Voiceover + timing for the Pudding Guy short. python3 vo.py MODEL_DIR OUT_DIR
Writes voice.wav (44.1k mono) and vo.json (sentence + caption-chunk times)."""
import sys, json, re
import numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
# each sentence: list of "display|spoken" caption chunks (spoken defaults to display)
S = [
 ["This man", "bought", "12,000 cups|twelve thousand cups", "of pudding,"],
 ["and he's been", "flying", "for free", "ever since."],
 ["In 1999,|In nineteen ninety-nine,", "a food company", "ran a promo."],
 ["Mail in", "10 barcodes,|ten barcodes,", "get", "500|five hundred", "airline miles."],
 ["Everyone", "ignored it."],
 ["Except", "David."],
 ["He's an", "engineer,", "so he does", "the math", "right there", "in the aisle."],
 ["And at a", "discount store,", "he finds it."],
 ["Chocolate", "pudding.", "25 cents|Twenty-five cents", "a cup."],
 ["And every", "single cup", "has its own", "barcode."],
 ["So he drives", "to 10 stores|to ten stores", "and clears", "the shelves."],
 ["The cashier", "asks,", "Sir...|Sir,", "why?"],
 ["And he says,", "Y2K.|Why two kay."],
 ["12,150|Twelve thousand, one hundred and fifty", "cups."],
 ["Total cost:|Total cost,", "$3,000.|three thousand dollars."],
 ["But now", "he has", "a problem."],
 ["The deadline", "is weeks away,", "and nobody", "can peel", "12,000 labels|twelve thousand labels", "alone."],
 ["So he calls", "a food bank."],
 ["They peel", "the labels,", "they keep", "the pudding."],
 ["He mails in", "the barcodes,", "and gets", "1.25 million|one point two five million", "miles."],
 ["That's about", "$150,000|a hundred and fifty thousand dollars", "of flights."],
 ["He's been", "flying on them", "for over", "20 years.|twenty years."],
 ["Oh, and", "because he", "donated", "the pudding,"],
 ["he got a", "tax write-off|tax write off", "too."],
]
GAP = {1: .22, 5: .16, 9: .14, 12: .22, 14: .2, 18: .16, 21: .22}  # pause after sentence i (default .07)
md, od = sys.argv[1], sys.argv[2]
k = Kokoro(md + '/kokoro.onnx', md + '/voices.bin')
SR = 44100; out = [np.zeros(int(.12 * SR))]; t = .12; sents = []; chunks = []
for i, s in enumerate(S):
    disp = [c.split('|')[0] for c in s]; spk = [c.split('|')[-1] for c in s]
    a, sr = k.create(' '.join(spk), voice='am_michael', speed=1.22, lang='en-us')
    e = np.abs(a); idx = np.where(e > 0.012)[0]; a = a[max(0, idx[0] - 240): idx[-1] + 1200]
    a = np.interp(np.arange(0, len(a), sr / SR), np.arange(len(a)), a)
    d = len(a) / SR; w = [len(re.sub(r'[^a-z]', '', x.lower())) + 1.5 for x in spk]; tot = sum(w); u = t
    for dd, ww in zip(disp, w): chunks.append([round(u, 3), round(u + d * ww / tot, 3), dd]); u += d * ww / tot
    sents.append([round(t, 3), round(t + d, 3)]); out.append(a); g = GAP.get(i, .07); out.append(np.zeros(int(g * SR))); t += d + g
x = np.concatenate(out + [np.zeros(int(1.1 * SR))]); x = x / np.abs(x).max() * 0.92
sf.write(od + '/voice.wav', x, SR)
json.dump({'dur': round(len(x) / SR, 3), 'sents': sents, 'chunks': chunks}, open(od + '/vo.json', 'w'))
print('dur', len(x) / SR); [print(i, s) for i, s in enumerate(sents)]
