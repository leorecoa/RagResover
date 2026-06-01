# Changelog

All notable changes to RagResover should be documented in this file.

## Unreleased

- Modular FastAPI backend with health, readiness, upload, search, and chat endpoints.
- PostgreSQL/pgvector persistence for source documents and chunks.
- MinIO-compatible object storage for uploaded files.
- OpenAI and Ollama provider support for chat and embeddings.
- Static frontend for upload, semantic search, and RAG chat demos.
- Docker Compose stack for local development.
- Repository documentation, security policy, CI, and local check script.
- Initial Alembic migration environment for versioned database schema management.
- PDF and DOCX parsing with useful source metadata for RAG chunks.
- Retrieval score thresholds, metadata filters, debug diagnostics, and a reranker interface.
