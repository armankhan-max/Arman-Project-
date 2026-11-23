# Arman-Project

Faceless YouTube video projects. Owner talks in Hindi/Hinglish: reply short, in Hinglish, minimal chat
text, no frames unless asked, work fast.

When the user sends a voiceover and asks for a video like before ("Mark Tilbury wala", "same style",
"voice se video bana do"): use the skill `.claude/skills/mark-tilbury-video/SKILL.md` and the kit in `kit/`.
Deliver one merged `Final_Video.mp4` under ~95 MB (bigger files fail on the user's phone).

- `avatar_video/` — video 1 ("7 smart things to buy in your 60s")
- `video2/` — video 2 ("if the market crashed 50%: 4 stocks"), reference for the current style
- `kit/` — reusable scripts, avatar stickers, fonts, Mixkit clip catalog
