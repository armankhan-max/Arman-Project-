"""Runtime configuration. Everything comes from environment variables (see .env.example)."""
import os
from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_DIR = os.path.dirname(BACKEND_DIR)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="FDA_", env_file=os.path.join(REPO_DIR, ".env"), extra="ignore")

    env: str = "development"
    database_url: str = "postgresql+psycopg://postgres@/fda?host=/tmp"
    redis_url: str = "redis://localhost:6379/0"
    # Celery: when false (or Redis is down) jobs run in a local thread pool inside the API process.
    use_celery: bool = True

    @field_validator("database_url")
    @classmethod
    def _driver(cls, v):  # managed hosts hand out plain postgres:// URLs
        for pre in ("postgres://", "postgresql://"):
            if v.startswith(pre):
                return "postgresql+psycopg://" + v[len(pre):]
        return v

    # single-owner auth
    owner_email: str = "owner@localhost"
    owner_password: str = ""            # plain password on first boot; stored hashed in the DB
    secret_key: str = "dev-only-change-me-dev-only-change-me"  # signs sessions, derives the credential-encryption key
    session_hours: int = 72
    cors_origins: str = "http://localhost:3000"

    # storage
    storage_backend: str = "local"       # local | db (files in PostgreSQL, survive restarts) | s3
    storage_dir: str = os.path.join(REPO_DIR, "storage")
    s3_bucket: str = ""
    s3_endpoint_url: str = ""
    s3_region: str = "auto"
    s3_access_key: str = ""
    s3_secret_key: str = ""
    max_upload_mb: int = 1024

    # tools
    ffmpeg_bin: str = "ffmpeg"
    ffprobe_bin: str = "ffprobe"
    blender_bin: str = "blender"
    whisper_model: str = "small"
    render_workers: int = max(1, (os.cpu_count() or 2))

    # Google OAuth for the owner's YouTube channel
    google_client_id: str = ""
    google_client_secret: str = ""
    public_base_url: str = "http://localhost:8000"

    # autonomy limits (owner can change in the UI; these are the defaults)
    max_retries: int = 2
    max_concurrent_jobs: int = 2


@lru_cache
def get_settings() -> Settings:
    return Settings()
