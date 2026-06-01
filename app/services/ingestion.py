import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from anyio import to_thread
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import settings
from app.services.storage import storage_service

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class IngestionResult:
    chunks: List[Document]
    storage_path: str
    file_size: int


class IngestionService:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            length_function=len,
            separators=["\n\n", "\n", " ", ""],
        )

    async def process_document(
        self,
        file_name: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Document]:
        logger.info("Iniciando chunking para %s", file_name)

        doc = Document(
            page_content=content,
            metadata=metadata or {"source": file_name},
        )

        chunks = await to_thread.run_sync(self.text_splitter.split_documents, [doc])

        logger.info("Documento %s dividido em %s chunks", file_name, len(chunks))

        return chunks

    async def ingest_raw_file(
        self,
        file_name: str,
        file_bytes: bytes,
        content_type: str,
    ) -> IngestionResult:
        try:
            storage_path = await storage_service.upload_file(
                file_name,
                file_bytes,
                content_type,
            )
            text_content = file_bytes.decode("utf-8", errors="replace")

            chunks = await self.process_document(
                file_name,
                text_content,
                {
                    "source": file_name,
                    "path": storage_path,
                    "content_type": content_type,
                    "size_bytes": len(file_bytes),
                },
            )
            return IngestionResult(
                chunks=chunks,
                storage_path=storage_path,
                file_size=len(file_bytes),
            )
        except Exception:
            logger.exception("Erro na pipeline de ingestao para %s", file_name)
            raise


ingestion_service = IngestionService()
