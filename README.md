
# RagResover

```md
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-TypeScript-61DAFB?style=for-the-badge&logo=react&logoColor=111827)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-pgvector-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-Queue_Worker-DC382D?style=for-the-badge&logo=redis&logoColor=white)
![MinIO](https://img.shields.io/badge/MinIO-Object_Storage-C72E49?style=for-the-badge&logo=minio&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)

![RAG](https://img.shields.io/badge/RAG-Document_AI-7C3AED?style=flat-square)
![Tenant Isolation](https://img.shields.io/badge/Tenant_Isolation-Enabled-16A34A?style=flat-square)
![Async Pipeline](https://img.shields.io/badge/Async_Pipeline-Jobs_%2B_Worker-2563EB?style=flat-square)
![Tests](https://img.shields.io/badge/Tests-Pytest_%2B_Playwright-0A9EDC?style=flat-square)
![CI](https://img.shields.io/badge/CI-GitHub_Actions-2088FF?style=flat-square&logo=githubactions&logoColor=white)
![Release](https://img.shields.io/badge/Release-v0.2.0-blue?style=flat-square)
![Status](https://img.shields.io/badge/Status-Production--Oriented_MVP-success?style=flat-square)
![License](https://img.shields.io/badge/License-Proprietary-red?style=flat-square)
```


RagResover is a local-first Retrieval-Augmented Generation platform for indexing private documents and asking questions over them with cited sources.

It combines FastAPI, PostgreSQL/pgvector, MinIO, Ollama/OpenAI providers, and a React/Vite web UI for upload, semantic search, and chat.

## Highlights

- Async document upload with durable Redis queue, retries, observable status, and job actions
- Tenant-scoped document management with detail, chunk inspection, and delete
- Text extraction for TXT, Markdown, JSON, PDF, and DOCX
- Text chunking with LangChain text splitters
- Vector persistence in PostgreSQL with pgvector
- Semantic search over indexed chunks
- Retrieval controls with score threshold and metadata filters
- Header-based tenant isolation for upload, search, and chat
- RAG chat with retrieved sources
- Provider switch between OpenAI and local Ollama
- Docker Compose stack for local development
- Alembic migrations for versioned database schema changes
- React/Vite frontend for demos and manual usage

## Architecture

```text
Frontend -> FastAPI -> Redis queue -> ingestion worker -> Services -> PostgreSQL/pgvector
                         |                              |
                         +-> MinIO raw files            +-> Ollama or OpenAI
```

Backend package layout:

```text
app/
  api/            HTTP routes and Pydantic schemas
  core/           app factory, config, logging, lifecycle
  db/             async database session
  migrations/     Alembic database migrations
  repositories/   SQL and persistence operations
  services/       ingestion, storage, embeddings, chat
  workers/        separate ingestion worker entrypoints
```

More detail: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

Supported upload content types:

- `text/plain`
- `text/markdown`
- `application/json`
- `application/pdf`
- `application/vnd.openxmlformats-officedocument.wordprocessingml.document`

## Quick Start

1. Copy environment variables:

```powershell
Copy-Item .env.example .env
```

2. Download the local Ollama models used by `.env.example`:

```powershell
ollama pull llama3.2:3b
ollama pull nomic-embed-text
```

3. Start the backend stack:

```powershell
docker compose up --build
```

4. Start the frontend in another terminal:

```powershell
cd frontend
npm run dev
```

5. Open:

```text
Frontend: http://localhost:3000
API docs: http://localhost:8000/docs
```

## Demo

Run the complete local demo flow after the stack is up:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/demo_flow.ps1
```

The demo generates local PDF/DOCX fixtures under `.demo/`, uploads them with
`X-Tenant-ID`, runs search/chat, prints source metadata and retrieval
diagnostics when `DEBUG=true`, and validates that one tenant cannot retrieve
another tenant's documents.

Full walkthrough: [docs/DEMO.md](docs/DEMO.md).

## API

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/health` | Lightweight liveness check |
| GET | `/ready` | Dependency readiness check |
| POST | `/upload` | Create an async upload processing job |
| GET | `/uploads` | List upload jobs for the current tenant |
| GET | `/uploads/{job_id}` | Inspect one upload job status |
| POST | `/uploads/{job_id}/retry` | Retry a failed upload job |
| POST | `/uploads/{job_id}/cancel` | Cancel a pending upload job |
| GET | `/documents` | List indexed documents for the current tenant |
| GET | `/documents/{document_id}` | Inspect one tenant-scoped document |
| GET | `/documents/{document_id}/chunks` | Inspect paginated chunks for a document |
| DELETE | `/documents/{document_id}` | Delete one tenant-scoped document and its chunks |
| POST | `/search` | Semantic search over indexed chunks |
| POST | `/chat` | RAG answer with sources |

Examples: [docs/API_EXAMPLES.md](docs/API_EXAMPLES.md).

Search and chat accept optional `score_threshold` and `metadata_filters` fields. When `DEBUG=true`, responses include retrieval diagnostics such as fetch size, effective threshold, filters, embedding provider, and reranker provider.

Upload now stores the raw file in MinIO, returns `202 Accepted` with a `job_id`, and enqueues the job. Poll `GET /uploads/{job_id}` until the status is `completed`, `failed`, or `canceled`; completed jobs include the indexed `document_id`, while failed jobs include attempts and error details. `GET /uploads` supports filters such as `status`, `filename`, `content_type`, date range, `document_id`, `limit`, and `offset`.

Upload, upload status, documents, search, and chat accept `X-Tenant-ID` to isolate data by tenant. Anonymous access uses `DEFAULT_TENANT_ID` while `ALLOW_ANONYMOUS_ACCESS=true`; set `ALLOW_ANONYMOUS_ACCESS=false` to require tenant headers, and set `API_AUTH_TOKEN` to require `Authorization: Bearer ...` or `X-API-Key`.

## Frontend

The React/Vite frontend in `frontend/` includes:

- API readiness panel
- async document upload with processing status
- upload job history with filters, retry, and cancel actions
- document management with metadata and chunk inspection
- semantic search
- chat with source display

Useful frontend commands:

```powershell
cd frontend
npx playwright install chromium
npm run dev
npm run build
npm run test:e2e
npm run preview
```

## Development

Run local checks:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/check.ps1
```

Run only backend tests:

```powershell
venv\Scripts\python.exe -m pytest tests
```

Run database migrations:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/migrate.ps1
```

Queue modes:

```powershell
# Simple local/test mode, no Redis worker required
$env:INGESTION_QUEUE_PROVIDER="inline"

# Durable mode, used by docker compose with the worker service
$env:INGESTION_QUEUE_PROVIDER="redis"
```

Useful commands:

```powershell
docker compose up --build
docker compose down
docker compose down -v
```

`docker compose down -v` removes local database and MinIO data.

## Roadmap

See [docs/ROADMAP.md](docs/ROADMAP.md).

## Commercial Readiness

Use these documents when preparing a public repository, demo, or paid offer:

- [docs/COMMERCIAL_READINESS.md](docs/COMMERCIAL_READINESS.md)
- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)
- [CHANGELOG.md](CHANGELOG.md)

## Publishing To GitHub

Before pushing:

```powershell
git init
git add .
git status
```

Confirm that `.env`, `venv/`, uploaded documents, database dumps, and logs are not staged.

## Security

Never commit `.env`, API keys, customer documents, or MinIO/Postgres volumes.

See [SECURITY.md](SECURITY.md).

## License

This project is proprietary by default. See [LICENSE](LICENSE).
