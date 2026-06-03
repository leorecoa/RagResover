from fastapi import APIRouter

from app.api.routes import chat, documents, health, ingestion, search


api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(ingestion.router)
api_router.include_router(documents.router)
api_router.include_router(search.router)
api_router.include_router(chat.router)
