# Roadmap

## MVP Stabilization

- Add visual regression coverage for the frontend.
- Pin dependency versions.
- Improve error responses and request IDs.
- Add structured worker metrics and queue depth monitoring.

## Document Processing

- Add `POST /documents/{document_id}/reindex`.
- Add HTML parser.
- Add OCR for scanned PDFs.
- Preserve metadata such as page number and section title.
- Add chunk deduplication.

## Retrieval Quality

- Add real Cohere reranking implementation behind the reranker interface.
- Add hybrid search with keyword + vector retrieval.
- Add richer retrieval evaluation fixtures.

## Product Features

- Add audit log entries for upload job retry/cancel actions.
- Add persistent chat history.
- Add source downloads.
- Add user accounts.
- Add organization/tenant separation.
- Add admin dashboard.

## Commercial Readiness

- Add authentication and authorization.
- Add audit logs.
- Add rate limits.
- Add deployment guide.
- Add backup and restore guide.
- Add pricing/package boundaries.
