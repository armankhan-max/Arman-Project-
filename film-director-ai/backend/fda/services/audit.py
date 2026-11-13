from fda.database import models as m


def audit(db, actor, action, target="", ip=None, **detail):
    db.add(m.AuditLog(actor=actor, action=action, target=str(target), detail=detail, ip=ip))
