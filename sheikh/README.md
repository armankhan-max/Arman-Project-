# Sheikh Umar: "10 money habits" video

Stock footage + Ken Burns avatar shots + text animations, cut to the voiceover
`Dubai_Sheikh_Voiceover_Merged.mp3` (16 min).

## What was done
1. **Voice cleanup** (`clean_voice.py`): the TTS voice said the word "Asterisk" 46 times.
   Each one was cut out at the nearest silence (8 ms fades at every join) and checked by
   re-transcribing every join. Result: `audio/voice_clean.wav` (15:56).
2. **Transcript** (`transcript.json`): Whisper `small` word timestamps, shifted to the cleaned audio.
3. **Timeline** (`timeline.py`): ~250 shots. Your avatar images (`img/av_*.jpg`) carry the
   "I / my" lines. B-roll images and 66 Mixkit stock clips carry the story beats. Every shot moves
   (zoom in/out, pan or push in to the face), with 0.5 s dissolves.
   Text animations: 10 habit title cards, quote cards, keyword pop-ups, numbered lists, a lower third,
   and word-highlighted captions (gold = current word).
4. **Sound** (`audio_mix.py`): voice + soft music bed (Mixkit free tracks, ducked under the voice)
   + a soft whoosh on each title/quote card. Normalized to -14 LUFS.
5. **Render** (`render.py`): 1920x1080, 30 fps, vignette + light film grain.

## Re-render
```bash
bash stock/dl.sh                      # (from inside stock/) re-download the Mixkit clips
python3 clean_voice.py voice.mp3      # only if the voiceover changes
python3 audio_mix.py
python3 render.py --jobs 4 --out video.mp4
ffmpeg -i video.mp4 -i audio/mix.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest final.mp4
```
Stock footage: Mixkit (free license). Music: Mixkit free stock music.
