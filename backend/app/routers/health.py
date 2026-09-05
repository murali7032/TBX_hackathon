from fastapi import APIRouter, Depends
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Account, Bank, Transaction
from app.schemas import HealthOut

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthOut)
def health(db: Session = Depends(get_db)) -> HealthOut:
    db.execute(text("SELECT 1"))
    banks = db.scalar(select(func.count()).select_from(Bank)) or 0
    accounts = db.scalar(select(func.count()).select_from(Account)) or 0
    transactions = db.scalar(select(func.count()).select_from(Transaction)) or 0
    return HealthOut(
        status="ok",
        database="connected",
        banks=banks,
        accounts=accounts,
        transactions=transactions,
    )
