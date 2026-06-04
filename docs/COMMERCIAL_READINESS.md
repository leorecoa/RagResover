# Commercial Readiness

RagResover is currently a strong technical MVP. It is suitable for local demos,
technical validation, and controlled pilots, but it should not be sold as a
fully managed enterprise product without the production hardening below.

## Ready In Current MVP

- Modular FastAPI backend with thin routes, services, repositories, and schemas.
- Docker-based local environment with Postgres/pgvector, Redis, MinIO, backend, and worker.
- Upload, parsing, chunking, embeddings, semantic search, and RAG chat.
- TXT, Markdown, JSON, HTML, PDF, and DOCX parsing with source metadata.
- PostgreSQL/pgvector persistence for source documents and chunks.
- MinIO-compatible raw file storage.
- Redis-backed durable ingestion queue with separate worker process.
- Async upload jobs with status polling, retries, cancellation, and filtered history.
- Alembic migrations with offline upgrade and downgrade SQL checks.
- Backend pytest suite, frontend Playwright E2E suite, and local check script.
- Header-based tenant isolation for upload, documents, search, and chat.
- MVP API token support via bearer token or `X-API-Key`.
- Optional user/role headers for role-aware operational checks.
- Tenant-scoped document management UI and API.
- Retrieval controls with score threshold, metadata filters, diagnostics, and optional Cohere reranking.
- Request IDs, W3C `traceparent` propagation, duration logs, and `/metrics`.
- Best-effort persistent audit events for mutable upload and document operations.
- End-to-end local demo flow with generated fixtures and tenant isolation checks.
- Initial deployment, security, migration, API, and demo documentation.

## Partially Ready

- Authentication is usable for MVP demos, but it is header/token based rather
  than real user account management.
- Tenant isolation exists at the API/repository level, but customer membership
  validation is not backed by a users/organizations model yet.
- Audit events are persisted, but retention, export, review workflows, and
  compliance policy still need product decisions.
- Cohere reranking is implemented, but retrieval quality still needs evaluation
  datasets, regression scoring, and cost/latency tuning.
- `/metrics`, request IDs, and trace context exist, but production monitoring
  still needs dashboards, alerts, and trace collection.
- Optional real database integration tests exist, but they are not enabled by
  default in CI.
- Docker Compose is strong for local/prototype operation, but cloud deployment
  hardening is still required.

## Still Required For Paid Customers

- Real user accounts and login flow.
- Organization membership validation.
- RBAC permissions for admin and end-user actions.
- Rate limiting and abuse protection for upload, search, chat, and management endpoints.
- OCR for scanned PDFs.
- Hybrid lexical + vector search.
- Retrieval quality evaluation harness and acceptance thresholds.
- Backup and restore guide for Postgres and object storage.
- Audit log retention and compliance process.
- Cloud deployment hardening with TLS, secrets management, managed Postgres/Redis/object storage, and operational runbooks.
- Production monitoring dashboards, alerts, and incident response process.
- Cost controls for hosted LLM, embedding, and reranking providers.

## Suggested Product Positioning

Short description:

```text
RagResover is a private document intelligence API that lets teams upload internal files and ask questions with cited answers.
```

Demo promise:

```text
Upload documents, search them semantically, and ask grounded questions through a local-first RAG stack.
```

Avoid promising:

- Full enterprise security.
- Production-grade account and membership management.
- Legal, medical, or financial correctness.
- Support for every file type.
- Fully managed cloud operations.

Those become paid roadmap milestones after the MVP is hardened.
