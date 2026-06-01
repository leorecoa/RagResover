# Architecture

RagResover is organized as a modular FastAPI backend with a static demo frontend.

## Runtime Components

```text
Browser
  -> frontend static app
  -> FastAPI backend
  -> PostgreSQL + pgvector
  -> MinIO object storage
  -> Ollama or OpenAI provider
```

## Backend Layers

```text
app/api/routes
  HTTP endpoints. Keep these thin.

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
  -> validate file
  -> upload raw file to MinIO
  -> parse text, PDF, or DOCX content
  -> split into chunks
  -> generate embeddings
  -> persist source document and chunks in Postgres
```

PDF parsing preserves page metadata when text is extractable. DOCX parsing preserves paragraph metadata and section headings when available.

## Retrieval Flow

```text
POST /search
  -> embed query
  -> vector search in document_chunks.embedding
  -> return ranked chunks
```

## Chat Flow

```text
POST /chat
  -> embed question
  -> retrieve top chunks
  -> build context prompt
  -> call LLM provider
  -> return answer and sources
```

## Data Model

Primary tables are managed through Alembic migrations:

- `source_documents`: one row per uploaded file.
- `document_chunks`: one row per chunk with optional vector embedding.
- `conversations`: reserved for future chat history.
- `messages`: reserved for future chat messages.

`scripts/init_db.sql` only bootstraps PostgreSQL extensions and schema search path for local Docker startup.

## Provider Strategy

RagResover supports:

- `openai` for hosted embeddings and chat.
- `ollama` for local embeddings and chat.

Provider settings live in `.env`:

```env
LLM_PROVIDER=ollama
EMBEDDING_PROVIDER=ollama
```

## Current Constraints

- Upload reads the whole file into memory.
- Scanned PDFs without embedded text are not OCR-processed yet.
- HTML parsing is not implemented yet.
- No authentication or tenant isolation yet.
