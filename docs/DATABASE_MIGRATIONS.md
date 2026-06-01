# Database Migrations

RagResover uses Alembic for versioned database schema changes.

## Local Commands

Run migrations:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/migrate.ps1
```

Or directly:

```powershell
venv\Scripts\alembic.exe upgrade head
```

Generate offline SQL for review:

```powershell
venv\Scripts\alembic.exe upgrade head --sql
```

Check current revision:

```powershell
venv\Scripts\alembic.exe current
```

## Docker Compose

`docker compose up --build` starts a dedicated `migrate` service before the backend. That service runs:

```text
alembic upgrade head
```

## Bootstrap SQL

`scripts/init_db.sql` is intentionally small. It only enables required PostgreSQL extensions and search path setup for local Docker startup. Tables, indexes, and future schema changes belong in Alembic migrations under `migrations/versions/`.
