import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
    # Attempt to load from both repo root and server/.env
    _this = Path(__file__).resolve()
    _server_dir = _this.parent.parent
    _repo_root = _server_dir.parent
    # Load root .env first (preferred), then server/.env as optional override
    load_dotenv(_repo_root / ".env")
    load_dotenv(_server_dir / ".env")
except ImportError:
    # python-dotenv not installed; rely on actual environment
    pass


def _get(name: str, default: str | None = None, required: bool = False) -> str | None:
    val = os.getenv(name, default)
    if required and not val:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return val


@dataclass
class Settings:
    gemini_api_key: str | None = _get("GEMINI_API_KEY", None, required=False)
    groq_api_key: str | None = _get("GROQ_API_KEY", None, required=False)
    openai_api_key: str | None = _get("OPENAI_API_KEY", None, required=False)
    datagovin_api_key: str | None = _get("DATA_GOV_IN_API_KEY")
    openweather_api_key: str | None = _get("OPENWEATHER_API_KEY")
    perplexity_api_key: str | None = _get("PERPLEXITY_API_KEY")
    redis_url: str | None = _get("REDIS_URL", "redis://localhost:6379/0")
    pg_dsn: str | None = _get("PG_DSN")
    allow_origins: list[str] = tuple((os.getenv("CORS_ALLOW_ORIGINS", "http://localhost:5173").split(",")))  # Vite default


settings = Settings()
