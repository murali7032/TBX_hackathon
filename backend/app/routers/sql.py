from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import SqlRequest, SqlResponse
from app.services.sql_guard import SqlValidationError, execute_readonly_sql

router = APIRouter(prefix="/api", tags=["sql"])


@router.post("/sql", response_model=SqlResponse)
def run_sql(body: SqlRequest, db: Session = Depends(get_db)) -> SqlResponse:
    try:
        columns, rows, executed = execute_readonly_sql(db, body.sql)
    except SqlValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"Query failed: {exc}") from exc
    return SqlResponse(columns=columns, rows=rows, row_count=len(rows), sql=executed)
