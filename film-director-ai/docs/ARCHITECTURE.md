# Architecture

## Layers

| Layer | Code | Notes |
| --- | --- | --- |
| UI | `frontend/` (Next.js 15, React 19, Tailwind) | Dark studio: dashboard, Director chat, project workspace (storyboard, timeline editor, renders/QC, research, versions, jobs), YouTube intelligence, knowledge, memory, settings. `/api/*` is proxied to the backend. |
| API | `backend/fda/main.py`, `fda/api/*` | FastAPI, versioned under `/api/v1`. Session cookie auth, CSRF header, security headers. |
| Director & agents | `fda/agents/*` | Each agent is a handler `run(ctx)` returning `{summary, state?, spawn?}`. |
| Workflow engine | `fda/orchestration/workflow.py` | Persistent DAG in PostgreSQL, executed by Celery or a local thread pool. |
| Providers | `fda/providers/*` | Adapters behind capability interfaces; registry chooses by capability and configuration. |
| Knowledge & memory | `fda/knowledge/*`, `fda/memory/*` | pgvector retrieval with trust levels; five memory categories with supersession. |
| Rendering | `fda/rendering/renderer.py`, `fda/rendering/engine/*` | Skia compositor + FFmpeg; parallel frame workers; ffprobe verification. |
| Storage | `fda/storage/store.py` | Local or S3-compatible; project-prefixed stable keys; originals kept separate. |

## Workflow engine

A **run** (`workflow_runs`) holds tasks (`workflow_tasks`) with `depends_on` lists. A dependency may be a key or a
glob (`visual:*`), so a task can wait for work that is spawned later. `dispatch()` (row-locked) queues every task
whose dependencies succeeded; `execute_task()` runs the agent, merges its `state` into the run (the checkpoint),
adds spawned tasks, writes events, and dispatches again. Failures retry with exponential back-off up to
`max_attempts` unless the error is non-retryable (missing credentials, budget, bad request). A failed task cancels
its dependents; **Resume** resets failed/cancelled tasks and continues from the checkpoint. `recover_stale()` re-queues
tasks whose worker died (no heartbeat), at API start-up and every 5 minutes via Celery beat.

Why not LangGraph: the production pipeline must survive process crashes, fan out to hundreds of per-scene jobs on
separate worker pools, and be inspected from the UI. A database-backed DAG gives that directly with Celery; the
Director's reasoning is done with structured (Pydantic-validated) model calls inside agents.

### Production run

```
analyze → research → script → voiceover → storyboard ─┬─ visual:0001 … visual:NNNN ─┐
                                                      └─ audio ──────────────────────┴─ edit → render → qc ─(repair rounds)→ finalize
```

- `analyze` decides deterministically what exists (title, brief, script, voiceover, references) and what to skip.
- `voiceover` analyses an uploaded narration (never modified) or voices the script with word timings.
- `storyboard` cuts scenes at real word timestamps (sentence ends, pauses, clause breaks), then plans each scene in
  batches with a validated schema; a heuristic planner covers any batch the model fails on, and says so.
- each `visual:N` produces one scene's asset; fallbacks are written to `scene.plan.substitution` and the event log.
- `qc` may spawn `repairN:visual:*`, `repairN:edit`, `repairN:render`, `repairN:qc` (max 2 rounds).

### Edit run (chat or timeline)

`apply_edit` applies an `EditPlan` (LLM, or rule-based fallback for EN/HI/Hinglish) and spawns only the needed
`edit_visual:N` and `audio` tasks; then `edit → render → qc → finalize`. Unaffected scenes keep their assets.

## Data model (PostgreSQL, Alembic migration `0001`)

users, user_preferences · channels, channel_connections, channel_metrics, videos · projects, project_settings,
project_versions · research_reports, research_sources · scripts, script_versions · voiceovers, transcripts,
transcript_segments · storyboards, scenes, scene_versions · assets, asset_sources, asset_licenses · timeline_items,
audio_tracks, subtitles · memories, knowledge_documents, knowledge_chunks, embeddings (vector 384) · model_providers,
model_runs, tool_runs · workflow_runs, workflow_tasks, workflow_events · budgets, usage_records · renders,
quality_reports · chat_messages · audit_logs.

JSONB is used for model outputs that vary (scene plans, clip props, QC issues); everything queried or joined is a column.

## Timeline and rendering

Track V1 holds one clip per scene, locked to narration timing; V2 holds motion-graphic overlays; T1 text; plus
subtitles (word-timed) and audio tracks (voice, music, SFX cue list, mix). The renderer converts this to a render
description; N worker processes (`python -m fda.rendering.engine.compose`) each draw a frame range with Skia —
camera moves on stills (push/pull/pan/tilt/orbit/handheld/focus-pull/ramp, framed cards for tall images),
decoded video for footage, 21 animated motion-graphic types, 11 transitions, look grade, grain/vignette, captions
in 4 styles — and pipe raw frames to x264. Parts are concatenated and muxed with the AAC mix, then probed:
codec, resolution, fps and duration must match or the render is marked failed.

## Security

- Single owner, scrypt password hash, signed HTTP-only SameSite=strict session cookie, login rate limit.
- CSRF: every state-changing `/api` request must carry `x-fda-request: 1`.
- Provider credentials and OAuth tokens encrypted with Fernet (key derived from `FDA_SECRET_KEY`), masked in responses.
- No LLM output reaches a shell: FFmpeg/Blender use fixed argument lists; Blender runs a fixed template script with
  sanitised numeric/colour/text parameters.
- External text (web pages, transcripts, uploads, YouTube metadata) is wrapped as untrusted data in prompts with a
  standing instruction never to follow it.
- Paid providers cannot run without an owner-configured limit and cost estimate; the Director cannot change limits.
- Memory refuses anything that looks like a secret.
