-- Bootstrap only. Alembic migrations are the schema source of truth.

-- Enable required PostgreSQL extensions before migrations run.
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Create schemas for multi-tenant support planned in future migrations.
CREATE SCHEMA IF NOT EXISTS tenant_common;

-- Set search path for the current database without hard-coding its name.
DO $$
DECLARE
    db_name text;
BEGIN
    SELECT current_database() INTO db_name;
    EXECUTE format(
        'ALTER DATABASE %I SET search_path TO public, tenant_common',
        db_name
    );
END $$;
