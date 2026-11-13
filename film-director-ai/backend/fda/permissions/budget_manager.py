"""Spending control. Paid operations must pass reserve() first; nothing paid runs without a configured limit."""
from datetime import datetime, timedelta, timezone

from sqlalchemy import func

from fda.database import models as m


class BudgetError(RuntimeError):
    code = "budget"


def _spent(db, since=None, project_id=None, provider=None):
    q = db.query(func.coalesce(func.sum(func.coalesce(m.UsageRecord.actual_usd, m.UsageRecord.estimated_usd)), 0)).filter(m.UsageRecord.status != "released")
    if since:
        q = q.filter(m.UsageRecord.created_at >= since)
    if project_id:
        q = q.filter(m.UsageRecord.project_id == project_id)
    if provider:
        q = q.filter(m.UsageRecord.provider == provider)
    return float(q.scalar() or 0)


def limits(db):
    return {(b.scope, b.scope_ref): float(b.limit_usd) for b in db.query(m.Budget).filter_by(active=True).all() if b.scope != "override"}


def status(db, project_id=None):
    now = datetime.now(timezone.utc)
    day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month = day.replace(day=1)
    L = limits(db)
    out = {"daily": {"limit": L.get(("daily", "")), "spent": _spent(db, day)}, "monthly": {"limit": L.get(("monthly", "")), "spent": _spent(db, month)}}
    if project_id:
        out["project"] = {"limit": L.get(("project", str(project_id))), "spent": _spent(db, None, project_id)}
    out["providers"] = {ref: {"limit": v, "spent": _spent(db, month, None, ref)} for (sc, ref), v in L.items() if sc == "provider"}
    out["owner_override"] = owner_override(db)
    out["configured"] = out["owner_override"] or bool(L.get(("daily", "")) is not None or L.get(("monthly", "")) is not None)
    return out


def set_limit(db, scope, ref, usd):
    b = db.query(m.Budget).filter_by(scope=scope, scope_ref=ref or "").one_or_none()
    if usd is None:
        if b:
            db.delete(b)
        return None
    if b is None:
        b = m.Budget(scope=scope, scope_ref=ref or "", limit_usd=usd)
        db.add(b)
    b.limit_usd, b.active = usd, True
    return b


def owner_override(db):
    """Owner chose unlimited mode (confirmed with their password). Spending is still recorded, just not blocked."""
    b = db.query(m.Budget).filter_by(scope="override", scope_ref="owner", active=True).one_or_none()
    return b is not None


def set_override(db, on):
    b = db.query(m.Budget).filter_by(scope="override", scope_ref="owner").one_or_none()
    if on and b is None:
        db.add(m.Budget(scope="override", scope_ref="owner", limit_usd=0))
    elif b is not None:
        b.active = bool(on)


def reserve(db, provider, operation, units, unit, project_id=None):
    """Free providers are recorded at $0. Paid providers need (a) an owner cost estimate and (b) a daily or monthly limit,
    and the reservation must fit every applicable limit."""
    est = provider.estimate(units) if provider.paid else 0.0
    if provider.paid and owner_override(db):
        est = provider.estimate(units) or 0.0
    elif provider.paid:
        L = limits(db)
        if L.get(("daily", "")) is None and L.get(("monthly", "")) is None:
            raise BudgetError("Paid provider '%s' needs a spending limit. Set a daily or monthly budget in Settings → Budget." % provider.label)
        if est is None:
            raise BudgetError("No cost estimate for '%s'. Enter its USD price per %s in Settings → Providers so spending can be controlled." % (provider.label, provider.unit))
        st = status(db, project_id)
        checks = [("daily", st["daily"]), ("monthly", st["monthly"])]
        if project_id and st.get("project", {}).get("limit") is not None:
            checks.append(("project", st["project"]))
        pv = st["providers"].get(provider.name)
        if pv:
            checks.append(("provider " + provider.name, pv))
        for name, s in checks:
            if s["limit"] is not None and s["spent"] + est > s["limit"] + 1e-9:
                raise BudgetError("This %s operation (≈$%.2f) would exceed the %s limit ($%.2f spent of $%.2f)." % (provider.label, est, name, s["spent"], s["limit"]))
    rec = m.UsageRecord(project_id=project_id, provider=provider.name, operation=operation, units=units, unit=unit, estimated_usd=est, status="reserved")
    db.add(rec)
    db.flush()
    return rec


def commit(db, rec, actual_units=None, actual_usd=None):
    if rec is None:
        return
    rec.status = "committed"
    if actual_units is not None:
        rec.units = actual_units
    if actual_usd is not None:
        rec.actual_usd = actual_usd


def release(db, rec):
    if rec is not None:
        rec.status = "released"
