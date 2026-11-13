"""Long-term memory in five categories. Confirmed entries are never silently overwritten: a change supersedes the old row."""
import re

from fda.database import models as m
from fda.knowledge.embeddings import embed_texts

CATEGORIES = ("preference", "channel", "project", "production", "performance")
SECRET = re.compile(r"(sk-[A-Za-z0-9_-]{16,}|AIza[0-9A-Za-z_-]{20,}|ghp_[A-Za-z0-9]{20,}|xox[abp]-|-----BEGIN|api[_-]?key\s*[:=]\s*\S{12,}|password\s*[:=])", re.I)


class MemoryError_(ValueError):
    pass


def remember(db, user_id, category, key, content, data=None, status="confirmed", source="owner", project_id=None):
    if category not in CATEGORIES:
        raise MemoryError_("unknown memory category")
    if SECRET.search(content or "") or SECRET.search(str(data or "")):
        raise MemoryError_("Refusing to store something that looks like a secret or credential in memory")
    cur = db.query(m.Memory).filter_by(user_id=user_id, category=category, key=key, project_id=project_id).filter(m.Memory.status != "superseded").first()
    if cur is not None:
        if cur.content == content and (cur.data or {}) == (data or {}):
            return cur
        if cur.status == "confirmed" and status == "inferred":
            return cur  # an inference never replaces something the owner confirmed
        cur.status = "superseded"
    vec = embed_texts(db, [key + ": " + content])[0]
    mem = m.Memory(user_id=user_id, category=category, key=key, content=content, data=data or {}, status=status, source=source, project_id=project_id,
                   supersedes_id=cur.id if cur else None, embedding=vec)
    db.add(mem)
    db.flush()
    return mem


def recall(db, user_id, query=None, category=None, project_id=None, k=12):
    q = db.query(m.Memory).filter(m.Memory.user_id == user_id, m.Memory.status != "superseded")
    if category:
        q = q.filter(m.Memory.category == category)
    if project_id is not None:
        q = q.filter((m.Memory.project_id == project_id) | (m.Memory.project_id.is_(None)))
    if query:
        vec = embed_texts(db, [query])[0]
        q = q.filter(m.Memory.embedding.isnot(None)).order_by(m.Memory.embedding.cosine_distance(vec))
    else:
        q = q.order_by(m.Memory.updated_at.desc())
    return q.limit(k).all()


def as_context(mems):
    return "\n".join("- [%s/%s] %s: %s" % (x.category, x.status, x.key, x.content) for x in mems)
