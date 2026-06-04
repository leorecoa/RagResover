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

The compose stack runs `alembic upgrade head` before the backend starts. It also
starts a separate ingestion worker with `INGESTION_QUEUE_PROVIDER=redis`.

Then start the static frontend:

```powershell
cd frontend
npm run serve
```

## Production Checklist

Before selling this as a hosted product, add or configure:

- Real authentication and authorization.
- Hardened user membership checks beyond the MVP tenant header.
- Strong Postgres and MinIO credentials.
- HTTPS/TLS at the edge.
- Restricted CORS origins.
- Rate limiting for upload, search, and chat.
- Request IDs, W3C trace context propagation, and structured logs.
- Protected `/metrics` access for production observability endpoints.
- Backup and restore for Postgres and object storage.
- Alembic migrations in the deployment pipeline.
- A durable Redis instance for ingestion queues.
- Separate API and ingestion worker processes.
- Operational access controls for retry/cancel actions in admin contexts.
- Retention policy for audit events.
- Monitoring for API latency, provider errors, token usage, and storage growth.

## Environment Notes

Local defaults are intentionally simple. Production should override:

```env
APP_ENV=production
DEBUG=false
CORS_ALLOW_ORIGINS=https://your-domain.example
STORAGE_REQUIRED=true
DATABASE_URL=postgresql+asyncpg://...
REDIS_URL=redis://...
INGESTION_QUEUE_PROVIDER=redis
INGESTION_JOB_MAX_ATTEMPTS=3
STORAGE_ACCESS_KEY=...
STORAGE_SECRET_KEY=...
ALLOW_ANONYMOUS_ACCESS=false
API_AUTH_TOKEN=change-this-token
ADMIN_ROLE_NAME=admin
METRICS_REQUIRE_ADMIN=true
```

When `METRICS_REQUIRE_ADMIN=true`, callers must provide a valid API token and
`X-User-Roles` containing the configured admin role.

Run migrations during deploy:

```powershell
alembic upgrade head
```

Run the API and worker as separate processes:

```powershell
uvicorn app.core.app:create_app --factory --host 0.0.0.0 --port 8000
python -m app.workers.ingestion_worker
```

For tests or a no-Redis local shell, set `INGESTION_QUEUE_PROVIDER=inline`.

## Provider Choice

Ollama is useful for local demos and private offline workflows. Hosted OpenAI models are usually easier to scale commercially because they remove local GPU/model operations, but they require cost controls and key management.
