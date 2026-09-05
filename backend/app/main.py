from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import api_router
from app.routers.chat import router as chat_router
from app.routers.export import router as export_router
from app.routers.health import router as health_router
from app.routers.sql import router as sql_router

app = FastAPI(title=settings.app_name, version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(api_router, prefix="/api")
app.include_router(sql_router)
app.include_router(chat_router)
app.include_router(export_router)
