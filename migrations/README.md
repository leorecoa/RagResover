# Database Migrations

Alembic migrations are the source of truth for the database schema.

Useful commands:

```powershell
alembic upgrade head
alembic current
alembic history
alembic downgrade -1
```

The local Docker Compose stack runs `alembic upgrade head` before starting the backend.
