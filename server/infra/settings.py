import os
from dataclasses import dataclass


def _get(name: str, default: str | None = None, required: bool = False) -> str | None:
    val = os.getenv(name, default)
    if required and not val:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return val


@dataclass
class Settings:
    gemini_api_key: str | None = _get("GEMINI_API_KEY", None, required=False)
    datagovin_api_key: str | None = _get("DATA_GOV_IN_API_KEY")
    redis_url: str | None = _get("REDIS_URL", "redis://localhost:6379/0")
    pg_dsn: str | None = _get("PG_DSN")
    allow_origins: list[str] = tuple((os.getenv("CORS_ALLOW_ORIGINS", "http://localhost:5173").split(",")))  # Vite default


settings = Settings()
