-- Use this only for an existing local database created before Ollama support.
-- Fresh Docker volumes use init_db.sql automatically.

DROP INDEX IF EXISTS documents_embedding_idx;
DROP INDEX IF EXISTS document_chunks_embedding_idx;

ALTER TABLE IF EXISTS documents
ALTER COLUMN embedding TYPE vector;

ALTER TABLE IF EXISTS document_chunks
ALTER COLUMN embedding TYPE vector;
