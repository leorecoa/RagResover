# RagResover

RagResover is a local-first Retrieval-Augmented Generation platform for indexing private documents and asking questions over them with cited sources.

It combines FastAPI, PostgreSQL/pgvector, MinIO, Ollama/OpenAI providers, and a lightweight web UI for upload, semantic search, and chat.

## Highlights

- Document upload with validation and raw-file storage in MinIO
- Text chunking with LangChain text splitters
- Vector persistence in PostgreSQL with pgvector
- Semantic search over indexed chunks
- RAG chat with retrieved sources
- Provider switch between OpenAI and local Ollama
- Docker Compose stack for local development
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
  repositories/   SQL and persistence operations
  services/       ingestion, storage, embeddings, chat
```

More detail: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

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

## API

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/health` | Lightweight liveness check |
| GET | `/ready` | Dependency readiness check |
| POST | `/upload` | Upload and index a document |
| POST | `/search` | Semantic search over indexed chunks |
| POST | `/chat` | RAG answer with sources |

Examples: [docs/API_EXAMPLES.md](docs/API_EXAMPLES.md).

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
