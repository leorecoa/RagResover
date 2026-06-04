import os

import anyio
import asyncpg
import pytest

from app.core.config import settings


pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_DATABASE_INTEGRATION") != "1",
    reason="Set RUN_DATABASE_INTEGRATION=1 to run real database integration tests.",
)


def database_url_for_asyncpg() -> str:
    return str(settings.DATABASE_URL).replace("postgresql+asyncpg://", "postgresql://")


async def fetch_value(query: str):
    connection = await asyncpg.connect(database_url_for_asyncpg())
    try:
        return await connection.fetchval(query)
    finally:
        await connection.close()


def test_real_database_has_pgvector_extension():
    async def call_database():
        return await fetch_value(
            "SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector')"
        )

    assert anyio.run(call_database) is True


def test_real_database_has_current_core_tables():
    async def call_database():
        connection = await asyncpg.connect(database_url_for_asyncpg())
        try:
            rows = await connection.fetch(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = ANY($1::text[])
                """,
                [
                    "source_documents",
                    "document_chunks",
                    "ingestion_jobs",
                    "audit_events",
                    "users",
                    "organizations",
                    "organization_memberships",
                    "organization_invitations",
                    "organization_api_keys",
                ],
            )
            return {row["table_name"] for row in rows}
        finally:
            await connection.close()

    assert anyio.run(call_database) == {
        "source_documents",
        "document_chunks",
        "ingestion_jobs",
        "audit_events",
        "users",
        "organizations",
        "organization_memberships",
        "organization_invitations",
        "organization_api_keys",
    }
