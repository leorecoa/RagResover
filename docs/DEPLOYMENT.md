# Deployment

This guide separates the current local demo setup from the requirements for a commercial production deployment.

## Local Demo

Use Docker Compose for the core infrastructure:

```powershell
Copy-Item .env.example .env
ollama pull llama3.2:3b
ollama pull nomic-embed-text
docker compose up --build
```

Then start the static frontend:

```powershell
cd frontend
npm run serve
```

## Production Checklist

Before selling this as a hosted product, add or configure:

- Real authentication and authorization.
- Per-user or per-organization tenant isolation.
- Strong Postgres and MinIO credentials.
- HTTPS/TLS at the edge.
- Restricted CORS origins.
- Rate limiting for upload, search, and chat.
- Request IDs and structured logs.
- Backup and restore for Postgres and object storage.
- Alembic migrations instead of only init SQL.
- Monitoring for API latency, provider errors, token usage, and storage growth.

## Environment Notes

Local defaults are intentionally simple. Production should override:

```env
APP_ENV=production
DEBUG=false
CORS_ALLOW_ORIGINS=https://your-domain.example
STORAGE_REQUIRED=true
DATABASE_URL=postgresql+asyncpg://...
STORAGE_ACCESS_KEY=...
STORAGE_SECRET_KEY=...
```

## Provider Choice

Ollama is useful for local demos and private offline workflows. Hosted OpenAI models are usually easier to scale commercially because they remove local GPU/model operations, but they require cost controls and key management.
