from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Account
from app.schemas import AccountOut

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.get("", response_model=list[AccountOut])
def list_accounts(
    bank_code: str | None = Query(default=None, description="Filter by bank code"),
    entity_id: str | None = Query(default=None, description="Filter by entity id"),
    db: Session = Depends(get_db),
) -> list[Account]:
    stmt = select(Account)
    if bank_code:
        stmt = stmt.where(Account.bank_code == bank_code.upper())
    if entity_id:
        stmt = stmt.where(Account.entity_id == entity_id)
    stmt = stmt.order_by(Account.account_number)
    return list(db.scalars(stmt).all())


@router.get("/{account_id}", response_model=AccountOut)
def get_account(account_id: str, db: Session = Depends(get_db)) -> Account:
    account = db.get(Account, account_id)
    if account is None:
        raise HTTPException(status_code=404, detail=f"Account '{account_id}' not found")
    return account
