from pathlib import Path

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings


def _resolve_guide_path() -> Path:
    path = Path(settings.database_guide_path)
    if not path.is_absolute():
        backend_root = Path(__file__).resolve().parent.parent.parent
        path = (backend_root / path).resolve()
    return path


def load_database_guide(*, max_chars: int | None = None) -> str:
    path = _resolve_guide_path()
    if not path.exists():
        return (
            "Guide file not found. Schema: bank(bank_code, bank_name); "
            "account(account_id, entity_id, account_number, program_id, available_balance, bank_code); "
            "transaction(transaction_id, account_id, transaction_date, transaction_type, description, "
            "transaction_amount, transaction_reference_id, utr_number). "
            "Always backtick `transaction` in MySQL."
        )
    text_body = path.read_text(encoding="utf-8")
    limit = max_chars if max_chars is not None else settings.guide_max_chars
    if len(text_body) > limit:
        return text_body[:limit] + "\n\n…[truncated for model context]…"
    return text_body


def list_schema_summary(db: Session) -> str:
    rows = db.execute(
        text(
            """
            SELECT table_name, column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = DATABASE()
              AND table_name IN ('bank', 'account', 'transaction')
            ORDER BY table_name, ordinal_position
            """
        )
    ).fetchall()
    if not rows:
        return "No tables found for bank/account/transaction in the current database."
    lines = ["table | column | type | nullable"]
    for table_name, column_name, data_type, is_nullable in rows:
        lines.append(f"{table_name} | {column_name} | {data_type} | {is_nullable}")
    return "\n".join(lines)
