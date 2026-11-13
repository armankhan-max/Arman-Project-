# Film Director AI

A private, single-owner AI film production studio. You talk to one **Film Director** agent; it plans the
production, delegates to specialist agents (research, script, narration, storyboard, visuals, Blender 3D, sound,
editing, render, quality control), runs the work as a persistent, resumable workflow, and hands back a verified
MP4 plus an editable project you can keep changing — by chat or on a timeline.

```
Owner ──chat / UI──► Next.js studio ──/api──► FastAPI ──► Director ──► workflow DAG (PostgreSQL) ──► Celery workers
                                                                         │
             research · script · voiceover · storyboard · visual(per scene) · blender · audio · editor · render · QC · repair
```

## What works today (verified in this repo)

| Area | Status |
| --- | --- |
| Owner login, signed sessions, CSRF header, encrypted provider credentials, audit log | working, tested |
| Projects, uploads with validation (corrupted files rejected), original/processed separation | working, tested |
| Persistent workflow engine: dependencies, wildcard fan-out, retries, cancel, resume, crash recovery | working, tested |
| Director: input analysis, production plan, chat intents (EN/HI/Hinglish), rule-based fallback | working |
| Narration: free neural TTS with word timings, uploaded voiceover analysis (probe, loudness, silences) | working |
| Transcription: faster-whisper / OpenAI adapters; script-to-speech alignment fallback when no STT model | working (Whisper model must be downloadable) |
| Storyboard: real-timestamp segmentation, per-scene shot/camera/lighting/sfx/transition plans, continuity bible | working |
| Visuals: stock (Pexels, Pixabay, Wikimedia Commons), archive (Wikimedia, NASA), AI images (free Pollinations / OpenAI) with licence records | working (Pexels/Pixabay need free keys) |
| AI video (Runway, Luma), avatars (D-ID) | adapters built from public docs, **awaiting credentials** |
| Blender 3D: 7 parameterised templates, EEVEE with Cycles fallback, .blend saved | working |
| Sound: original score per mood, planned SFX, ducking, voice clean-up chain, −14 LUFS | working |
| Editor: multi-track timeline (scenes, graphics, text, subtitles, voice, music, SFX), clip/overlay inspector, versions & restore | working |
| Render: parallel compositor (camera moves, transitions, motion graphics, captions, grade) → H.264/AAC, ffprobe-verified | working, tested |
| QC: codecs, resolution, fps, duration, black/frozen frames, silence, clipping, loudness, gaps, repetition, subtitle sync, creative review; bounded auto-repair | working, tested |
| Chat editing: smallest change, only affected scenes regenerated, owner edits preserved | working, tested |
| YouTube: public research (Data API), OAuth read-only channel analytics, snapshots, analysis | built; needs your API key / OAuth client |
| Knowledge (pgvector RAG with trust levels), five-category memory | working, tested |
| Budget: daily/monthly/project/provider limits, owner-set cost estimates, paid calls blocked without limits | working, tested |

See `DEVELOPMENT_STATUS.md` for the full list, limitations and next tasks.

## Quick start (local, no Docker)

Requirements: Python 3.11+, Node 20+, PostgreSQL 16 with pgvector, Redis 7, FFmpeg, Blender 4 (optional).

```bash
cp .env.example .env                       # set FDA_SECRET_KEY and FDA_OWNER_PASSWORD
cd backend
pip install -r requirements.txt
createdb fda && psql fda -c "create extension vector"
alembic upgrade head
uvicorn fda.main:app --port 8000           # API (+ in-process jobs if Celery is not running)
celery -A fda.workers.celery_app worker -Q default,research,transcription,visual,audio,qc -c 4   # optional
celery -A fda.workers.celery_app worker -Q render,blender -c 1                                   # optional
cd ../frontend && npm install && npm run dev   # http://localhost:3000
```

With Docker: `cp .env.example .env && docker compose up --build`, then open http://localhost:3000.

First sign-in: `owner@localhost` and the password from `FDA_OWNER_PASSWORD`, or from
`storage/OWNER_CREDENTIALS.txt` if you left it empty.

## Using it

1. **Settings → Providers**: the studio runs with zero keys (free text model, free images, Wikimedia/NASA archive,
   neural voices, Blender, original music). Add keys to raise quality: Anthropic (Director/writer), Pexels and
   Pixabay (free stock video), ElevenLabs, Runway/Luma (AI video), YouTube Data API, Google OAuth.
2. **Settings → Budget**: set a daily or monthly limit and, for each paid provider, your USD-per-unit estimate.
   Without both, paid providers never run.
3. **AI Director** chat: “Create a documentary titled *What If Jupiter Disappeared?* — 8 minutes, cinematic,
   scientifically accurate.” Attach a narration file to have it preserved and analysed instead of voiced.
4. Watch progress live in the project; when it finishes, review the storyboard, play the render, read the QC
   report, then edit by chat (“Scene 4 ka camera movement change kar”, “music thoda lower kar”) or on the timeline
   and press **Apply & render**. Every change creates a new project version; old versions can be restored.
5. **Export project** downloads the editable package: project JSON, timeline, script, transcript, storyboard,
   captions (SRT), research with sources, and per-asset licences.

## Tests

```bash
cd backend && createdb fda_test && psql fda_test -c "create extension vector"
pytest -q                     # unit + API integration + offline end-to-end render/QC/chat-edit
cd ../frontend && npm run build && npm test
FDA_PASSWORD=... node tests/e2e/ui.e2e.cjs   # UI check against running servers (needs Playwright)
```

## Documentation

- `docs/ARCHITECTURE.md` — agents, workflow engine, data model, rendering, security
- `docs/PROVIDERS.md` — every provider, what it needs and how it is used
- `docs/OPERATIONS.md` — deployment, workers, backups, troubleshooting
- `DEVELOPMENT_STATUS.md` — implemented / tested / incomplete, missing credentials
