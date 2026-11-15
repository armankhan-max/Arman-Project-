# Project notes

## Slicing ASMR videos
If the user asks for a slicing / cutting / "1 cut vs 1000 cuts" / satisfying ASMR cutting animation of any
object or product, use the `slicing-asmr` skill (`.claude/skills/slicing-asmr/SKILL.md`). It holds the user's
rules (very short replies, one video only, 720p vertical, 60-65 s, hook, counters, sound), the analysed
reference videos, and the Blender pipeline in `teddy/`. Ask only for the object and the maximum cut count
if they are missing, then build, render in the background (resume after container restarts) and send only the MP4.
