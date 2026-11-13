"""Helpers shared by agents."""
import re

from fda import catalog
from fda.database import models as m


def style(db, project):
    ps = db.query(m.ProjectSettings).filter_by(project_id=project.id).one()
    st = catalog.default_style(project.mode, project.language)
    st.update(ps.style or {})
    return ps, st


def latest_script(db, project_id):
    s = db.query(m.Script).filter_by(project_id=project_id).order_by(m.Script.created_at.desc()).first()
    if not s:
        return None, None
    v = db.query(m.ScriptVersion).filter_by(script_id=s.id, version=s.current_version).one_or_none()
    return s, v


def voiceover(db, project_id):
    return db.query(m.Voiceover).filter_by(project_id=project_id).order_by(m.Voiceover.created_at.desc()).first()


def transcript(db, project_id):
    vo = voiceover(db, project_id)
    if not vo:
        return None, None
    return vo, db.query(m.Transcript).filter_by(voiceover_id=vo.id).order_by(m.Transcript.created_at.desc()).first()


def storyboard(db, project_id):
    return db.query(m.Storyboard).filter_by(project_id=project_id).order_by(m.Storyboard.version.desc()).first()


def scenes(db, project_id):
    sb = storyboard(db, project_id)
    if not sb:
        return []
    return db.query(m.Scene).filter_by(storyboard_id=sb.id).order_by(m.Scene.idx).all()


def uploads(db, project_id, kind=None):
    q = db.query(m.Asset).filter_by(project_id=project_id, role="upload_original")
    if kind:
        q = q.filter(m.Asset.kind == kind)
    return q.order_by(m.Asset.created_at).all()


def words(text):
    return re.findall(r"\S+", text or "")


def sentences(text):
    text = re.sub(r"\s+", " ", text or "").strip()
    if not text:
        return []
    parts = re.split(r"(?<=[.!?।])\s+(?=\S)", text)
    out = []
    for p in parts:
        if out and len(p) < 12:
            out[-1] += " " + p
        elif p.strip():
            out.append(p.strip())
    return out


STOP = set("the a an and or but so because of to in on at for with from by as is are was were be been it its this that these those you your he she they them "
           "his her their we our i my me not no do does did have has had will would can could should than then there here what when where why how who which "
           "into over under about after before again just very more most much many some any each every all also only even still".split())


def keywords(s, n=4):
    ws = [w.strip(".,!?\"'()[]:;").lower() for w in (s or "").split()]
    ws = [w for w in ws if len(w) > 3 and w not in STOP and w.isascii()]
    seen, out = set(), []
    for w in sorted(ws, key=lambda w: -len(w)):
        if w not in seen:
            seen.add(w)
            out.append(w)
    return out[:n]


def clean_narration(t):
    t = re.sub(r"```.*?```", " ", t or "", flags=re.S)
    t = re.sub(r"^\s*(#+.*|\*\*[^*]{0,60}\*\*\s*$|(chapter|scene|part)\s+\d+[:.].{0,60}$|narrator:|voiceover:)", " ", t, flags=re.I | re.M)
    t = re.sub(r"\[[^\]]{0,80}\]|\([^)]{0,80}\)", " ", t)
    for a, b in (("‑", "-"), ("‐", "-"), ("’", "'"), ("‘", "'"), ("“", '"'), ("”", '"'), ("—", ", "), ("–", ", "), (";", ","), ("*", ""), ("#", "")):
        t = t.replace(a, b)
    return re.sub(r"\s+", " ", t).strip().strip('"')
