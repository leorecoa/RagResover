
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
- Text extraction for TXT, Markdown, HTML, JSON, PDF, and DOCX
- Text chunking with LangChain text splitters
- Vector persistence in PostgreSQL with pgvector
- Semantic search over indexed chunks
- Retrieval controls with score threshold and metadata filters
- Optional Cohere reranking for retrieved candidates
- Header-based tenant isolation for upload, search, and chat
- JWT auth API with users, organizations, and membership-backed tenant access
- Persistent audit events for mutable upload and document operations
- RAG chat with retrieved sources
- Provider switch between OpenAI and local Ollama
- Docker Compose stack for local development
- Alembic migrations for versioned database schema changes
- React/Vite frontend with login, organization selection, demos, and manual usage

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
  repositories/   SQL, persistence operations, and audit events
  services/       ingestion, storage, embeddings, chat
  workers/        separate ingestion worker entrypoints
```

More detail: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

Supported upload content types:

- `text/plain`
- `text/markdown`
- `text/html`
- `application/xhtml+xml`
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

The demo generates local PDF/DOCX/HTML fixtures under `.demo/`, uploads them with
`X-Tenant-ID`, runs search/chat, prints source metadata and retrieval
diagnostics when `DEBUG=true`, and validates that one tenant cannot retrieve
another tenant's documents.

Full walkthrough: [docs/DEMO.md](docs/DEMO.md).

## API

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/health` | Lightweight liveness check |
| GET | `/ready` | Dependency readiness check |
| GET | `/metrics` | Prometheus-style request counters and duration sums |
| POST | `/auth/register` | Create a user, organization, owner membership, and JWT |
| POST | `/auth/login` | Authenticate with email/password and return JWT |
| GET | `/auth/me` | Inspect the current JWT identity and memberships |
| GET | `/organizations/current` | Inspect current organization settings and caller role |
| PATCH | `/organizations/current` | Rename the current organization |
| GET | `/organizations/current/members` | List organization members and roles |
| PATCH | `/organizations/current/members/{user_id}` | Update one member role |
| GET | `/organizations/current/invitations` | List organization invitations |
| POST | `/organizations/current/invitations` | Create or refresh a pending invitation |
| GET | `/organizations/current/api-keys` | List redacted tenant-scoped API keys |
| POST | `/organizations/current/api-keys` | Create a tenant-scoped API key |
| DELETE | `/organizations/current/api-keys/{api_key_id}` | Revoke a tenant-scoped API key |
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

Set `RERANKER_PROVIDER=cohere`, `COHERE_API_KEY`, and optionally `COHERE_RERANK_MODEL` to rerank retrieved candidates before search/chat responses are returned.

Upload now stores the raw file in MinIO, returns `202 Accepted` with a `job_id`, and enqueues the job. Poll `GET /uploads/{job_id}` until the status is `completed`, `failed`, or `canceled`; completed jobs include the indexed `document_id`, while failed jobs include attempts and error details. `GET /uploads` supports filters such as `status`, `filename`, `content_type`, date range, `document_id`, `limit`, and `offset`.

Upload, upload status, documents, search, and chat accept `X-Tenant-ID` to isolate data by tenant. Anonymous access uses `DEFAULT_TENANT_ID` only while `ALLOW_ANONYMOUS_ACCESS=true`; production refuses to start with anonymous access enabled. Real auth is available through `/auth/register` and `/auth/login`, which return JWT bearer tokens backed by users, organizations, and memberships. Tenant-scoped API keys can be created under `/organizations/current/api-keys` and used with `X-API-Key`; keys are stored hashed and the raw key is shown only once. The React frontend stores the JWT locally, validates saved sessions through `/auth/me`, and sends the selected organization as `X-Tenant-ID`. The legacy shared `API_AUTH_TOKEN` path remains available for controlled deployments and compatibility.

RBAC is applied to sensitive actions: `viewer` can read, `member` can upload/retry/cancel jobs, and `owner`/`admin` can manage organization settings, API keys, invites, roles, and document deletion.

Mutable upload/document actions write best-effort audit events with tenant, optional user, roles, action, resource, and metadata.

Every response includes `X-Request-ID` and `traceparent`. Send your own `X-Request-ID` or W3C `traceparent` to correlate client logs with backend request duration logs and downstream traces.

`GET /metrics` exposes process-local Prometheus-style counters for HTTP requests and duration sums. Set `METRICS_REQUIRE_ADMIN=true` and use either a JWT membership with the configured admin role or the legacy shared token plus `X-User-Roles: admin`.

## Frontend

The React/Vite frontend in `frontend/` includes:

- login and registration backed by the JWT auth API
- current organization selection from authenticated memberships
- organization settings with member roles and invitations
- tenant-scoped API key creation and revocation
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
