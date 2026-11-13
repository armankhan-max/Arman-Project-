"""Register files as assets with provenance and licence records."""
import mimetypes
import os

from fda.database import models as m
from fda.services import media
from fda.storage.store import make_key, sha256_file, store

KIND_BY_EXT = {".mp4": "video", ".mov": "video", ".webm": "video", ".mkv": "video", ".m4v": "video",
               ".jpg": "image", ".jpeg": "image", ".png": "image", ".webp": "image",
               ".mp3": "audio", ".wav": "audio", ".m4a": "audio", ".aac": "audio", ".ogg": "audio", ".flac": "audio", ".opus": "audio",
               ".blend": "blend", ".srt": "caption", ".vtt": "caption", ".txt": "document", ".md": "document", ".pdf": "document", ".docx": "document"}


def kind_of(filename):
    return KIND_BY_EXT.get(os.path.splitext(filename.lower())[1])


def register(db, path, project_id, role, folder, filename=None, origin="upload", provider="", source_url=None, prompt=None, settings=None,
             license=None, attribution="", commercial_use="unknown", terms_url=None, parent_id=None, move=False, meta=None, kind=None) -> m.Asset:
    filename = filename or os.path.basename(path)
    kind = kind or kind_of(filename) or "document"
    info = {}
    if kind in ("video", "audio", "image"):
        try:
            info = media.probe(path)
        except media.MediaError:
            if kind != "image":
                raise
    sha = sha256_file(path)
    size = os.path.getsize(path)
    key = make_key(project_id, folder, filename)
    store().put_file(path, key, move=move)
    v = (info.get("video") or {})
    a = m.Asset(project_id=project_id, kind=kind, role=role, storage_key=key, filename=filename, content_type=mimetypes.guess_type(filename)[0] or "",
                size_bytes=size, sha256=sha, width=v.get("width"), height=v.get("height"),
                duration_s=(info.get("duration") or None) if kind in ("video", "audio") else None, meta=dict(meta or {}, probe=info) if info else (meta or {}), parent_id=parent_id)
    db.add(a)
    db.flush()
    db.add(m.AssetSource(asset_id=a.id, origin=origin, provider=provider, source_url=source_url, prompt=prompt, settings=settings or {}))
    if license:
        db.add(m.AssetLicense(asset_id=a.id, license=license, attribution=attribution, commercial_use=commercial_use, terms_url=terms_url))
    return a


def local(asset: m.Asset) -> str:
    return store().local_path(asset.storage_key)
