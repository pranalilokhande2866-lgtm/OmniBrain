"""
Central app configuration.

Everything reads from environment variables (via a .env file in the
project root). Import `settings` anywhere you need a config value —
don't read os.environ directly elsewhere in the codebase.
"""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Anchored to this file's location, NOT the process's current working
# directory. run_dev.sh launches uvicorn from backend/ and Streamlit
# from frontend/ - if .env/data_dir were plain relative paths ("./.env",
# "./data"), they'd resolve differently (and wrongly) depending on which
# of those you happened to launch from. This file is always at
# <project_root>/backend/app/config.py, so walking up three parents
# always lands on <project_root> no matter where the process was started.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- OpenAI (optional if GOOGLE_API_KEY is set instead - see below) ---
    openai_api_key: str = ""
    openai_chat_model: str = "gpt-4o"
    openai_vision_model: str = "gpt-4o"

    # --- Google Gemini (free tier via https://aistudio.google.com/apikey -
    # no billing/credit card required. Used automatically instead of OpenAI
    # when set - see agents/llm.py) ---
    google_api_key: str = ""
    google_chat_model: str = "gemini-flash-latest"
    google_vision_model: str = "gemini-flash-latest"  # same model handles both; it's natively multimodal

    # --- Qdrant ---
    qdrant_url: str = ""
    qdrant_api_key: str = ""

    # --- Langfuse (all optional; tracing silently no-ops if unset) ---
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"

    # --- App behaviour ---
    self_rag_max_retries: int = 2
    data_dir: str = str(_PROJECT_ROOT / "data")

    @property
    def data_path(self) -> Path:
        p = Path(self.data_dir)
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def uploads_path(self) -> Path:
        p = self.data_path / "uploads"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def qdrant_storage_path(self) -> Path:
        """Used only when qdrant_url is empty (local/embedded mode)."""
        p = self.data_path / "qdrant_storage"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def sqlite_path(self) -> Path:
        return self.data_path / "stock_data.db"

    @property
    def has_openai_key(self) -> bool:
        return bool(self.openai_api_key.strip())

    @property
    def has_google_key(self) -> bool:
        return bool(self.google_api_key.strip())

    @property
    def llm_provider(self) -> str | None:
        if self.has_google_key:
            return "gemini"
        if self.has_openai_key:
            return "openai"
        return None

    @property
    def has_langfuse_keys(self) -> bool:
        return bool(self.langfuse_public_key.strip() and self.langfuse_secret_key.strip())


settings = Settings()
