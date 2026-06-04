from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.core.constants import APP_VERSION
from app.core.lifespan import lifespan
from app.core.logging import configure_logging
from app.core.middleware import request_observability_middleware


def create_app() -> FastAPI:
    configure_logging()

    app = FastAPI(
        title="RagResover API",
        description="Backend modular para upload, busca semantica e chat RAG com fontes.",
        version=APP_VERSION,
        lifespan=lifespan,
        debug=settings.DEBUG,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.middleware("http")(request_observability_middleware)
    app.include_router(api_router)

    return app
