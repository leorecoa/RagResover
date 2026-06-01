import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import settings
from app.services.storage import storage_service

logger = logging.getLogger("rag_resover")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Iniciando RagResover em modo: %s", settings.APP_ENV)
    logger.info("Modelo LLM configurado: %s", settings.LLM_MODEL)

    logger.info("Verificando conexao com Storage (MinIO)...")
    try:
        await storage_service.ensure_bucket_exists()
    except Exception:
        if settings.storage_required:
            logger.exception("Falha ao conectar no Storage durante a inicializacao")
            raise
        logger.warning(
            "Storage indisponivel na inicializacao; uploads falharao ate o MinIO subir."
        )

    yield

    logger.info("Encerrando RagResover...")
