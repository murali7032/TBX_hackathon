from fastapi import APIRouter, Depends
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Account, Bank
from app.schemas import HealthOut

router = APIRouter(tags=["health"])


def _table_row_estimate(db: Session, table_name: str) -> int:
    """InnoDB approximate row count — avoids full COUNT(*) on huge tables."""
    value = db.execute(
        text(
            """
            SELECT TABLE_ROWS
            FROM information_schema.tables
            WHERE table_schema = DATABASE()
              AND table_name = :table_name
            """
        ),
        {"table_name": table_name},
    ).scalar()
    return int(value or 0)


@router.get("/health", response_model=HealthOut)
def health(db: Session = Depends(get_db)) -> HealthOut:
    db.execute(text("SELECT 1"))
    banks = db.scalar(select(func.count()).select_from(Bank)) or 0
    accounts = db.scalar(select(func.count()).select_from(Account)) or 0
    # Exact COUNT on 10M+ rows is too slow for a health check
    transactions = _table_row_estimate(db, "transaction")
    return HealthOut(
        status="ok",
        database="connected",
        banks=banks,
        accounts=accounts,
        transactions=transactions,
    )
