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
        "mysql+pymysql://tiby:tiby@3.91.96.208:3306/tiby_hackathon"
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
    # MySQL MAX_EXECUTION_TIME for read-only queries (ms). Large ledgers need headroom.
    sql_timeout_ms: int = 180000
    # Gemini HTTP client timeout (ms) — covers multi-round tool + generation loops.
    gemini_http_timeout_ms: int = 300000
    # MySQL TCP connect timeout (seconds)
    db_connect_timeout_sec: int = 30
    guide_max_chars: int = 12000


settings = Settings()
