from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Bank
from app.schemas import BankOut

router = APIRouter(prefix="/banks", tags=["banks"])


@router.get("", response_model=list[BankOut])
def list_banks(db: Session = Depends(get_db)) -> list[Bank]:
    return list(db.scalars(select(Bank).order_by(Bank.bank_code)).all())


@router.get("/{bank_code}", response_model=BankOut)
def get_bank(bank_code: str, db: Session = Depends(get_db)) -> Bank:
    bank = db.get(Bank, bank_code.upper())
    if bank is None:
        raise HTTPException(status_code=404, detail=f"Bank '{bank_code}' not found")
    return bank
