from fastapi import APIRouter

from app.api.routes import auth, chat, documents, health, ingestion, metrics, organizations, search


api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(organizations.router)
api_router.include_router(ingestion.router)
api_router.include_router(documents.router)
api_router.include_router(search.router)
api_router.include_router(chat.router)
api_router.add_api_route("/metrics", metrics.metrics, methods=["GET"], tags=["Observability"])
