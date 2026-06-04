# Changelog

All notable changes to RagResover should be documented in this file.

## Unreleased

- Modular FastAPI backend with health, readiness, upload, search, and chat endpoints.
- PostgreSQL/pgvector persistence for source documents and chunks.
- MinIO-compatible object storage for uploaded files.
- OpenAI and Ollama provider support for chat and embeddings.
- React frontend for login, organization selection, upload, semantic search, and RAG chat demos.
- Docker Compose stack for local development.
- Repository documentation, security policy, CI, and local check script.
- Initial Alembic migration environment for versioned database schema management.
- PDF and DOCX parsing with useful source metadata for RAG chunks.
- HTML parsing with title, block, heading, and section metadata for RAG chunks.
- Retrieval score thresholds, metadata filters, debug diagnostics, and optional Cohere reranking.
- MVP header/token authentication and tenant isolation for upload, search, and chat.
- End-to-end local demo flow with generated PDF/DOCX fixtures, debug diagnostics, and tenant isolation checks.
- Tenant-scoped document management API and UI for listing, inspecting chunks, filtering, and deleting documents.
- Async upload processing jobs with tenant-scoped status polling, failure messages, frontend progress, and demo flow support.
- Durable ingestion queue abstraction with inline and Redis providers, separate worker process, retries, attempts tracking, and stale-job failure handling.
- Upload job management with filtered history, pagination, manual retry for failed jobs, safe cancellation for pending jobs, and frontend controls.
- Request observability middleware with `X-Request-ID` propagation, per-request duration logs, and `/metrics` counters.
- Local check script now validates Alembic offline downgrade SQL generation.
- Demo flow now generates, uploads, and searches an HTML fixture.
- Auth context now captures optional user IDs and roles, with admin-gated metrics support.
- Upload route now reads incoming files in bounded chunks and rejects oversized uploads early.
- Request middleware now emits and propagates W3C `traceparent` headers for downstream tracing.
- Persistent audit events for upload creation/retry/cancel and document deletion.
- Optional real database integration tests for pgvector and migrated core tables.
- JWT auth API with users, organizations, and membership-backed tenant access.
- Frontend login, registration, saved JWT session validation, and current organization selection.
- Production config now rejects anonymous access.
- Organization settings API/UI with member listing, pending invitations, and MVP role management.
