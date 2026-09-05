from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_BACKEND_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = (
        "postgresql+psycopg2://finance_user:finance_password@127.0.0.1:5432/finance"
    )
    app_name: str = "TBX Finance Assistant API"
    cors_origins: list[str] = ["*"]

    # Google Gemini (primary LLM for /chat)
    gemini_api_key: str = ""
    gemini_model: str = ""
    gemini_optimize_for: Literal["cost", "balanced", "intelligence"] = "balanced"

    # Optional legacy Cursor settings (ignored by chat agent)
    cursor_api_key: str = ""
    cursor_optimize_for: Literal["cost", "balanced", "intelligence"] = "balanced"
    cursor_model: str = ""
    cursor_use_router: bool = False
    cursor_workspace: str = str(_BACKEND_ROOT)

    database_guide_path: str = str(
        _BACKEND_ROOT.parent / "database" / "LLM_TOOL_GUIDE.md"
    )

    max_tool_rounds: int = 5
    sql_row_limit: int = 200
    sql_timeout_ms: int = 5000
    guide_max_chars: int = 12000


settings = Settings()
