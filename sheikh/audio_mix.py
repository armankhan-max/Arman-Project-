"""Voice + ducked music bed (Mixkit free tracks) + soft whooshes on habit titles -> audio/mix.wav"""
import os, sys, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import timeline as TL

HERE = os.path.dirname(os.path.abspath(__file__))
A = os.path.join(HERE, "audio")
END = TL.END
# (track, start time in video)
BED = [("m1104", 0), ("m584", 134), ("m22", 430), ("m1051", 625), ("m27", 728), ("m584", 842)]
XF = 5.0

inputs = ["-i", os.path.join(A, "voice_clean.wav")]
filt = []
for k, (name, st) in enumerate(BED):
    nxt = BED[k + 1][1] if k + 1 < len(BED) else END
    dur = nxt - st + XF
    inputs += ["-stream_loop", "-1", "-i", os.path.join(A, "music", name + ".mp3")]
    fo = max(0.0, dur - XF)
    filt.append(f"[{k + 1}:a]loudnorm=I=-16:TP=-2:LRA=11,aresample=44100,aformat=channel_layouts=stereo,"
                f"atrim=0:{dur:.2f},afade=t=in:d={XF if k else 1.5},afade=t=out:st={fo:.2f}:d={XF},"
                f"adelay={int(st * 1000)}|{int(st * 1000)}[m{k}]")
nb = len(BED)
filt.append("".join(f"[m{k}]" for k in range(nb)) + f"amix=inputs={nb}:normalize=0,volume=-25dB,atrim=0:{END:.2f}[bed]")
filt.append("[0:a]aresample=44100,aformat=channel_layouts=stereo,highpass=f=70,"
            "acompressor=threshold=-20dB:ratio=2.5:attack=8:release=120,volume=3dB,asplit=2[v][vsc]")
filt.append("[bed][vsc]sidechaincompress=threshold=0.03:ratio=8:attack=30:release=650[duck]")
# whooshes on habit titles and quotes
hits = [o["s"] - 0.35 for o in TL.OVERLAYS if o["k"] in ("title", "quote")]
si = 1 + nb
inputs += ["-i", os.path.join(A, "sfx", "w1490.mp3")]
filt.append(f"[{si}:a]aresample=44100,aformat=channel_layouts=stereo,volume=-28dB,asplit={len(hits)}" +
            "".join(f"[s{k}]" for k in range(len(hits))))
for k, h in enumerate(hits):
    filt.append(f"[s{k}]adelay={int(max(h, 0) * 1000)}|{int(max(h, 0) * 1000)}[d{k}]")
filt.append("[v][duck]" + "".join(f"[d{k}]" for k in range(len(hits))) +
            f"amix=inputs={2 + len(hits)}:normalize=0,afade=t=out:st={END - 2:.2f}:d=2,"
            f"loudnorm=I=-13:TP=-1.2:LRA=11,aresample=48000,apad[out]")
out = os.path.join(A, "mix.wav")
cmd = ["ffmpeg", "-v", "error", "-y"] + inputs + ["-filter_complex", ";".join(filt), "-map", "[out]",
                                                  "-t", f"{END:.2f}", "-c:a", "pcm_s16le", out]
subprocess.run(cmd, check=True)
print("wrote", out)
