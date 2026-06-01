from fastapi import APIRouter

from app.api.routes import chat, health, ingestion, search


api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(ingestion.router)
api_router.include_router(search.router)
api_router.include_router(chat.router)
