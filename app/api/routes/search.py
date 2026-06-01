import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.search import SearchRequest, SearchResponse
from app.core.config import settings
from app.db.session import get_db_session
from app.repositories.documents import DocumentRepository
from app.services.retrieval import retrieval_service

logger = logging.getLogger("rag_resover")
router = APIRouter(tags=["Retrieval"])


@router.post("/search", response_model=SearchResponse, response_model_exclude_none=True)
async def search_documents(
    request: SearchRequest,
    session: AsyncSession = Depends(get_db_session),
):
    try:
        retrieval = await retrieval_service.retrieve(
            repository=DocumentRepository(session),
            query=request.query,
            top_k=request.top_k,
            score_threshold=request.score_threshold,
            metadata_filters=request.metadata_filters,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception:
        logger.exception("Erro ao executar busca semantica")
        raise HTTPException(status_code=500, detail="Erro interno ao executar busca.") from None

    return {
        "query": request.query,
        "results": [
            {
                "chunk_id": str(item.chunk_id),
                "document_id": str(item.document_id),
                "file_name": item.file_name,
                "content": item.content,
                "score": item.score,
                "metadata": item.metadata,
            }
            for item in retrieval.results
        ],
        "diagnostics": retrieval.diagnostics.as_dict() if settings.DEBUG else None,
    }
