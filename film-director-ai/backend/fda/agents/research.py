"""Research Agent: gathers sources, separates confirmed facts from speculation, and stores a cited report."""
from fda.database import models as m
from fda.knowledge.ingestion import ingest
from fda.providers import registry
from fda.providers.base import ProviderError
from fda.schemas.agents import ResearchOut
from fda.services.llm import LLM, external


def gather(db, query, n=6):
    sources, errors = [], []
    for p in registry.for_cap(db, "web_search"):
        try:
            for r in p.search(query, n):
                if r.get("url") and r["url"] not in {s["url"] for s in sources} and r.get("content"):
                    sources.append(r)
        except ProviderError as e:
            errors.append("%s: %s" % (p.label, e))
        if len(sources) >= n:
            break
    return sources[:n], errors


def research(db, query, project_id=None, kind="topic", user_id=None):
    sources, errors = gather(db, query)
    llm = LLM(db, project_id, "research")
    numbered = "\n\n".join("[%d] %s (%s, %s)\n%s" % (i + 1, s["title"], s.get("publisher", ""), s.get("published_at", ""), s["content"][:2500]) for i, s in enumerate(sources))
    system = ("You are a meticulous research editor for documentary films. Only mark a claim 'confirmed' when a numbered source states it. "
              "Claims from general knowledge without a source must be 'unverified'. Note conflicts between sources. Never invent sources.")
    prompt = "Research question: %s\n\nSources:\n%s\n\nWrite a structured report with up to 14 findings that a scriptwriter can use, plus visual ideas." % (
        query, external(numbered or "(no sources could be retrieved)", "search results"))
    out = llm.structured(system, prompt, ResearchOut, max_tokens=3500)
    rep = m.ResearchReport(project_id=project_id, kind=kind, query=query, summary=out.summary,
                           findings=[f.model_dump() for f in out.findings], data={"conflicts": out.conflicts, "avoid": out.inaccuracies_to_avoid, "errors": errors,
                                                                               "source_count": len(sources)})
    db.add(rep)
    db.flush()
    ids = []
    for s in sources:
        rs = m.ResearchSource(report_id=rep.id, url=s["url"], title=s.get("title", ""), publisher=s.get("publisher", ""), published_at=s.get("published_at") or None,
                              excerpt=s["content"][:2000])
        db.add(rs)
        db.flush()
        ids.append(str(rs.id))
        ingest(db, s["content"], s.get("title", s["url"]), "web", project_id, "unverified", s["url"], {"report_id": str(rep.id)})
    # findings point at stored source rows; drop indexes that do not exist (a model cannot invent a citation)
    fixed = []
    for f in rep.findings:
        good = [ids[i - 1] for i in f.get("source_indexes", []) if 0 < i <= len(ids)]
        status = f["status"] if good or f["status"] in ("unverified", "speculative") else "unverified"
        fixed.append(dict(f, source_ids=good, status=status))
    rep.findings = fixed
    text = out.summary + "\n" + "\n".join("- (%s) %s" % (f["status"], f["claim"]) for f in fixed)
    ingest(db, text, "Research: " + query, "research", project_id, "inferred", None, {"report_id": str(rep.id)})
    db.flush()
    return rep


def run(ctx):
    a = ctx.state.get("analysis", {})
    if not a.get("needs_research", True):
        return {"skipped": True, "summary": "Research not needed for this request"}
    q = ctx.project.title + (". " + ctx.project.brief[:400] if ctx.project.brief and ctx.project.brief != ctx.project.title else "")
    ctx.progress(0.1, "Searching sources")
    rep = research(ctx.db, q, ctx.project.id)
    n_conf = sum(1 for f in rep.findings if f["status"] == "confirmed")
    msg = "Research: %d findings (%d confirmed by sources), %d sources" % (len(rep.findings), n_conf, rep.data.get("source_count", 0))
    if rep.data.get("errors"):
        ctx.log("Some sources were unreachable: " + "; ".join(rep.data["errors"])[:400], "warn")
    if not rep.data.get("source_count"):
        ctx.log("No web sources were reachable; findings are marked unverified. Configure a web search provider for cited research.", "warn")
    return {"summary": msg, "state": {"research_report_id": str(rep.id)}}
