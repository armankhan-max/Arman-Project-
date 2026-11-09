"""Female voiceover (Kokoro TTS, local) + sentence timing -> voice.wav, timing.json"""
import json, sys, re, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
M = sys.argv[1]
SEG = [  # (text, pause_after_seconds)
 ("If I had three minutes and thirty-two seconds to show you how to never procrastinate again,", 0.15),
 ("all I'd say is...", 0.35),
 ("procrastination is like being trapped in an infinite loop.", 2.2),
 ("Have you ever woken up, and completely forgotten about the promises that you made to yourself the night before?", 0.45),
 ("You know, all the things that you swore you'd finally get done tomorrow.", 0.3),
 ("But then, tomorrow comes.", 0.5),
 ("Nothing's changed.", 0.4),
 ("You're back to your same old, comfortable routine.", 1.6),
 ("You see, every time you put off doing something really difficult, you trap yourself in an infinite psychological loop.", 0.6),
 ("First, there's the difficult task.", 0.35),
 ("Maybe it's reading that book you've been putting off,", 0.15),
 ("or finally starting that project you've been meaning to work on.", 0.5),
 ("That difficult task brings you discomfort.", 0.35),
 ("Maybe that's boredom, frustration, or the fear of not even knowing where to begin.", 0.5),
 ("So you avoid the task, maybe by picking up your phone,", 0.2),
 ("and therefore, you feel a sense of relief.", 0.5),
 ("But that relief teaches your brain to avoid discomfort,", 0.2),
 ("trapping you in the same cycle of procrastination, day after day.", 1.8),
 ("So how do you break free from the endless cycle of procrastination,", 0.2),
 ("before another day,", 0.15), ("another month,", 0.15), ("another year?", 1.8),
 ("First, slow down long enough to recognize the pattern you're stuck in.", 0.5),
 ("This is called metacognition,", 0.2),
 ("which is just a fancy word for thinking about your thinking.", 0.6),
 ("You see, you probably already know when you're procrastinating.", 0.25),
 ("But how often do you examine the very thoughts that led you to procrastinate?", 0.7),
 ("Every day, you make hundreds of decisions without even thinking about them.", 0.3),
 ("From what you make for breakfast, to what you do when you sit down for work.", 0.5),
 ("And somewhere along the way, procrastinating becomes just another automatic decision.", 0.2),
 ("Just another part of your routine.", 0.7),
 ("But when you slow down long enough to pay attention to your own thoughts,", 0.2),
 ("you can finally catch yourself, in that split second, before you slip into your same old habits.", 0.7),
 ("When you think metacognitively, you are finally given the choice:", 0.35),
 ("to either keep living the same day, over and over again, stuck in the cycle of procrastination.", 0.6),
 ("Or, you can finally take one small step forward,", 0.25),
 ("toward breaking the cycle.", 3.0),
]
k = Kokoro(f"{M}/kokoro-v1.0.onnx", f"{M}/voices-v1.0.bin")
voice = sys.argv[2] if len(sys.argv) > 2 else "af_heart"
out, tl, t = [], [], 0.6
out.append(np.zeros(int(0.6 * 24000), np.float32))
for txt, p in SEG:
    a, sr = k.create(txt, voice=voice, speed=0.88, lang="en-us")
    # trim silence
    nz = np.where(np.abs(a) > 0.01)[0]; a = a[max(0, nz[0]-240):nz[-1]+480]
    d = len(a) / sr
    words = re.findall(r"\S+", txt); L = sum(len(w) + 1 for w in words); c = 0; ws = []
    for w in words:
        s = t + d * c / L; c += len(w) + 1; ws.append({"w": w, "s": round(s, 3), "e": round(t + d * c / L, 3)})
    tl.append({"text": txt, "start": round(t, 3), "end": round(t + d, 3), "words": ws})
    out += [a, np.zeros(int(p * 1.9 * sr), np.float32)]; t += d + p * 1.9
sf.write("voice.wav", np.concatenate(out), 24000)
json.dump(tl, open("timing.json", "w"), indent=1)
print("dur", round(t, 2))
for i, s in enumerate(tl): print(i, s["start"], s["end"], s["text"][:50])
