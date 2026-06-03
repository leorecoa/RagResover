# Architecture

RagResover is organized as a modular FastAPI backend with a React/Vite frontend.

## Runtime Components

```text
Browser
  -> React/Vite frontend
  -> FastAPI backend
  -> PostgreSQL + pgvector
  -> MinIO object storage
  -> Ollama or OpenAI provider
```

## Backend Layers

```text
app/api/routes
  HTTP endpoints. Keep these thin.

app/api/dependencies
  Request dependencies such as tenant authentication.

app/api/schemas
  Pydantic request and response contracts.

app/services
  Business workflows and external provider integrations.

app/repositories
  SQL and persistence operations.

app/db
  SQLAlchemy async engine and session factory.

app/core
  Config, app factory, logging, constants, lifespan.

migrations
  Alembic migration environment and versioned schema changes.
```

## Ingestion Flow

```text
POST /upload
  -> resolve tenant from headers/config
  -> validate file
  -> upload raw file to MinIO
  -> parse text, PDF, or DOCX content
  -> split into chunks
  -> generate embeddings
  -> persist source document and chunks in Postgres
```

PDF parsing preserves page metadata when text is extractable. DOCX parsing preserves paragraph metadata and section headings when available.

## Document Management Flow

```text
GET /documents
  -> resolve tenant from headers/config
  -> list source_documents scoped by tenant_id
  -> include chunk counts and document metadata

GET /documents/{document_id}
  -> resolve tenant from headers/config
  -> return document details only when tenant_id matches

GET /documents/{document_id}/chunks
  -> resolve tenant from headers/config
  -> verify document ownership
  -> return paginated chunks ordered by chunk_index

DELETE /documents/{document_id}
  -> resolve tenant from headers/config
  -> delete only matching tenant document
  -> cascade-delete document_chunks through the database foreign key
```

## Retrieval Flow

```text
POST /search
  -> resolve tenant from headers/config
  -> embed query
  -> vector search in document_chunks.embedding
  -> constrain results by tenant_id
  -> apply optional score threshold and metadata filters
  -> optionally pass through a reranker interface
  -> return ranked chunks
```

## Chat Flow

```text
POST /chat
  -> resolve tenant from headers/config
  -> embed question
  -> retrieve top chunks with the same retrieval controls used by search
  -> constrain results by tenant_id
  -> build context prompt
  -> call LLM provider
  -> return answer and sources
```

When `DEBUG=true`, search and chat responses include retrieval diagnostics with the effective threshold, metadata filters, fetch limit, embedding provider, and reranker provider.

## Data Model

Primary tables are managed through Alembic migrations:

- `source_documents`: one row per uploaded file.
- `document_chunks`: one row per chunk with optional vector embedding.
- `conversations`: reserved for future chat history.
- `messages`: reserved for future chat messages.

`scripts/init_db.sql` only bootstraps PostgreSQL extensions and schema search path for local Docker startup.

Tenant isolation is stored in `tenant_id` columns. Upload writes the current tenant into `source_documents` and `document_chunks`; document management, search, and chat filter by that same tenant before returning data.

## Authentication

The MVP uses header-based tenant auth:

- `X-Tenant-ID`: tenant or organization identifier.
- `ALLOW_ANONYMOUS_ACCESS=true`: missing tenant header falls back to `DEFAULT_TENANT_ID`.
- `ALLOW_ANONYMOUS_ACCESS=false`: missing tenant header returns `401`.
- `API_AUTH_TOKEN`: optional shared token. When configured, requests must send `Authorization: Bearer <token>` or `X-API-Key: <token>`.

## Provider Strategy

RagResover supports:

- `openai` for hosted embeddings and chat.
- `ollama` for local embeddings and chat.

Provider settings live in `.env`:

```env
LLM_PROVIDER=ollama
EMBEDDING_PROVIDER=ollama
```

## Retrieval Controls

RagResover supports:

- optional `score_threshold` per search/chat request
- optional `RETRIEVAL_SCORE_THRESHOLD` default from `.env`
- exact JSONB metadata filters through `metadata_filters`
- a no-op reranker interface prepared for future providers
- debug-only retrieval diagnostics

## Current Constraints

- Upload reads the whole file into memory.
- Scanned PDFs without embedded text are not OCR-processed yet.
- HTML parsing is not implemented yet.
- Reindexing is not implemented yet; the planned route is `POST /documents/{document_id}/reindex`.
- Authentication is MVP header/token based, not full user account management yet.
