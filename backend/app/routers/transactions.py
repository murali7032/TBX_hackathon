from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Transaction, TransactionType
from app.schemas import TransactionOut

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("", response_model=list[TransactionOut])
def list_transactions(
    account_id: str | None = Query(default=None, description="Filter by account id"),
    transaction_type: TransactionType | None = Query(
        default=None, description="Filter by credit/debit"
    ),
    limit: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[Transaction]:
    stmt = select(Transaction)
    if account_id:
        stmt = stmt.where(Transaction.account_id == account_id)
    if transaction_type:
        stmt = stmt.where(Transaction.transaction_type == transaction_type)
    stmt = stmt.order_by(Transaction.transaction_date.desc()).limit(limit)
    return list(db.scalars(stmt).all())


@router.get("/{transaction_id}", response_model=TransactionOut)
def get_transaction(transaction_id: str, db: Session = Depends(get_db)) -> Transaction:
    txn = db.get(Transaction, transaction_id)
    if txn is None:
        raise HTTPException(status_code=404, detail=f"Transaction '{transaction_id}' not found")
    return txn
