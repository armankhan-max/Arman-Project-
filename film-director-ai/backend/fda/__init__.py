import os as _os

# the procedural render engine keeps its caches under the storage directory
if "STUDIO_DATA" not in _os.environ:
    from fda.config import get_settings as _gs
    _os.environ["STUDIO_DATA"] = _os.path.join(_gs().storage_dir, ".engine")
