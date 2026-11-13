"""Relational schema. Flexible model outputs live in JSONB columns; everything the app queries or joins on is a real column."""
import uuid
from datetime import datetime, timezone

from pgvector.sqlalchemy import Vector
from sqlalchemy import (BigInteger, Boolean, DateTime, Float, ForeignKey, Index, Integer, LargeBinary, Numeric, String, Text,
                        UniqueConstraint, func)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

EMBED_DIM = 384


def now():
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


def pk():
    return mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


def fk(target, ondelete="CASCADE", nullable=False, index=True):
    return mapped_column(UUID(as_uuid=True), ForeignKey(target, ondelete=ondelete), nullable=nullable, index=index)


class Timestamps:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now, server_default=func.now(), nullable=False)


# ------------------------------------------------------------------ owner
class User(Base, Timestamps):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = pk()
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_owner: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class UserPreference(Base, Timestamps):
    __tablename__ = "user_preferences"
    __table_args__ = (UniqueConstraint("user_id", "key"),)
    id: Mapped[uuid.UUID] = pk()
    user_id = fk("users.id")
    key: Mapped[str] = mapped_column(String(120), nullable=False)
    value: Mapped[dict] = mapped_column(JSONB, nullable=False)
    confirmed: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    source: Mapped[str] = mapped_column(String(60), default="owner", nullable=False)


# ------------------------------------------------------------------ youtube
class Channel(Base, Timestamps):
    __tablename__ = "channels"
    id: Mapped[uuid.UUID] = pk()
    youtube_channel_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(300), default="")
    is_own: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    niche: Mapped[str | None] = mapped_column(Text)
    meta: Mapped[dict] = mapped_column(JSONB, default=dict)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ChannelConnection(Base, Timestamps):
    __tablename__ = "channel_connections"
    id: Mapped[uuid.UUID] = pk()
    user_id = fk("users.id")
    channel_id = fk("channels.id", nullable=True)
    provider: Mapped[str] = mapped_column(String(40), default="google", nullable=False)
    scopes: Mapped[str] = mapped_column(Text, default="")
    token_encrypted: Mapped[bytes | None] = mapped_column(LargeBinary)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(30), default="pending", nullable=False)
    last_error: Mapped[str | None] = mapped_column(Text)


class ChannelMetric(Base):
    __tablename__ = "channel_metrics"
    __table_args__ = (Index("ix_metric_lookup", "channel_id", "video_id", "metric", "period_start"),)
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    channel_id = fk("channels.id")
    video_id: Mapped[str | None] = mapped_column(String(32))
    metric: Mapped[str] = mapped_column(String(80), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    period_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    dimension: Mapped[str | None] = mapped_column(String(120))
    source: Mapped[str] = mapped_column(String(60), nullable=False)   # youtube_data_api | youtube_analytics_api
    scope: Mapped[str] = mapped_column(String(30), nullable=False)    # public | authorized
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, nullable=False)


class Video(Base, Timestamps):
    __tablename__ = "videos"
    id: Mapped[uuid.UUID] = pk()
    youtube_video_id: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    channel_id = fk("channels.id", ondelete="SET NULL", nullable=True)
    title: Mapped[str] = mapped_column(Text, default="")
    description: Mapped[str] = mapped_column(Text, default="")
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    duration_s: Mapped[int | None] = mapped_column(Integer)
    view_count: Mapped[int | None] = mapped_column(BigInteger)
    like_count: Mapped[int | None] = mapped_column(BigInteger)
    comment_count: Mapped[int | None] = mapped_column(BigInteger)
    tags: Mapped[list] = mapped_column(JSONB, default=list)
    snapshot_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source: Mapped[str] = mapped_column(String(60), default="youtube_data_api")


# ------------------------------------------------------------------ projects
class Project(Base, Timestamps):
    __tablename__ = "projects"
    id: Mapped[uuid.UUID] = pk()
    user_id = fk("users.id")
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    brief: Mapped[str] = mapped_column(Text, default="")
    mode: Mapped[str] = mapped_column(String(40), default="documentary", nullable=False)
    language: Mapped[str] = mapped_column(String(20), default="en", nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="draft", nullable=False, index=True)
    current_version: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    preserve_narration: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    settings: Mapped["ProjectSettings"] = relationship(back_populates="project", uselist=False, cascade="all, delete-orphan")


class ProjectSettings(Base, Timestamps):
    __tablename__ = "project_settings"
    id: Mapped[uuid.UUID] = pk()
    project_id = fk("projects.id")
    width: Mapped[int] = mapped_column(Integer, default=1920)
    height: Mapped[int] = mapped_column(Integer, default=1080)
    fps: Mapped[int] = mapped_column(Integer, default=30)
    target_minutes: Mapped[float] = mapped_column(Float, default=3.0)
    style: Mapped[dict] = mapped_column(JSONB, default=dict)   # look, captions, music mood, pace, voice, sources …
    project: Mapped[Project] = relationship(back_populates="settings")


class ProjectVersion(Base):
    __tablename__ = "project_versions"
    __table_args__ = (UniqueConstraint("project_id", "version"),)
    id: Mapped[uuid.UUID] = pk()
    project_id = fk("projects.id")
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(Text, default="")
    snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False)  # scenes + timeline + audio + subtitles at that point
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, nullable=False)


# ------------------------------------------------------------------ research
class ResearchReport(Base, Timestamps):
    __tablename__ = "research_reports"
    id: Mapped[uuid.UUID] = pk()
    project_id = fk("projects.id", nullable=True)
    kind: Mapped[str] = mapped_column(String(40), default="topic")  # topic | youtube_public | youtube_channel
    query: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str] = mapped_column(Text, default="")
    findings: Mapped[list] = mapped_column(JSONB, default=list)   # [{claim, status, source_ids}]
    data: Mapped[dict] = mapped_column(JSONB, default=dict)


class ResearchSource(Base):
    __tablename__ = "research_sources"
    id: Mapped[uuid.UUID] = pk()
    report_id = fk("research_reports.id")
    url: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, default="")
    publisher: Mapped[str] = mapped_column(String(200), default="")
    published_at: Mapped[str | None] = mapped_column(String(40))
    excerpt: Mapped[str] = mapped_column(Text, default="")
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, nullable=False)


# ------------------------------------------------------------------ script & narration
class Script(Base, Timestamps):
    __tablename__ = "scripts"
    id: Mapped[uuid.UUID] = pk()
    project_id = fk("projects.id")
    current_version: Mapped[int] = mapped_column(Integer, default=1)
    origin: Mapped[str] = mapped_column(String(30), default="generated")  # generated | user | transcript


class ScriptVersion(Base):
    __tablename__ = "script_versions"
    __table_args__ = (UniqueConstraint("script_id", "version"),)
    id: Mapped[uuid.UUID] = pk()
    script_id = fk("scripts.id")
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    outline: Mapped[dict] = mapped_column(JSONB, default=dict)
    note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, nullable=False)


class Voiceover(Base, Timestamps):
    __tablename__ = "voiceovers"
    id: Mapped[uuid.UUID] = pk()
    project_id = fk("projects.id")
    origin: Mapped[str] = mapped_column(String(20), nullable=False)  # upload | tts
    original_asset_id = fk("assets.id", ondelete="RESTRICT", nullable=True)
    processed_asset_id = fk("assets.id", ondelete="SET NULL", nullable=True)
    duration_s: Mapped[float | None] = mapped_column(Float)
    sample_rate: Mapped[int | None] = mapped_column(Integer)
    channels: Mapped[int | None] = mapped_column(Integer)
    codec: Mapped[str | None] = mapped_column(String(40))
    analysis: Mapped[dict] = mapped_column(JSONB, default=dict)  # loudness, peak, silences, pace


class Transcript(Base, Timestamps):
    __tablename__ = "transcripts"
    id: Mapped[uuid.UUID] = pk()
    voiceover_id = fk("voiceovers.id")
    language: Mapped[str | None] = mapped_column(String(20))
    text: Mapped[str] = mapped_column(Text, default="")
    word_level: Mapped[bool] = mapped_column(Boolean, default=False)
    provider: Mapped[str] = mapped_column(String(60), default="")
    words: Mapped[list] = mapped_column(JSONB, default=list)  # [{w,s,e,p}]


class TranscriptSegment(Base):
    __tablename__ = "transcript_segments"
    id: Mapped[uuid.UUID] = pk()
    transcript_id = fk("transcripts.id")
    idx: Mapped[int] = mapped_column(Integer, nullable=False)
    start_s: Mapped[float] = mapped_column(Float, nullable=False)
    end_s: Mapped[float] = mapped_column(Float, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    word_start: Mapped[int] = mapped_column(Integer, default=0)
    word_end: Mapped[int] = mapped_column(Integer, default=0)
    pause_after_s: Mapped[float] = mapped_column(Float, default=0)


# ------------------------------------------------------------------ storyboard
class Storyboard(Base, Timestamps):
    __tablename__ = "storyboards"
    id: Mapped[uuid.UUID] = pk()
    project_id = fk("projects.id")
    version: Mapped[int] = mapped_column(Integer, default=1)
    continuity: Mapped[dict] = mapped_column(JSONB, default=dict)  # recurring characters, places, objects, palette
    notes: Mapped[str] = mapped_column(Text, default="")


class Scene(Base, Timestamps):
    __tablename__ = "scenes"
    __table_args__ = (UniqueConstraint("storyboard_id", "idx"),)
    id: Mapped[uuid.UUID] = pk()
    storyboard_id = fk("storyboards.id")
    project_id = fk("projects.id")
    idx: Mapped[int] = mapped_column(Integer, nullable=False)
    start_s: Mapped[float] = mapped_column(Float, nullable=False)
    end_s: Mapped[float] = mapped_column(Float, nullable=False)
    narration: Mapped[str] = mapped_column(Text, default="")
    word_start: Mapped[int | None] = mapped_column(Integer)
    word_end: Mapped[int | None] = mapped_column(Integer)
    purpose: Mapped[str] = mapped_column(Text, default="")
    visual_type: Mapped[str] = mapped_column(String(30), default="stock_video")  # stock_video|ai_video|ai_image|archive|blender|motion_graphic|avatar|user
    plan: Mapped[dict] = mapped_column(JSONB, default=dict)  # description, subject, environment, shot, angle, movement, lens, lighting, color, sfx, music, transition, prompt, negative_prompt, mg
    provider: Mapped[str | None] = mapped_column(String(60))
    asset_id = fk("assets.id", ondelete="SET NULL", nullable=True)
    asset_status: Mapped[str] = mapped_column(String(20), default="pending")  # pending|generating|ready|failed
    quality_status: Mapped[str] = mapped_column(String(20), default="unchecked")
    version: Mapped[int] = mapped_column(Integer, default=1)
    last_error: Mapped[str | None] = mapped_column(Text)


class SceneVersion(Base):
    __tablename__ = "scene_versions"
    id: Mapped[uuid.UUID] = pk()
    scene_id = fk("scenes.id")
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    plan: Mapped[dict] = mapped_column(JSONB, nullable=False)
    asset_id = fk("assets.id", ondelete="SET NULL", nullable=True)
    reason: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, nullable=False)


# ------------------------------------------------------------------ assets
class Asset(Base, Timestamps):
    __tablename__ = "assets"
    id: Mapped[uuid.UUID] = pk()
    project_id = fk("projects.id", ondelete="CASCADE", nullable=True)
    kind: Mapped[str] = mapped_column(String(20), nullable=False)  # video|image|audio|blend|caption|document|render
    role: Mapped[str] = mapped_column(String(30), default="scene")  # upload_original|processed|scene|music|sfx|render|blender_project
    storage_key: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    filename: Mapped[str] = mapped_column(String(300), default="")
    content_type: Mapped[str] = mapped_column(String(120), default="")
    size_bytes: Mapped[int] = mapped_column(BigInteger, default=0)
    sha256: Mapped[str | None] = mapped_column(String(64), index=True)
    width: Mapped[int | None] = mapped_column(Integer)
    height: Mapped[int | None] = mapped_column(Integer)
    duration_s: Mapped[float | None] = mapped_column(Float)
    meta: Mapped[dict] = mapped_column(JSONB, default=dict)
    parent_id = fk("assets.id", ondelete="SET NULL", nullable=True)


class AssetSource(Base):
    __tablename__ = "asset_sources"
    id: Mapped[uuid.UUID] = pk()
    asset_id = fk("assets.id")
    origin: Mapped[str] = mapped_column(String(30), nullable=False)  # generated|stock|archive|upload|blender|procedural|tts
    provider: Mapped[str] = mapped_column(String(60), default="")
    source_url: Mapped[str | None] = mapped_column(Text)
    prompt: Mapped[str | None] = mapped_column(Text)
    settings: Mapped[dict] = mapped_column(JSONB, default=dict)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, nullable=False)


class AssetLicense(Base):
    __tablename__ = "asset_licenses"
    id: Mapped[uuid.UUID] = pk()
    asset_id = fk("assets.id")
    license: Mapped[str] = mapped_column(String(120), nullable=False)
    attribution: Mapped[str] = mapped_column(Text, default="")
    commercial_use: Mapped[str] = mapped_column(String(20), default="unknown")  # yes|no|unknown
    terms_url: Mapped[str | None] = mapped_column(Text)


# ------------------------------------------------------------------ timeline
class TimelineItem(Base, Timestamps):
    __tablename__ = "timeline_items"
    __table_args__ = (Index("ix_timeline_project_track", "project_id", "track", "start_s"),)
    id: Mapped[uuid.UUID] = pk()
    project_id = fk("projects.id")
    scene_id = fk("scenes.id", ondelete="SET NULL", nullable=True)
    asset_id = fk("assets.id", ondelete="SET NULL", nullable=True)
    track: Mapped[str] = mapped_column(String(20), nullable=False)  # V1 V2 (overlays) T1 (text)
    kind: Mapped[str] = mapped_column(String(20), nullable=False)   # video|image|motion_graphic|avatar|text|blender
    start_s: Mapped[float] = mapped_column(Float, nullable=False)
    duration_s: Mapped[float] = mapped_column(Float, nullable=False)
    in_s: Mapped[float] = mapped_column(Float, default=0.0)
    props: Mapped[dict] = mapped_column(JSONB, default=dict)  # motion, focus, transition, tdur, filter, speed, scale, x, y, opacity, crop, mg, text…


class AudioTrack(Base, Timestamps):
    __tablename__ = "audio_tracks"
    id: Mapped[uuid.UUID] = pk()
    project_id = fk("projects.id")
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # voice|music|sfx|ambience|mix
    asset_id = fk("assets.id", ondelete="SET NULL", nullable=True)
    volume: Mapped[float] = mapped_column(Float, default=1.0)
    muted: Mapped[bool] = mapped_column(Boolean, default=False)
    props: Mapped[dict] = mapped_column(JSONB, default=dict)  # cues, sections, ducking, fades


class Subtitle(Base):
    __tablename__ = "subtitles"
    __table_args__ = (Index("ix_subtitles_project_start", "project_id", "start_s"),)
    id: Mapped[uuid.UUID] = pk()
    project_id = fk("projects.id")
    idx: Mapped[int] = mapped_column(Integer, nullable=False)
    start_s: Mapped[float] = mapped_column(Float, nullable=False)
    end_s: Mapped[float] = mapped_column(Float, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    words: Mapped[list] = mapped_column(JSONB, default=list)


# ------------------------------------------------------------------ memory & knowledge
class Memory(Base, Timestamps):
    __tablename__ = "memories"
    id: Mapped[uuid.UUID] = pk()
    user_id = fk("users.id")
    category: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # preference|channel|project|production|performance
    project_id = fk("projects.id", nullable=True)
    key: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    data: Mapped[dict] = mapped_column(JSONB, default=dict)
    status: Mapped[str] = mapped_column(String(20), default="confirmed")  # confirmed|inferred|superseded
    source: Mapped[str] = mapped_column(String(120), default="owner")
    supersedes_id = fk("memories.id", ondelete="SET NULL", nullable=True)
    embedding = mapped_column(Vector(EMBED_DIM), nullable=True)


class KnowledgeDocument(Base, Timestamps):
    __tablename__ = "knowledge_documents"
    id: Mapped[uuid.UUID] = pk()
    project_id = fk("projects.id", nullable=True)
    title: Mapped[str] = mapped_column(Text, default="")
    source_type: Mapped[str] = mapped_column(String(30), nullable=False)  # upload|web|research|youtube|script|qc
    trust: Mapped[str] = mapped_column(String(20), default="unverified")  # verified|user_provided|inferred|unverified|outdated
    source_url: Mapped[str | None] = mapped_column(Text)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    meta: Mapped[dict] = mapped_column(JSONB, default=dict)


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"
    id: Mapped[uuid.UUID] = pk()
    document_id = fk("knowledge_documents.id")
    idx: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    tokens: Mapped[int] = mapped_column(Integer, default=0)


class Embedding(Base):
    __tablename__ = "embeddings"
    __table_args__ = (UniqueConstraint("chunk_id", "model"),)
    id: Mapped[uuid.UUID] = pk()
    chunk_id = fk("knowledge_chunks.id")
    model: Mapped[str] = mapped_column(String(80), nullable=False)
    vector = mapped_column(Vector(EMBED_DIM), nullable=False)


# ------------------------------------------------------------------ providers & runs
class ModelProvider(Base, Timestamps):
    __tablename__ = "model_providers"
    id: Mapped[uuid.UUID] = pk()
    name: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    credentials_encrypted: Mapped[bytes | None] = mapped_column(LargeBinary)
    config: Mapped[dict] = mapped_column(JSONB, default=dict)  # model choices, cost estimates set by the owner
    status: Mapped[str] = mapped_column(String(30), default="unconfigured")  # unconfigured|ok|invalid|error
    status_detail: Mapped[str | None] = mapped_column(Text)
    checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ModelRun(Base):
    __tablename__ = "model_runs"
    id: Mapped[uuid.UUID] = pk()
    project_id = fk("projects.id", ondelete="SET NULL", nullable=True)
    provider: Mapped[str] = mapped_column(String(60), nullable=False)
    model: Mapped[str] = mapped_column(String(120), default="")
    purpose: Mapped[str] = mapped_column(String(80), default="")
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    ok: Mapped[bool] = mapped_column(Boolean, default=True)
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, nullable=False, index=True)


class ToolRun(Base):
    __tablename__ = "tool_runs"
    id: Mapped[uuid.UUID] = pk()
    project_id = fk("projects.id", ondelete="SET NULL", nullable=True)
    task_id = fk("workflow_tasks.id", ondelete="SET NULL", nullable=True)
    tool: Mapped[str] = mapped_column(String(80), nullable=False)
    args: Mapped[dict] = mapped_column(JSONB, default=dict)
    result: Mapped[dict] = mapped_column(JSONB, default=dict)
    ok: Mapped[bool] = mapped_column(Boolean, default=True)
    error: Mapped[str | None] = mapped_column(Text)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, nullable=False)


# ------------------------------------------------------------------ workflow
class WorkflowRun(Base, Timestamps):
    __tablename__ = "workflow_runs"
    id: Mapped[uuid.UUID] = pk()
    project_id = fk("projects.id")
    kind: Mapped[str] = mapped_column(String(40), nullable=False)  # produce|edit|render|repair|research
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)  # pending|running|succeeded|failed|cancelled|waiting_approval
    plan: Mapped[dict] = mapped_column(JSONB, default=dict)
    state: Mapped[dict] = mapped_column(JSONB, default=dict)  # checkpointed shared state
    error: Mapped[str | None] = mapped_column(Text)
    cancel_requested: Mapped[bool] = mapped_column(Boolean, default=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class WorkflowTask(Base, Timestamps):
    __tablename__ = "workflow_tasks"
    __table_args__ = (UniqueConstraint("run_id", "key"),)
    id: Mapped[uuid.UUID] = pk()
    run_id = fk("workflow_runs.id")
    key: Mapped[str] = mapped_column(String(80), nullable=False)
    agent: Mapped[str] = mapped_column(String(40), nullable=False)
    queue: Mapped[str] = mapped_column(String(30), default="default")
    depends_on: Mapped[list] = mapped_column(JSONB, default=list)
    params: Mapped[dict] = mapped_column(JSONB, default=dict)
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)  # pending|queued|running|succeeded|failed|skipped|cancelled
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3)
    timeout_s: Mapped[int] = mapped_column(Integer, default=3600)
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    message: Mapped[str] = mapped_column(Text, default="")
    output: Mapped[dict] = mapped_column(JSONB, default=dict)
    error: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class WorkflowEvent(Base):
    __tablename__ = "workflow_events"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    run_id = fk("workflow_runs.id")
    task_key: Mapped[str | None] = mapped_column(String(80))
    level: Mapped[str] = mapped_column(String(10), default="info")
    message: Mapped[str] = mapped_column(Text, nullable=False)
    data: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, nullable=False, index=True)


# ------------------------------------------------------------------ budget
class Budget(Base, Timestamps):
    __tablename__ = "budgets"
    __table_args__ = (UniqueConstraint("scope", "scope_ref"),)
    id: Mapped[uuid.UUID] = pk()
    scope: Mapped[str] = mapped_column(String(20), nullable=False)  # daily|monthly|project|provider
    scope_ref: Mapped[str] = mapped_column(String(80), default="")   # project id or provider name
    limit_usd: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class UsageRecord(Base):
    __tablename__ = "usage_records"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    project_id = fk("projects.id", ondelete="SET NULL", nullable=True)
    provider: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    operation: Mapped[str] = mapped_column(String(80), nullable=False)
    units: Mapped[float] = mapped_column(Float, default=0)
    unit: Mapped[str] = mapped_column(String(30), default="")
    estimated_usd: Mapped[float | None] = mapped_column(Numeric(12, 4))
    actual_usd: Mapped[float | None] = mapped_column(Numeric(12, 4))
    status: Mapped[str] = mapped_column(String(20), default="reserved")  # reserved|committed|released
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, nullable=False, index=True)


# ------------------------------------------------------------------ render & qc
class Render(Base, Timestamps):
    __tablename__ = "renders"
    id: Mapped[uuid.UUID] = pk()
    project_id = fk("projects.id")
    project_version: Mapped[int] = mapped_column(Integer, nullable=False)
    kind: Mapped[str] = mapped_column(String(20), default="final")  # preview|final
    status: Mapped[str] = mapped_column(String(20), default="pending")
    settings: Mapped[dict] = mapped_column(JSONB, default=dict)
    asset_id = fk("assets.id", ondelete="SET NULL", nullable=True)
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    probe: Mapped[dict] = mapped_column(JSONB, default=dict)
    error: Mapped[str | None] = mapped_column(Text)


class QualityReport(Base):
    __tablename__ = "quality_reports"
    id: Mapped[uuid.UUID] = pk()
    project_id = fk("projects.id")
    render_id = fk("renders.id", ondelete="SET NULL", nullable=True)
    passed: Mapped[bool] = mapped_column(Boolean, default=False)
    issues: Mapped[list] = mapped_column(JSONB, default=list)  # [{check, severity, scene_idx, description, repair, auto_repairable, repaired}]
    stats: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, nullable=False)


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id: Mapped[uuid.UUID] = pk()
    project_id = fk("projects.id", nullable=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # user|director|system
    content: Mapped[str] = mapped_column(Text, nullable=False)
    data: Mapped[dict] = mapped_column(JSONB, default=dict)  # attachments, actions taken, run ids
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, nullable=False, index=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    actor: Mapped[str] = mapped_column(String(60), nullable=False)  # owner|director|system|worker
    action: Mapped[str] = mapped_column(String(80), nullable=False)
    target: Mapped[str] = mapped_column(String(200), default="")
    detail: Mapped[dict] = mapped_column(JSONB, default=dict)
    ip: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, nullable=False, index=True)


class StoredFile(Base):
    """File bytes kept in PostgreSQL (storage backend 'db'), so uploads and renders survive container restarts."""
    __tablename__ = "stored_files"
    key: Mapped[str] = mapped_column(Text, primary_key=True)
    data: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, server_default=func.now(), nullable=False)
