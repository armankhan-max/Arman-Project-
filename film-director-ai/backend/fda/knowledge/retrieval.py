"""Semantic retrieval with metadata filters, freshness and citations."""
from datetime import datetime, timezone

from fda.database import models as m

from .embeddings import embed_texts, embedding_model


def search(db, query, k=8, project_id=None, include_global=True, source_types=None, min_trust=None):
    vec = embed_texts(db, [query])[0]
    model = embedding_model(db)
    dist = m.Embedding.vector.cosine_distance(vec)
    q = (db.query(m.KnowledgeChunk, m.KnowledgeDocument, dist.label("d")).join(m.Embedding, m.Embedding.chunk_id == m.KnowledgeChunk.id)
         .join(m.KnowledgeDocument, m.KnowledgeDocument.id == m.KnowledgeChunk.document_id).filter(m.Embedding.model == model))
    if project_id and include_global:
        q = q.filter((m.KnowledgeDocument.project_id == project_id) | (m.KnowledgeDocument.project_id.is_(None)))
    elif project_id:
        q = q.filter(m.KnowledgeDocument.project_id == project_id)
    if source_types:
        q = q.filter(m.KnowledgeDocument.source_type.in_(source_types))
    if min_trust == "verified":
        q = q.filter(m.KnowledgeDocument.trust.in_(["verified", "user_provided"]))
    now = datetime.now(timezone.utc)
    out = []
    for c, d, dd in q.order_by(dist).limit(k * 2).all():
        trust = "outdated" if d.expires_at and d.expires_at < now else d.trust
        score = 1 - float(dd) - (0.1 if trust in ("outdated", "unverified") else 0)
        out.append({"text": c.text, "score": round(score, 4), "document_id": str(d.id), "title": d.title, "source_type": d.source_type, "trust": trust,
                    "source_url": d.source_url, "retrieved_at": d.retrieved_at.isoformat() if d.retrieved_at else None})
    out.sort(key=lambda r: -r["score"])
    return out[:k]


def as_context(results, limit_chars=5000):
    parts, n = [], 0
    for i, r in enumerate(results):
        s = "[%d] (%s, %s%s) %s" % (i + 1, r["trust"], r["source_type"], (", " + r["source_url"]) if r.get("source_url") else "", r["text"])
        if n + len(s) > limit_chars:
            break
        parts.append(s)
        n += len(s)
    return "\n".join(parts)
