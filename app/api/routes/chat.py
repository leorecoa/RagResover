import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.chat import ChatRequest, ChatResponse
from app.db.session import get_db_session
from app.repositories.documents import DocumentRepository, SearchResult
from app.services.chat import chat_service
from app.services.embeddings import embedding_service

logger = logging.getLogger("rag_resover")
router = APIRouter(tags=["Chat"])


def build_source_payload(results: list[SearchResult]) -> list[dict]:
    return [
        {
            "index": index,
            "chunk_id": str(item.chunk_id),
            "document_id": str(item.document_id),
            "file_name": item.file_name,
            "score": item.score,
            "excerpt": item.content[:600],
            "metadata": item.metadata,
        }
        for index, item in enumerate(results, start=1)
    ]


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    session: AsyncSession = Depends(get_db_session),
):
    try:
        query_embedding = await embedding_service.embed_query(request.question)
        results = await DocumentRepository(session).search_similar_chunks(
            embedding=query_embedding,
            limit=request.top_k,
        )

        if not results:
            return {
                "question": request.question,
                "answer": "Nao encontrei contexto suficiente nos documentos indexados.",
                "sources": [],
            }

        chat_answer = await chat_service.answer_question(
            question=request.question,
            results=results,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception:
        logger.exception("Erro ao executar chat RAG")
        raise HTTPException(status_code=500, detail="Erro interno ao executar chat.") from None

    return {
        "question": request.question,
        "answer": chat_answer.answer,
        "sources": build_source_payload(results),
    }
