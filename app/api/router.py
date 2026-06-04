from fastapi import APIRouter

from app.api.routes import chat, documents, health, ingestion, metrics, search


api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(ingestion.router)
api_router.include_router(documents.router)
api_router.include_router(search.router)
api_router.include_router(chat.router)
api_router.add_api_route("/metrics", metrics.metrics, methods=["GET"], tags=["Observability"])
