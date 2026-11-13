"""Document ingestion: extract → normalise → de-duplicate → chunk → embed → store, with source and trust level."""
import hashlib
import os
import re
from datetime import datetime, timezone

from fda.database import models as m

from .embeddings import embed_texts, embedding_model

TRUST = ("verified", "user_provided", "inferred", "unverified", "outdated")


def extract_text(path):
    ext = os.path.splitext(path.lower())[1]
    if ext == ".pdf":
        from pypdf import PdfReader
        return "\n\n".join((p.extract_text() or "") for p in PdfReader(path).pages)
    if ext == ".docx":
        import docx
        return "\n\n".join(p.text for p in docx.Document(path).paragraphs)
    if ext in (".txt", ".md", ".srt", ".vtt", ".csv", ".json"):
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    raise ValueError("Unsupported document type %s" % ext)


def chunk(text, size=900, overlap=150):
    text = re.sub(r"[ \t]+", " ", text or "").strip()
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    out, cur = [], ""
    for p in paras:
        while len(p) > size:
            cut = p.rfind(". ", 0, size)
            cut = cut + 1 if cut > size * 0.5 else size
            if cur:
                out.append(cur)
                cur = ""
            out.append(p[:cut].strip())
            p = p[max(0, cut - overlap):].strip()
        if len(cur) + len(p) + 2 > size and cur:
            out.append(cur)
            cur = cur[-overlap:] + "\n" + p if overlap else p
        else:
            cur = (cur + "\n\n" + p).strip()
    if cur:
        out.append(cur)
    return [c for c in out if len(c) > 20]


def ingest(db, text, title, source_type, project_id=None, trust="unverified", source_url=None, meta=None, expires_at=None):
    if trust not in TRUST:
        raise ValueError("bad trust level")
    h = hashlib.sha256(re.sub(r"\s+", " ", text or "").strip().lower().encode()).hexdigest()
    dup = db.query(m.KnowledgeDocument).filter_by(content_hash=h, project_id=project_id).first()
    if dup:
        return dup, False
    doc = m.KnowledgeDocument(project_id=project_id, title=title[:500], source_type=source_type, trust=trust, source_url=source_url,
                              content_hash=h, retrieved_at=datetime.now(timezone.utc), meta=meta or {}, expires_at=expires_at)
    db.add(doc)
    db.flush()
    parts = chunk(text)
    vecs = embed_texts(db, parts) if parts else []
    model = embedding_model(db)
    for i, (t, v) in enumerate(zip(parts, vecs)):
        c = m.KnowledgeChunk(document_id=doc.id, idx=i, text=t, tokens=len(t) // 4)
        db.add(c)
        db.flush()
        db.add(m.Embedding(chunk_id=c.id, model=model, vector=v))
    db.flush()
    return doc, True


def reindex(db, document_id=None):
    q = db.query(m.KnowledgeChunk)
    if document_id:
        q = q.filter_by(document_id=document_id)
    chunks = q.all()
    model = embedding_model(db)
    for i in range(0, len(chunks), 64):
        batch = chunks[i:i + 64]
        vecs = embed_texts(db, [c.text for c in batch])
        for c, v in zip(batch, vecs):
            e = db.query(m.Embedding).filter_by(chunk_id=c.id, model=model).one_or_none()
            if e:
                e.vector = v
            else:
                db.add(m.Embedding(chunk_id=c.id, model=model, vector=v))
    db.flush()
    return len(chunks)
