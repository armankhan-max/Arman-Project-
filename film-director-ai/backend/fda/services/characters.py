"""Saved AI hosts (characters): design a persona, generate or upload the face, keep the voice."""
import os
import tempfile

from fda.database import models as m
from fda.permissions import budget_manager as budget
from fda.providers import registry
from fda.providers.base import ProviderError
from fda.services import assets
from fda.services.llm import LLM, external
from pydantic import BaseModel


class Persona(BaseModel):
    name: str
    age: int = 65
    gender: str = "female"
    heritage: str = ""
    one_liner: str = ""
    look: str
    set: str
    voice_style: str = ""
    recurring_people: list[str] = []
    signature_phrases: list[str] = []
    sign_off: str = ""


def design(db, topic, bible=""):
    sys = ("You design original fictional on-camera hosts for long-form YouTube. Never base one on a real person. The host has built-in authority from age and background. "
           "look = face, hair, glasses, jewelry and clothing only with one signature clothing color (30-45 words). set = the room they film in (15-25 words). No real town names.")
    prompt = ("PERSONA BIBLE (extract this person faithfully, do not invent a different one):\n%s" % external(bible[:6000], "persona bible")) if bible.strip() else \
        "Create the host for a channel about: %s" % topic[:600]
    p = LLM(db, None, "persona").structured(sys, prompt, Persona, max_tokens=1200, temperature=0.8).model_dump()
    p["bible"] = bible.strip() or "%s, %s, %s. %s Speaks: %s. People in their stories: %s. Says: %s. Sign-off: %s" % (
        p["name"], p["age"], p["heritage"], p["one_liner"], p["voice_style"], "; ".join(p["recurring_people"]), "; ".join(p["signature_phrases"]), p["sign_off"])
    return p


def portrait_prompt(persona):
    return ("Wide medium shot, from the waist up, of an original fictional character sitting behind a table, both hands resting on the table and holding nothing, facing the viewer: %s, about %s years old. "
            "The whole head, shoulders and chest are visible with space above the head; the person fills only the middle third of the frame; eyes open and looking straight into the lens, "
            "head level, mouth gently closed in a slight warm smile, shoulders square to camera. Behind them: %s, in sharp detail. Eye-level view from across the table, like a video call, "
            "natural window light, true-to-life skin texture, photorealistic, wide 16:9 frame, no text, no watermark.") % (
        persona.get("look", "a friendly older person with grey hair and round glasses"), persona.get("age", 65), (persona.get("set") or "a cosy lived-in kitchen").rstrip("."))


def make_portrait(db, char, seed=None):
    errors = []
    for prov in registry.for_cap(db, "text_to_image"):
        rec = None
        try:
            rec = budget.reserve(db, prov, "portrait", 1, "images", None)
            d = tempfile.mkdtemp(prefix="fda_char_")
            raw = os.path.join(d, "portrait.png")
            prov.generate(portrait_prompt(char.persona or {}), raw, 1280, 720, seed or (char.id.int % 90000))
            budget.commit(db, rec)
            from fda.agents.visual import normalise_image
            jpg = normalise_image(raw, os.path.join(d, "portrait.jpg"))
            a = assets.register(db, jpg, None, "character", "characters", "%s.jpg" % char.name[:40], origin="generated", provider=prov.name,
                                prompt=portrait_prompt(char.persona or {}), license="AI-generated (%s terms)" % prov.label, commercial_use="unknown", kind="image",
                                meta={"ai_generated": True, "character_id": str(char.id)})
            char.image_asset_id = a.id
            char.external = {k: v for k, v in (char.external or {}).items() if k != "heygen_talking_photo_id"}
            return a
        except (ProviderError, budget.BudgetError) as e:
            budget.release(db, rec)
            errors.append(str(e)[:160])
    raise ProviderError("Could not generate the portrait: %s" % "; ".join(errors), retryable=False)


def apply_to_style(char, st):
    st = dict(st)
    st["character_id"] = str(char.id)
    st["persona"] = dict(char.persona or {}, name=char.name)
    if char.image_asset_id:
        st["avatar_image_asset"] = str(char.image_asset_id)
    if char.voice:
        st["voice"], st["voice_rate"], st["voice_pitch"] = char.voice, char.voice_rate, char.voice_pitch
    if char.tts_provider:
        st["tts_provider"] = char.tts_provider
    return st
