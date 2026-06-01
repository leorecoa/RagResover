
# RagResover

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-pgvector-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![MinIO](https://img.shields.io/badge/MinIO-Object_Storage-C72E49?style=for-the-badge&logo=minio&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Ollama](https://img.shields.io/badge/Ollama-Local_LLM-000000?style=for-the-badge&logo=ollama&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-Provider-412991?style=for-the-badge&logo=openai&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-Text_Splitting-1C3C3C?style=for-the-badge)
![Alembic](https://img.shields.io/badge/Alembic-Migrations-6BA81E?style=for-the-badge)
![Pytest](https://img.shields.io/badge/Pytest-Tested-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white)

![RAG](https://img.shields.io/badge/RAG-Retrieval_Augmented_Generation-blueviolet?style=flat-square)
![Local First](https://img.shields.io/badge/Local--First-Private_Documents-success?style=flat-square)
![Semantic Search](https://img.shields.io/badge/Semantic_Search-pgvector-informational?style=flat-square)
![Status](https://img.shields.io/badge/Status-MVP_in_progress-yellow?style=flat-square)
![License](https://img.shields.io/badge/License-Proprietary-red?style=flat-square)

RagResover is a local-first Retrieval-Augmented Generation platform for indexing private documents and asking questions over them with cited sources.

It combines FastAPI, PostgreSQL/pgvector, MinIO, Ollama/OpenAI providers, and a lightweight web UI for upload, semantic search, and chat.

## Highlights

- Document upload with validation and raw-file storage in MinIO
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
- Static frontend for demos and manual usage

## Architecture

```text
Frontend -> FastAPI -> Services -> Repositories -> PostgreSQL/pgvector
                         |
                         +-> MinIO
                         +-> Ollama or OpenAI
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
npm run serve
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
| POST | `/upload` | Upload and index a document |
| POST | `/search` | Semantic search over indexed chunks |
| POST | `/chat` | RAG answer with sources |

Examples: [docs/API_EXAMPLES.md](docs/API_EXAMPLES.md).

Search and chat accept optional `score_threshold` and `metadata_filters` fields. When `DEBUG=true`, responses include retrieval diagnostics such as fetch size, effective threshold, filters, embedding provider, and reranker provider.

Upload, search, and chat accept `X-Tenant-ID` to isolate documents by tenant. Anonymous access uses `DEFAULT_TENANT_ID` while `ALLOW_ANONYMOUS_ACCESS=true`; set `ALLOW_ANONYMOUS_ACCESS=false` to require tenant headers, and set `API_AUTH_TOKEN` to require `Authorization: Bearer ...` or `X-API-Key`.

## Frontend

The static frontend in `frontend/` includes:

- API readiness panel
- document upload
- semantic search
- chat with source display

It does not require a build step.

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
