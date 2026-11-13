# Operations

## Processes

| Process | Command | Notes |
| --- | --- | --- |
| API | `uvicorn fda.main:app --host 0.0.0.0 --port 8000` | Runs migrations-free; run `alembic upgrade head` first. |
| General worker | `celery -A fda.workers.celery_app worker -Q default,research,transcription,visual,audio,qc -c 4` | Network/IO-bound work. |
| Render worker | `celery -A fda.workers.celery_app worker -Q render,blender -c 1` | CPU-bound; one job at a time, each render already uses `FDA_RENDER_WORKERS` processes. Put it on a separate machine for long videos. |
| Beat | `celery -A fda.workers.celery_app beat` | Re-queues tasks whose worker died. |
| Website | built into the backend image (`npm run build` → `frontend/out`, served by the API) | `npm run dev` for development. |

If Redis or Celery workers are not available, the API runs jobs in an in-process thread pool (fine for one owner on
one machine). Jobs never depend on the browser staying open.

A GPU worker is only needed if you add a local video model; none of the bundled providers require one. Cloud GPU
providers are never started automatically.

## Blender

Install Blender 4.x and make sure `blender` is on PATH (or set `FDA_BLENDER_BIN`). EEVEE is used first; on machines
without an OpenGL/EGL context the agent falls back to Cycles on CPU automatically (slower). Renders run at
`FDA_BLENDER_SCALE` of the output size and are scaled by the compositor.

## Backups

- Database: `pg_dump -Fc fda > fda-$(date +%F).dump` (daily), restore with `pg_restore -d fda`.
- Storage: back up `FDA_STORAGE_DIR` (or the S3 bucket); keys are stable, so DB and files restore independently.
- `.work/` inside storage is scratch space and can be deleted when no job is running.

## Troubleshooting

| Symptom | Cause / fix |
| --- | --- |
| “No reasoning model available” | No LLM key and the free endpoint is unreachable. Add an Anthropic/OpenAI key and budget. |
| “Paid provider … needs a spending limit” | Set a daily or monthly limit in Settings → Budget and a USD-per-unit estimate on the provider. |
| Scenes say “substituted” | The requested source was unavailable (e.g. no Pexels key); the reason is on the scene card. |
| Transcription fails | faster-whisper could not load its model (no network). Point `FDA_WHISPER_MODEL` to a local model folder, configure OpenAI transcription, or upload the script with the narration (alignment fallback). |
| Job stuck “running” after a crash | Wait for beat (5 min) or restart the API; or press **Resume from checkpoint**. |
| Render verification failed | The message lists the mismatch (codec, size, fps, duration); check FFmpeg version and disk space. |
| OAuth “redirect_uri_mismatch” | Register exactly `FDA_PUBLIC_BASE_URL/api/v1/youtube/oauth/callback`. |
