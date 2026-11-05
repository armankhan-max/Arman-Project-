"""Phoneme-accurate lip sync for characters who actually speak a line.

speak(t, line) -> pose fields (viseme, open, head nod) for that instant, or {} when not speaking.
Phonemes come from forced alignment of the real voiceover (pocketsphinx), openness from the
voice loudness, with 40 ms co-articulation so the mouth anticipates the next sound.
"""
import json
import math
import os
import subprocess
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))

VIS = {}
for ph in ('AA', 'AE', 'AH', 'AY', 'AW', 'HH'):
    VIS[ph] = 'AA'
for ph in ('IY', 'IH', 'EH', 'EY', 'Y'):
    VIS[ph] = 'EE'
for ph in ('OW', 'AO', 'OY', 'UW', 'UH', 'W'):
    VIS[ph] = 'OO'
for ph in ('M', 'B', 'P'):
    VIS[ph] = 'MBP'
for ph in ('F', 'V'):
    VIS[ph] = 'FV'
for ph in ('L', 'N', 'T', 'D', 'TH', 'DH'):
    VIS[ph] = 'L'
for ph in ('S', 'Z', 'SH', 'ZH', 'CH', 'JH', 'K', 'G', 'NG', 'R', 'ER'):
    VIS[ph] = 'S'
BASE_OPEN = dict(AA=1.0, EE=0.55, OO=0.7, MBP=0.0, FV=0.15, L=0.45, S=0.3, rest=0.0)


def align_phones(wav16, text, t0, t1, custom=None):
    from pocketsphinx import Decoder
    raw = open(wav16, 'rb').read()[44:]
    seg = raw[int(t0 * 16000) * 2:int(t1 * 16000) * 2]
    d = Decoder(samprate=16000, loglevel='FATAL')
    for k, v in (custom or {}).items():
        if d.lookup_word(k) is None:
            d.add_word(k, v, True)
    d.set_align_text(text)
    d.start_utt()
    d.process_raw(seg, full_utt=True)
    d.end_utt()
    d.set_alignment()
    d.start_utt()
    d.process_raw(seg, full_utt=True)
    d.end_utt()
    out = []
    for w in d.get_alignment():
        for p in w:
            if p.name != 'SIL':
                out.append((p.name, t0 + p.start / 100, t0 + (p.start + p.duration) / 100))
    return out


def loudness(wav16):
    x = np.frombuffer(open(wav16, 'rb').read()[44:], np.int16).astype(float) / 32768
    hop = 160
    n = len(x) // hop
    r = np.sqrt((x[:n * hop].reshape(n, hop) ** 2).mean(1))
    r = r / (np.percentile(r, 98) + 1e-9)
    return np.clip(r, 0, 1)


class Lines:
    def __init__(self, wav16, lines, cache):
        """lines: {name: (text, t0, t1)}"""
        self.env = loudness(wav16)
        if os.path.exists(cache):
            self.ph = {k: [tuple(p) for p in v] for k, v in json.load(open(cache)).items()}
        else:
            self.ph = {k: align_phones(wav16, txt, a, b) for k, (txt, a, b) in lines.items()}
            json.dump(self.ph, open(cache, 'w'), indent=0)

    def _vis(self, phones, t):
        for i, (p, a, b) in enumerate(phones):
            if a - 0.04 <= t < b - 0.04:  # co-articulation: shape the next sound 40 ms early
                return VIS.get(p, 'L')
        return 'rest'

    def speak(self, t, name):
        phones = self.ph.get(name, [])
        if not phones or t < phones[0][1] - 0.06 or t > phones[-1][2] + 0.08:
            return {}
        v = self._vis(phones, t)
        i = int(t * 100)
        e = float(self.env[min(max(i, 0), len(self.env) - 1)])
        op = 0.0 if v in ('MBP', 'rest') else min(1.0, BASE_OPEN[v] * (0.55 + 0.6 * e))
        nod = 2.5 * math.sin(t * 9.0) * e  # tiny head motion carried by the voice energy
        return dict(viseme=v, open=op, nod=nod)
