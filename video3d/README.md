# "Your phone is dirtier than a toilet seat": 3D animated short

A vertical (1080×1920, 30 fps, 19 s) 3D explainer short in a glossy, macro-close-up style, timed to
the uploaded voiceover.

Output: `phone_germs_3d.mp4` (energetic voice + low background music + SFX, −14 LUFS, with captions)

## Shots (all modelled and animated procedurally in Blender / Cycles)

| # | Time | Line | Shot |
|---|------|------|------|
| 1 | 0.0–2.6 | Your phone can be dirtier than a toilet seat. | Germ-covered phone resting on a toilet seat, camera pulls back |
| 2 | 2.6–4.9 | That's because toilet seats get cleaned, | Spray bottle mists the seat, sponge wipes germs away, sparkles |
| 3 | 4.9–6.6 | …and your phone almost never does. | Low macro push-in on a phone swarming with crawling germs |
| 4 | 6.6–7.8 | Every door handle, | Hand grabs a brass lever handle, germs jump onto the fingers |
| 5 | 7.8–9.0 | every dollar bill, | Hand touches a germy banknote |
| 6 | 9.0–9.9 | every snack | Hand grabs chips from a bowl |
| 7 | 9.9–11.6 | leaves bacteria on your fingers. | Extreme close-up: germs pop up all over a fingertip |
| 8 | 11.6–13.3 | Then you tap your screen, | Finger taps the screen (ripples) and leaves germs behind |
| 9 | 13.3–15.4 | and then, you press it against your face. | Phone pressed to a cheek, pulled away: germs left on the skin |
| 10 | 15.4–19.0 | Wiping it once a day removes most of them. | Microfibre cloth wipes the germs off, screen brightens, sparkles |

## Files

- `lib3d.py`: scene setup, materials (skin, wood, tiles, germs), props (phone, germs with cilia,
  skin-modifier hands with nails and sleeves, sparkles), animation helpers.
- `shots.py`: the 10 shots.
- `assets.py`: phone home screen and generic banknote textures.
- `audio3d.py`: synthesized music (a quirky 112 bpm pluck/marimba groove, ducked about 22 dB under
  the voice) and around 60 timed SFX: whooshes on cuts, germ squelches and bloops, spray, scrubbing,
  door latch, paper rustle, chip crunch, screen taps and ripples, cloth swish, sparkle chimes and a ding.
  It reuses the instruments in `../video/audio.py`.
- `compose.py`: joins the shots, upscales 540×960 renders to 1080×1920, grades the picture, burns in
  word-by-word captions and muxes the audio.
- `audio/voice_energetic.wav`: the voiceover, processed to sound more energetic: 7% faster, pitch
  +0.5 semitone with formants preserved, presence EQ, compression and a light room tone.

## Voice processing

```bash
ffmpeg -i voice.mp3 -af "aresample=48000:resampler=soxr,rubberband=tempo=1.07:pitch=1.03:formant=preserved:transients=crisp,\
highpass=f=75,equalizer=f=180:t=q:w=1:g=2,equalizer=f=350:t=q:w=1.2:g=-2,equalizer=f=3200:t=q:w=1:g=3.5,\
equalizer=f=7500:t=q:w=1.5:g=-1.5,highshelf=f=10000:g=1.5,acompressor=threshold=-20dB:ratio=3.5:attack=5:release=60:makeup=4,\
aecho=0.9:0.9:23|41:0.07|0.04,alimiter=limit=0.89" -ac 1 audio/voice_energetic.wav
```

Word timings (`audio/words.json`) come from sherpa-onnx (Whisper small.en for the text, Zipformer for
the timestamps).

## Re-render

```bash
pip install bpy==5.2.3 numpy scipy pillow   # needs libegl1 on Linux
python assets.py
RES_X=360 RES_Y=640 SAMPLES=8 python run_shot.py s07 --still 30 --out preview/   # one preview frame
./render_all.sh                      # all shots -> frames/ (540x960, 10 spp + denoise)
python audio3d.py --voice audio/voice_energetic.wav --out audio/mix.wav
python compose.py --audio audio/mix.wav --out phone_germs_3d.mp4     # add --no-captions for a clean version
```
