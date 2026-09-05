import re
from decimal import Decimal
from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Result
from sqlalchemy.orm import Session

from app.config import settings


FORBIDDEN_PATTERN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|CREATE|GRANT|REVOKE|"
    r"COPY|EXECUTE|CALL|DO|MERGE|REPLACE|ATTACH|DETACH|VACUUM|REINDEX|"
    r"CLUSTER|COMMENT|SECURITY|SET\s+ROLE|SET\s+SESSION)\b",
    re.IGNORECASE,
)


class SqlValidationError(ValueError):
    pass


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
    return cleaned


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

    db.execute(text(f"SET LOCAL statement_timeout = '{int(settings.sql_timeout_ms)}'"))
    result: Result = db.execute(text(wrapped))
    columns = list(result.keys())
    rows = [[_serialize_cell(cell) for cell in row] for row in result.fetchall()]
    return columns, rows, wrapped
