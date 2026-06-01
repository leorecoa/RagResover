import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.search import SearchRequest, SearchResponse
from app.db.session import get_db_session
from app.repositories.documents import DocumentRepository
from app.services.embeddings import embedding_service

logger = logging.getLogger("rag_resover")
router = APIRouter(tags=["Retrieval"])


@router.post("/search", response_model=SearchResponse)
async def search_documents(
    request: SearchRequest,
    session: AsyncSession = Depends(get_db_session),
):
    try:
        query_embedding = await embedding_service.embed_query(request.query)
        results = await DocumentRepository(session).search_similar_chunks(
            embedding=query_embedding,
            limit=request.top_k,
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
            for item in results
        ],
    }
