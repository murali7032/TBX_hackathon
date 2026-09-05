from fastapi import APIRouter

from app.routers import accounts, banks, transactions

api_router = APIRouter()
api_router.include_router(banks.router)
api_router.include_router(accounts.router)
api_router.include_router(transactions.router)
