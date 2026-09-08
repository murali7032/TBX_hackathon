from datetime import datetime
from decimal import Decimal
from enum import Enum as PyEnum

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TransactionType(str, PyEnum):
    credit = "credit"
    debit = "debit"


class Bank(Base):
    __tablename__ = "bank"

    bank_code: Mapped[str] = mapped_column(String(10), primary_key=True)
    bank_name: Mapped[str] = mapped_column(String(150), nullable=False)

    accounts: Mapped[list["Account"]] = relationship(back_populates="bank")


class Account(Base):
    __tablename__ = "account"

    account_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    entity_id: Mapped[str] = mapped_column(String(36), nullable=False)
    account_number: Mapped[str] = mapped_column(String(20), nullable=False)
    program_id: Mapped[int] = mapped_column(Integer, nullable=False)
    available_balance: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False, default=Decimal("0.00")
    )
    bank_code: Mapped[str] = mapped_column(
        String(10), ForeignKey("bank.bank_code"), nullable=False
    )

    bank: Mapped["Bank"] = relationship(back_populates="accounts")
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="account")


class Transaction(Base):
    __tablename__ = "transaction"

    transaction_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    account_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("account.account_id"), nullable=False
    )
    transaction_date: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)
    transaction_type: Mapped[TransactionType] = mapped_column(
        Enum(
            TransactionType,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
            native_enum=True,
        ),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(String(500))
    transaction_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False, default=Decimal("0.00")
    )
    transaction_reference_id: Mapped[str | None] = mapped_column(String(64))
    utr_number: Mapped[str | None] = mapped_column(String(256))

    account: Mapped["Account"] = relationship(back_populates="transactions")
