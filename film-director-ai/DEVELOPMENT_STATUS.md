# Development status

Last updated: 2026-11-13. Environment used for verification: Linux, Python 3.13, PostgreSQL 16 + pgvector 0.6,
Redis 7, FFmpeg 6.1, Blender 4.0.2 (EEVEE via surfaceless EGL, Cycles CPU), Node 22. Outbound network limited to
an allow-list (no Hugging Face, Wikipedia or NASA; Wikimedia Commons, Pollinations and Edge TTS reachable).

## Phase status

| Phase | State | Evidence |
| --- | --- | --- |
| 1 Foundation (structure, DB, migrations, auth, config, storage, Docker files) | done | 41 tables via Alembic `0001`; auth/CSRF/API tests pass; `docker-compose.yml` written (not run here: no Docker daemon used) |
| 2 AI brain (Director, structured outputs, tool/agent registry, persistent workflow) | done | workflow tests: deps, wildcard fan-out, retry, failure propagation, resume, cancel, crash recovery |
| 3 Memory & knowledge | done | supersession, inference-can't-override, secret refusal, chunk/dedupe/search tests |
| 4 YouTube intelligence | built, untested live | Data API search/channel/videos, OAuth flow, Analytics sync (daily, per-video, traffic, retention), snapshots, analysis, dashboard. Needs your API key + OAuth client. |
| 5 Audio & storyboard | done | TTS with word timings, upload analysis (probe, loudness, silences, pauses), Whisper adapters, alignment fallback, timestamp segmentation tests |
| 6 Visual production | done (free sources); paid video awaiting keys | Wikimedia, Pollinations, Blender verified in a live run; Pexels/Pixabay/Runway/Luma adapters untested without keys |
| 7 Advanced production | done except third-party avatars | procedural score/SFX/mix verified; Blender templates verified; talking-photo avatar built in; D-ID adapter awaiting key |
| 8 Editor & renderer | done | timeline UI + APIs; parallel compositor render verified by ffprobe in e2e test |
| 9 Autonomy | done | budget gate tests; QC + bounded repair; chat edit plan → only affected scenes (e2e test) |
| 10 Hardening | partial | security headers, rate-limited login, encrypted secrets, audit log; no load testing, no frontend unit tests yet |

## Tested

- `pytest`: 33 tests (unit, API integration, offline end-to-end: storyboard → audio → timeline → render → ffprobe
  verify → QC → chat edit preserving unaffected scenes → rebuild keeping owner edits).
- Live run through the API with only free providers: script → neural narration → 6-scene storyboard (stock video,
  Blender, motion graphics) → Wikimedia archive + Pollinations image substitutions recorded → Blender renders →
  score/SFX/mix → timeline → render → QC.
- `next build` of the frontend: all pages compile and type-check.

## Missing credentials (features built, waiting for keys)

Anthropic / OpenAI / Groq (stronger reasoning), Pexels and Pixabay (stock video, free), ElevenLabs, Runway, Luma,
D-ID, Tavily, YouTube Data API key, Google OAuth client. Set a daily or monthly budget and per-provider cost
estimates before paid providers will run.

## Known limitations

- Without a paid LLM the free text model is used; it is slower and storyboard batches sometimes fall back to the
  heuristic planner (flagged per scene as `planned_by: heuristic`).
- Local Whisper needs its model downloaded once; in this sandbox the model host is blocked, so uploaded narration
  is aligned to an uploaded script instead (approximate word timing, flagged in QC).
- The built-in avatar is a talking-photo approximation (mouth/blink/camera), not true lip sync.
- Remotion is not used: every composition is rendered by the Skia/FFmpeg compositor, which covers the required
  features; a Remotion adapter can be added behind the renderer if React-based templates are wanted.
- Blender on CPU is slow (minutes per scene); EEVEE is preferred and Cycles is the fallback.
- QC creative review is text-based (narration vs. plan, asset title); it does not look at pixels.
- YouTube impressions/CTR are not available from the Analytics API and are shown as unavailable.
- Project deletion is a soft delete; a storage cleanup job for deleted projects is not implemented yet.

## Next tasks

1. Live-test Pexels/Pixabay, Anthropic, Runway, YouTube OAuth once keys are available.
2. Vision-based creative QC (frame samples → multimodal model) when a vision-capable provider is configured.
3. Storage retention job (purge soft-deleted projects, `.work/` scratch).
4. Frontend component tests (Vitest) and Playwright e2e for the editor.
5. Optional Remotion renderer adapter.
