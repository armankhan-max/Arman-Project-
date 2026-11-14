"""Packaging Agent: titles, description with real chapter times, tags, hashtags, pinned comment and rendered thumbnails."""
import os
import re

from pydantic import BaseModel

from fda.database import models as m
from fda.permissions import budget_manager as budget
from fda.providers import registry
from fda.providers.base import ProviderError
from fda.rendering import thumbnail
from fda.services import assets
from fda.services.llm import LLM, external
from fda.storage.store import scratch_dir

from .common import latest_script, scenes, style
from .visual import normalise_image


class Thumb(BaseModel):
    idea: str
    text: str
    accent_word: str = ""
    layout: str = "hero"
    prompt: str
    hook: str = "none"
    side_text: str = ""
    style: str = ""


class Pack(BaseModel):
    titles: list[str]
    description_intro: str
    tags: list[str]
    hashtags: list[str]
    pinned_comment: str
    thumbnails: list[Thumb]


def fmt(t):
    t = int(t)
    return "%02d:%02d" % (t // 60, t % 60)


def chapters(scs, total):
    if total < 120 or len(scs) < 6:
        return []
    n = 5 if total < 600 else 8
    out, step = ["00:00 Intro"], max(1, len(scs) // n)
    for sc in scs[step::step][:n - 1]:
        name = (sc.purpose or (sc.plan or {}).get("subject") or "").strip().rstrip(".")
        if name and sc.start_s > 10:
            out.append("%s %s" % (fmt(sc.start_s), name[:48]))
    return out if len(out) >= 3 else []


def run(ctx):
    db, p = ctx.db, ctx.project
    try:
        return _run(ctx)
    except Exception as e:  # packaging must never fail a finished video
        db.rollback()
        ctx.log("Upload pack could not be created: %s" % str(e)[:300], "warn")
        return {"summary": "Upload pack skipped: %s" % str(e)[:160]}


def _run(ctx):
    db, p = ctx.db, ctx.project
    ps, st = style(db, p)
    scs = scenes(db, p.id)
    _, sv = latest_script(db, p.id)
    script = (sv.text if sv else " ".join(s.narration for s in scs))[:6000]
    persona = st.get("persona") or {}
    avatar = p.mode == "avatar"
    sys = ("You are a YouTube packaging specialist. Titles carry one honest curiosity gap the video delivers, under 70 characters, at most one ALL-CAPS word, no emojis, no brand names. "
           "Thumbnails look like a skilled editor's clean composite: one subject, one hero object, 2 to 4 bold words that ADD to the title and never repeat it; no glow, no clutter.")
    prompt = """VIDEO TITLE: %s
STYLE: %s%s
SCRIPT:
%s

Return: 6 titles; description_intro (two punchy lines with the main search phrase, then one warm paragraph of what the viewer learns%s);
20-30 search tags, most important first; 8 hashtags without spaces; a 2-4 sentence pinned comment (thank-you, one bonus detail not in the video, one easy question);
3 clearly different thumbnails, each {idea, text (2-4 words, capitals), accent_word (one word of the text), layout: "%s", hook: "arrow"|"circle"|"none",
side_text: optional 2-4 extra words (a price, a number, a short second line) or empty, style: one of %s,
prompt: describe ONLY the subject and action of the picture (the hero object large on the %s); the look is added by the chosen style; no text in the image}.
Thumbnail styles: %s. Use a different style for each of the three when it suits the channel.""" % (
        p.title, p.mode, ("\nHOST: " + str(persona.get("one_liner") or persona.get("name") or "")) if avatar else "", external(script, "script"),
        ", written in the host's first-person voice" if avatar else "", "face" if avatar else 'hero" or "split', list(thumbnail.STYLES),
        "right", "; ".join("%s = %s" % kv for kv in thumbnail.STYLES.items()))
    pack = LLM(db, p.id, "pack").structured(sys, prompt, Pack, max_tokens=2600, temperature=0.8)
    total = scs[-1].end_s if scs else 0
    ch = chapters(scs, total)
    tags, n = [], 0
    for t in pack.tags:
        if n + len(t) + 2 > 495:
            break
        tags.append(t)
        n += len(t) + 2
    hashtags = ["#" + re.sub(r"[^\w]", "", h) for h in pack.hashtags][:8]
    credits = sorted({l.attribution for s in scs if s.asset_id for l in db.query(m.AssetLicense).filter_by(asset_id=s.asset_id).all() if l.attribution})
    desc = pack.description_intro.strip()
    if ch:
        desc += "\n\nCHAPTERS\n" + "\n".join(ch)
    if credits:
        desc += "\n\nVISUAL CREDITS\n" + "\n".join(credits[:40])
    if avatar or any((s.provider or "").startswith(("pollinations", "openai", "runway", "luma", "heygen")) for s in scs):
        desc += "\n\nThis video contains AI-generated visuals" + (" and an AI-generated host." if avatar else ".")
    desc += "\n\n" + " ".join(hashtags[:3])
    # thumbnails
    work = scratch_dir(p.id, "thumbs")
    face = None
    if avatar:
        aid = st.get("avatar_image_asset")
        ch_ = db.get(m.Character, st["character_id"]) if st.get("character_id") else None
        fa = db.get(m.Asset, ch_.image_asset_id) if ch_ and ch_.image_asset_id else (db.get(m.Asset, aid) if aid else None)
        face = assets.local(fa) if fa else None
    thumbs = []
    for k, th in enumerate(pack.thumbnails[:3]):
        ctx.progress(0.4 + 0.2 * k, "Rendering thumbnail %d" % (k + 1))
        img = None
        for prov in registry.for_cap(db, "text_to_image"):
            rec = None
            try:
                rec = budget.reserve(db, prov, "thumbnail", 1, "images", p.id)
                raw = os.path.join(work, "t%d.png" % k)
                tstyle = th.style if th.style in thumbnail.STYLES else (st.get("thumb_style") or ("banner" if avatar else ["hero", "clean", "boxed"][k % 3]))
                prov.generate("%s. %s No text, no letters, no logos, no watermark." % (th.prompt.rstrip("."), thumbnail.PROMPT_STYLE[tstyle]), raw, 1280, 720, p.id.int % 9000 + k)
                budget.commit(db, rec)
                img = normalise_image(raw, raw[:-4] + ".jpg")
                break
            except (ProviderError, budget.BudgetError):
                budget.release(db, rec)
        if not img:
            continue
        out = os.path.join(work, "thumbnail_%d.png" % (k + 1))
        concept = dict(th.model_dump(), text=th.text.upper()[:32], layout="face" if face else ("hero" if th.layout not in ("hero", "split") else "hero"))
        thumbnail.compose_style(out, concept, img, face if tstyle in ("banner", "hero") else None, tstyle, st.get("thumb_accent") or "#ffd400")
        a = assets.register(db, out, p.id, "thumbnail", "thumbnails", "thumbnail_%d.png" % (k + 1), origin="generated", provider="fda-thumbnail", prompt=th.prompt,
                            settings={"text": concept["text"], "style": tstyle}, license="AI-generated picture with original typography", commercial_use="unknown", kind="image")
        thumbs.append({"asset_id": str(a.id), "idea": th.idea, "text": concept["text"], "style": tstyle})
    rep = m.ResearchReport(project_id=p.id, kind="upload_pack", query=p.title, summary=pack.titles[0] if pack.titles else p.title,
                           data={"titles": [t[:100] for t in pack.titles[:6]], "description": desc, "tags": ", ".join(tags), "hashtags": " ".join(hashtags),
                                 "pinned_comment": pack.pinned_comment, "chapters": ch, "thumbnails": thumbs,
                                 "synthetic_notice": "Answer YES to YouTube's 'Altered or synthetic content' question." if avatar else ""})
    db.add(rep)
    return {"summary": "Upload pack ready: %d titles, description, tags, %d thumbnails" % (len(pack.titles[:6]), len(thumbs))}
