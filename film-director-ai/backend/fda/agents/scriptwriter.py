"""Scriptwriter Agent: outline → chapters written for the ear, in English, Hindi or Hinglish."""
from concurrent.futures import ThreadPoolExecutor

from fda.database import models as m
from fda.database.session import SessionLocal
from fda.memory.store import as_context, recall
from fda.schemas.agents import OutlineOut
from fda.services.llm import LLM, external

from .common import clean_narration, latest_script, style, words

WPM = 145  # avatar scripts use 140
RULES = """Write narration that will be read aloud.
- Output only the spoken words: no headings, labels, stage directions, brackets, lists or markdown.
- Flowing spoken sentences of mixed length; never strings of tiny fragments.
- Write numbers, symbols and units as words a voice reads naturally.
- Do not repeat the same point. Each paragraph moves the story forward.
- Never invent quotes, statistics or dates. If a fact is uncertain, say so in the narration or leave it out.
- No cliché AI phrases (delve, tapestry, testament, unlock, buckle up, let's dive in, in conclusion)."""
STYLE = {
    "documentary": "Cinematic documentary. Open inside the most dramatic moment, then rewind. Precise, calm, curiosity-building.",
    "historical": "Historical documentary. Dates, places, period detail, why each event mattered. Respectful and vivid.",
    "faceless": "Faceless narration. Second person where it helps, clear story spine, strong open loops.",
    "educational": "Educational explainer. One driving question, analogies from daily life, step by step with the why.",
    "science": "Science documentary. Wonder first, then mechanism. Scale comparisons the viewer can feel. Separate known from uncertain.",
    "realistic": "Cinematic, sensory, scene-led narration.",
    "avatar": ("An older host with lived experience talking straight to camera across a kitchen table, first person. Every line must sound like a real, warm, slightly funny person talking to one friend. "
               "HOOK: open inside a scene (the viewer's own frustration in vivid detail, a surprising concrete claim with a number, or a tiny story with tension), never a greeting. In the first 20 seconds absolve the viewer "
               "('it was never your fault'), say what they will get, and open the big loop that is paid off at the end. Introduce the host by name only after the hook with one personal detail, never a credential. "
               "RETENTION: a new tease every 60 to 90 seconds and close every one; bridges that pull forward; one true twist around two thirds; the strongest secret last; the ending calls back to the opening. "
               "Teach the WHY behind every trick in plain words. Dry, gentle, personal humor and short family stories with the recurring people from the persona. Name concrete objects and actions often so matching pictures can be made. "
               "Every method must be correct and safe for a normal home with the real safety warning where it applies; if a popular trick is a myth, say so. No brand names, no medical, legal or investment advice. "
               "One mid-video ask phrased as a small favor between 35 and 55 percent. End with a warm human recap, one small homework, one question for the comments, a one-line tease of a related video, and the host's exact sign-off as the last line. "
               "Mostly medium and long flowing sentences joined by and, but, so, because; never more than one short fragment in a row; at most three ellipses; no colons inside spoken lines. Years are written as spoken."),
    "anim2d": "Story-driven narration with simple, visual beats a character can act out.",
    "blender3d": "Scientific visual narration: each sentence describes something that can be shown in 3D.",
    "motion_graphics": "Punchy explainer where numbers, comparisons and lists carry the story.",
    "hybrid": "Cinematic documentary that mixes story, explanation and data.",
    "short": "Vertical short: hook in the first five words, one idea, end on the payoff.",
}


def lang_line(lang):
    return {"hi": "Write in Hindi (Devanagari script).", "hinglish": "Write in Hinglish: conversational Hindi written in Latin letters with natural English words mixed in."}.get(
        lang, "Write in English.")


def context_for(db, project, user_id):
    from fda.knowledge.retrieval import as_context as kctx, search
    rep = db.query(m.ResearchReport).filter_by(project_id=project.id).order_by(m.ResearchReport.created_at.desc()).first()
    facts = ""
    if rep:
        facts = rep.summary + "\n" + "\n".join("- (%s) %s" % (f["status"], f["claim"]) for f in rep.findings[:16])
    prefs = as_context(recall(db, user_id, "narration style script tone pacing", "preference", k=8))
    know = kctx(search(db, project.title, 5, project.id, include_global=False, source_types=["upload"]))
    return facts, prefs, know


def run(ctx):
    db, p = ctx.db, ctx.project
    a = ctx.state.get("analysis", {})
    sc, cur = latest_script(db, p.id)
    if cur and not ctx.params.get("rewrite"):
        return {"skipped": True, "summary": "Using the existing %s script (%d words)" % (sc.origin, len(words(cur.text)))}
    if a.get("has_voiceover") and not ctx.params.get("rewrite"):
        return {"skipped": True, "summary": "Narration comes from the uploaded voiceover"}
    ps, st = style(db, p)
    total = int(ps.target_minutes * (140 if p.mode == "avatar" else WPM))
    facts, prefs, know = context_for(db, p, p.user_id)
    persona = st.get("persona") or {}
    if p.mode == "avatar" and persona:
        prefs = (prefs + "\n" if prefs else "") + "HOST PERSONA (write in this person's voice): " + (persona.get("bible") or str({k: v for k, v in persona.items() if k != "bible"}))[:3000]
    llm = LLM(db, p.id, "script")
    n = max(1, min(30, round(ps.target_minutes / 1.5)))
    ctx.progress(0.05, "Outlining")
    sys = "You plan YouTube videos that hold attention to the end. " + STYLE.get(p.mode, STYLE["documentary"]) + " " + lang_line(p.language)
    o = llm.structured(sys, """Video title: %s
Brief: %s
Owner preferences:
%s
Research (statuses matter; unverified claims must be hedged):
%s
%s
Plan about %d words of narration in %d chapters. Chapter 1 is the cold open; the last pays off the big question.""" % (
        p.title, p.brief[:3000], prefs or "(none saved)", external(facts or "(no research)", "research"), external(know, "owner documents") if know else "", total, n),
        OutlineOut, max_tokens=2500)
    chs = o.chapters or []
    s = sum(max(40, c.words) for c in chs) or 1
    for c in chs:
        c.words = max(40, int(max(40, c.words) * total / s))
    texts = [None] * len(chs)
    host = ("HOST PERSONA: " + (persona.get("bible") or str(persona))[:2000] + "\n") if p.mode == "avatar" and persona else ""

    def write(i):
        d = SessionLocal()
        try:
            c = chs[i]
            pos = ("OPENING chapter: start inside the scene, no greeting, hook in the first two sentences, open the big question." if i == 0 else
                   "FINAL chapter: answer the big question, end with one clean memorable line." if i == len(chs) - 1 else
                   "Middle chapter: continue directly, no recap, end with a line that pulls into the next chapter.")
            txt = LLM(d, p.id, "script").complete(RULES + "\n" + STYLE.get(p.mode, "") + "\n" + lang_line(p.language),
                                                    ("VIDEO: %s\nHOOK: %s\nBIG QUESTION: %s\nCHAPTERS: %s\n" + host.replace("%", "%%") + "FACTS:\n%s\n\nWrite chapter %d of %d, \"%s\": %s\n%s\nAbout %d words.") % (
                                                        o.title, o.hook, o.big_question, " | ".join(x.title for x in chs), external(facts[:2500], "research"),
                                                        i + 1, len(chs), c.title, c.summary, pos, c.words), max_tokens=int(c.words * 2.5) + 400, temperature=0.8)
            d.commit()
            texts[i] = clean_narration(txt)
        finally:
            d.close()
    done = [0]

    def job(i):
        write(i)
        done[0] += 1
    with ThreadPoolExecutor(3) as ex:
        for i, _ in enumerate(ex.map(job, range(len(chs)))):
            pass
    ctx.progress(0.9, "Saving script")
    text = "\n\n".join(t for t in texts if t)
    sc = sc or m.Script(project_id=p.id, origin="generated", current_version=0)
    db.add(sc)
    db.flush()
    sc.current_version += 1
    db.add(m.ScriptVersion(script_id=sc.id, version=sc.current_version, text=text, outline=o.model_dump(), note="Generated by Scriptwriter"))
    if not p.title or p.title == "Untitled":
        p.title = o.title[:300]
    return {"summary": "Script written: %d words in %d chapters (target %d)" % (len(words(text)), len(chs), total), "state": {"outline": o.model_dump()}}
