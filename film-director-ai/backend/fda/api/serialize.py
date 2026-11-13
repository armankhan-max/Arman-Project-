"""Plain dict views of ORM rows for JSON responses."""
from datetime import datetime
from uuid import UUID

from fda.database import models as m


def row(r, exclude=()):
    if r is None:
        return None
    out = {}
    for c in r.__table__.columns:
        if c.name in exclude:
            continue
        v = getattr(r, c.name)
        if isinstance(v, UUID):
            v = str(v)
        elif isinstance(v, datetime):
            v = v.isoformat()
        elif isinstance(v, (bytes, memoryview)):
            continue
        elif hasattr(v, "tolist"):
            continue
        elif c.name in ("limit_usd", "estimated_usd", "actual_usd") and v is not None:
            v = float(v)
        out[c.name] = v
    return out


def asset(db, a):
    if a is None:
        return None
    d = row(a, ("storage_key",))
    d["url"] = "/api/v1/assets/%s/file" % a.id
    src = db.query(m.AssetSource).filter_by(asset_id=a.id).first()
    lic = db.query(m.AssetLicense).filter_by(asset_id=a.id).first()
    d["source"] = row(src) if src else None
    d["license"] = row(lic) if lic else None
    return d
