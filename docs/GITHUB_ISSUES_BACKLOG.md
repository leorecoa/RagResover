# GitHub Issues Backlog

Use these as the first public issues for the repository.

## 1. Expand Automated Backend Tests

Labels: `testing`, `backend`, `quality`

### Summary

Expand the current pytest suite so future changes can be made safely across more realistic scenarios.

### Scope

- Add integration tests with a real Postgres/pgvector database.
- Add ingestion tests for storage failures and rollback behavior.
- Add service-level tests for provider selection and provider errors.
- Add regression tests for chat source formatting.
- Add test fixtures for sample documents.

### Acceptance Criteria

- Tests run with one documented command.
- CI runs the test suite.
- Tests do not require real OpenAI credentials.

## 2. Add Authentication And Tenant Isolation

Labels: `security`, `backend`, `commercial-readiness`

### Summary

Add authentication and data isolation so each user or organization can only access its own documents.

### Scope

- Choose authentication approach for MVP.
- Add owner or tenant fields to persisted documents and chunks.
- Filter upload, search, and chat by authenticated tenant.
- Update API schemas and docs.

### Acceptance Criteria

- Anonymous access can be disabled.
- Search and chat cannot return documents from another tenant.
- Tests cover access boundaries.

## 3. Expand Document Parsing

Labels: `ingestion`, `rag-quality`, `feature`

### Summary

Support more real-world business documents beyond the current text, Markdown, JSON, PDF, and DOCX parsers.

### Scope

- Add HTML text extraction.
- Add OCR strategy for scanned PDFs.
- Preserve useful metadata when possible, such as page number or section.
- Return clear errors for unsupported or unreadable files.

### Acceptance Criteria

- Users can upload HTML documents.
- Scanned PDFs produce clear OCR-related guidance or are processed by OCR.
- Extracted text is chunked and indexed.
- Search and chat source references include useful document metadata.

## 4. Harden Alembic Migration Workflow

Labels: `database`, `devops`, `quality`

### Summary

Harden the initial Alembic setup for production deployment and future schema changes.

### Scope

- Add a real integration test that upgrades a fresh Postgres database.
- Add migration downgrade smoke checks.
- Add release guidance for running migrations before backend rollout.
- Decide whether migration execution should stay in Docker Compose or move to deployment tooling.

### Acceptance Criteria

- A fresh database can be created through migrations.
- Existing local schema can be aligned without manual SQL editing.
- CI validates migration configuration.

## 5. Expand Retrieval Quality Controls

Labels: `retrieval`, `rag-quality`, `feature`

### Summary

Expand the current retrieval controls with production-grade ranking and evaluation.

### Scope

- Add a real reranking provider implementation.
- Add hybrid keyword + vector search.
- Add retrieval quality evaluation fixtures.
- Add latency and ranking diagnostics.

### Acceptance Criteria

- Reranking can be enabled without changing API contracts.
- Hybrid search can improve recall for exact keywords.
- Retrieval quality can be regression-tested.
