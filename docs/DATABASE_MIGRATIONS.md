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

Generate downgrade SQL for smoke review:

```powershell
venv\Scripts\alembic.exe downgrade head:base --sql
```

Check current revision:

```powershell
venv\Scripts\alembic.exe current
```

Run optional real database integration tests after applying migrations:

```powershell
$env:RUN_DATABASE_INTEGRATION="1"
venv\Scripts\python.exe -m pytest tests/test_database_integration.py
```

These tests are skipped by default and verify pgvector plus core migrated tables
against `DATABASE_URL`.

## Docker Compose

`docker compose up --build` starts a dedicated `migrate` service before the backend. That service runs:

```text
alembic upgrade head
```

## Bootstrap SQL

`scripts/init_db.sql` is intentionally small. It only enables required PostgreSQL extensions and search path setup for local Docker startup. Tables, indexes, and future schema changes belong in Alembic migrations under `migrations/versions/`.

The local `scripts/check.ps1` validates both offline upgrade SQL and offline
downgrade SQL generation.

Audit events and identity tables (`users`, `organizations`,
`organization_memberships`, and `organization_invitations`) are created by
Alembic migrations, not by bootstrap SQL.
