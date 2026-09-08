import re
from decimal import Decimal
from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Result
from sqlalchemy.orm import Session

from app.config import settings


FORBIDDEN_PATTERN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|CREATE|GRANT|REVOKE|"
    r"COPY|EXECUTE|CALL|DO\b|MERGE|ATTACH|DETACH|VACUUM|REINDEX|"
    r"CLUSTER|COMMENT|SECURITY|SET\s+ROLE|SET\s+SESSION|LOAD\s+DATA|"
    r"INTO\s+OUTFILE|INTO\s+DUMPFILE)\b",
    re.IGNORECASE,
)


class SqlValidationError(ValueError):
    pass


def normalize_sql_dialect(sql: str) -> str:
    """Best-effort Postgres → MySQL dialect fixes for LLM-generated SQL."""
    out = sql
    # Reserved table name quoting
    out = re.sub(r'"transaction"', "`transaction`", out, flags=re.IGNORECASE)
    # Case-insensitive match operator
    out = re.sub(r"\bILIKE\b", "LIKE", out, flags=re.IGNORECASE)
    # Common month truncation pattern
    out = re.sub(
        r"date_trunc\(\s*'month'\s*,\s*([a-zA-Z0-9_.'`]+)\s*\)(::date)?",
        r"DATE_FORMAT(\1, '%Y-%m-01')",
        out,
        flags=re.IGNORECASE,
    )
    # Strip Postgres type casts like ::numeric / ::int / ::date
    out = re.sub(r"::[a-zA-Z_][a-zA-Z0-9_]*", "", out)
    return out


def assert_read_only_sql(sql: str) -> str:
    cleaned = sql.strip().rstrip(";").strip()
    if not cleaned:
        raise SqlValidationError("SQL is empty")
    if ";" in cleaned:
        raise SqlValidationError("Only a single SQL statement is allowed")
    if FORBIDDEN_PATTERN.search(cleaned):
        raise SqlValidationError("Only read-only SELECT/WITH queries are allowed")
    upper = cleaned.lstrip().upper()
    if not (upper.startswith("SELECT") or upper.startswith("WITH")):
        raise SqlValidationError("Query must start with SELECT or WITH")
    return normalize_sql_dialect(cleaned)


def _serialize_cell(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except Exception:
            return str(value)
    return value


def execute_readonly_sql(
    db: Session,
    sql: str,
    *,
    row_limit: int | None = None,
) -> tuple[list[str], list[list[Any]], str]:
    safe_sql = assert_read_only_sql(sql)
    limit = row_limit if row_limit is not None else settings.sql_row_limit

    # Enforce a soft row cap when the caller did not include LIMIT
    wrapped = safe_sql
    if not re.search(r"\bLIMIT\b", safe_sql, re.IGNORECASE):
        wrapped = f"{safe_sql}\nLIMIT {int(limit)}"

    # MySQL max execution time in milliseconds (0 = unlimited)
    timeout_ms = max(1, int(settings.sql_timeout_ms))
    try:
        db.execute(text(f"SET SESSION MAX_EXECUTION_TIME = {timeout_ms}"))
    except Exception:
        # Some managed MySQL hosts disallow session vars — continue without timeout.
        pass

    result: Result = db.execute(text(wrapped))
    columns = list(result.keys())
    rows = [[_serialize_cell(cell) for cell in row] for row in result.fetchall()]
    return columns, rows, wrapped
