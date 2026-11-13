"""Structured outputs exchanged between the Director and specialist agents."""
from typing import Literal, Optional

from pydantic import BaseModel, Field

VisualType = Literal["stock_video", "ai_video", "ai_image", "archive", "stock_image", "blender", "motion_graphic", "avatar", "user"]
Shot = Literal["extreme_wide", "wide", "medium", "close_up", "extreme_close_up", "macro", "pov", "aerial", "over_shoulder", "insert"]
Movement = Literal["static", "push_in", "pull_out", "pan_left", "pan_right", "tilt_up", "tilt_down", "tracking", "orbit", "handheld", "drone", "dolly_zoom", "crane"]
Transition = Literal["cut", "fade", "dip", "flash", "zoom", "push", "slide", "wipe", "glitch", "burn"]


class InputAnalysis(BaseModel):
    has_title: bool
    has_brief: bool
    has_script: bool
    has_voiceover: bool
    has_reference_media: bool
    needs_research: bool
    needs_script: bool
    needs_transcription: bool
    preserve_narration: bool
    mode: str
    language: str
    target_minutes: float
    notes: list[str] = []


class Finding(BaseModel):
    claim: str
    status: Literal["confirmed", "disputed", "speculative", "unverified"]
    source_indexes: list[int] = Field(default_factory=list, description="1-based indexes into the numbered sources list; empty if none supports it")
    visual_ideas: list[str] = []


class ResearchOut(BaseModel):
    summary: str
    findings: list[Finding]
    conflicts: list[str] = []
    inaccuracies_to_avoid: list[str] = []


class Chapter(BaseModel):
    title: str
    summary: str
    words: int


class OutlineOut(BaseModel):
    title: str
    logline: str
    hook: str
    big_question: str
    chapters: list[Chapter]


class ScenePlan(BaseModel):
    n: int = Field(description="scene number as given")
    purpose: str
    visual_type: VisualType
    description: str
    subject: str
    environment: str
    shot: Shot
    angle: str
    movement: Movement
    lens: str
    lighting: str
    color: str
    subject_motion: str = ""
    background: str = ""
    sfx: list[str] = []
    music: str = ""
    transition: Transition = "cut"
    prompt: str = Field(description="detailed generation prompt for image/video models; no on-screen text")
    negative_prompt: str = ""
    search_query: str = Field(description="2-5 concrete words for stock/archive search")
    motion_graphic: Optional[dict] = Field(default=None, description="only for visual_type motion_graphic: {type, ...data}")
    blender_template: Optional[str] = None
    blender_params: Optional[dict] = None
    continuity_refs: list[str] = []


class StoryboardBatch(BaseModel):
    scenes: list[ScenePlan]


class Continuity(BaseModel):
    characters: list[dict] = []
    places: list[dict] = []
    objects: list[dict] = []
    palette: str = ""
    look: str = ""


class EditOp(BaseModel):
    op: Literal["regenerate_scene", "change_camera", "change_visual_type", "change_prompt", "change_transition", "music_volume", "sfx_volume",
                "voice_enhance", "resync_subtitles", "change_duration", "more_engaging_opening", "change_caption_style", "change_look", "render", "note"]
    scenes: list[int] = []
    value: Optional[str] = None
    number: Optional[float] = None
    reason: str = ""


class EditPlan(BaseModel):
    understood: str
    ops: list[EditOp]
    needs_render: bool = True


class DirectorIntent(BaseModel):
    intent: Literal["produce", "edit", "research", "youtube_research", "question", "remember", "render", "status"]
    title: str = ""
    brief: str = ""
    mode: str = ""
    language: str = ""
    target_minutes: Optional[float] = None
    preserve_narration: Optional[bool] = None
    reply: str = ""
    remember: list[dict] = []
