# API Examples

Base URL:

```text
http://localhost:8000
```

## Health

```powershell
Invoke-RestMethod http://localhost:8000/health
```

## Readiness

```powershell
Invoke-RestMethod http://localhost:8000/ready
```

## Metrics

```powershell
Invoke-RestMethod http://localhost:8000/metrics
```

The response is Prometheus-style text with request counters and duration sums.

If `METRICS_REQUIRE_ADMIN=true`, include auth and admin role headers:

```powershell
Invoke-RestMethod http://localhost:8000/metrics `
  -Headers @{
    "Authorization" = "Bearer your-token"
    "X-Tenant-ID" = "tenant-admin"
    "X-User-ID" = "admin-user"
    "X-User-Roles" = "admin"
  }
```

All API responses include `X-Request-ID` and `traceparent` headers. Clients may
send their own values to correlate request logs and distributed traces.

## Upload

```powershell
curl.exe -X POST http://localhost:8000/upload `
  -H "X-Tenant-ID: tenant-demo" `
  -F "file=@README.md;type=text/markdown"
```

PDF:

```powershell
curl.exe -X POST http://localhost:8000/upload `
  -H "X-Tenant-ID: tenant-demo" `
  -F "file=@manual.pdf;type=application/pdf"
```

DOCX:

```powershell
curl.exe -X POST http://localhost:8000/upload `
  -H "X-Tenant-ID: tenant-demo" `
  -F "file=@manual.docx;type=application/vnd.openxmlformats-officedocument.wordprocessingml.document"
```

HTML:

```powershell
curl.exe -X POST http://localhost:8000/upload `
  -H "X-Tenant-ID: tenant-demo" `
  -F "file=@manual.html;type=text/html"
```

Example response:

```json
{
  "job_id": "d7cefc92-9a7f-4ca3-9b52-b6e68853218e",
  "filename": "README.md",
  "content_type": "text/markdown",
  "file_size": 4096,
  "status": "pending",
  "tenant_id": "tenant-demo",
  "error_message": null,
  "attempts": 0,
  "max_attempts": 3,
  "last_error": null,
  "document_id": null,
  "created_at": "2026-06-03T12:00:00",
  "updated_at": "2026-06-03T12:00:00",
  "started_at": null,
  "finished_at": null,
  "message": "Upload recebido para processamento."
}
```

Poll job status:

```powershell
Invoke-RestMethod http://localhost:8000/uploads/d7cefc92-9a7f-4ca3-9b52-b6e68853218e `
  -Headers @{ "X-Tenant-ID" = "tenant-demo" }
```

Completed response:

```json
{
  "job_id": "d7cefc92-9a7f-4ca3-9b52-b6e68853218e",
  "filename": "README.md",
  "content_type": "text/markdown",
  "file_size": 4096,
  "status": "completed",
  "tenant_id": "tenant-demo",
  "error_message": null,
  "attempts": 1,
  "max_attempts": 3,
  "last_error": null,
  "document_id": "67a96a52-3b77-4efa-b6eb-e065ca66c4f4",
  "created_at": "2026-06-03T12:00:00",
  "updated_at": "2026-06-03T12:00:04",
  "started_at": "2026-06-03T12:00:01",
  "finished_at": "2026-06-03T12:00:04",
  "message": "Upload recebido para processamento."
}
```

Failed response after retries:

```json
{
  "job_id": "d7cefc92-9a7f-4ca3-9b52-b6e68853218e",
  "filename": "broken.pdf",
  "content_type": "application/pdf",
  "file_size": 1024,
  "status": "failed",
  "tenant_id": "tenant-demo",
  "error_message": "Arquivo PDF invalido.",
  "attempts": 3,
  "max_attempts": 3,
  "last_error": "Arquivo PDF invalido.",
  "document_id": null,
  "created_at": "2026-06-03T12:00:00",
  "updated_at": "2026-06-03T12:00:10",
  "started_at": "2026-06-03T12:00:09",
  "finished_at": "2026-06-03T12:00:10",
  "message": "Upload recebido para processamento."
}
```

List recent upload jobs for the tenant:

```powershell
Invoke-RestMethod "http://localhost:8000/uploads?limit=20" `
  -Headers @{ "X-Tenant-ID" = "tenant-demo" }
```

Filter and paginate upload jobs:

```powershell
Invoke-RestMethod "http://localhost:8000/uploads?status=failed&filename=manual&content_type=application/pdf&limit=10&offset=0" `
  -Headers @{ "X-Tenant-ID" = "tenant-demo" }
```

Retry a failed upload job:

```powershell
Invoke-RestMethod http://localhost:8000/uploads/d7cefc92-9a7f-4ca3-9b52-b6e68853218e/retry `
  -Method Post `
  -Headers @{ "X-Tenant-ID" = "tenant-demo" }
```

Cancel a pending upload job:

```powershell
Invoke-RestMethod http://localhost:8000/uploads/d7cefc92-9a7f-4ca3-9b52-b6e68853218e/cancel `
  -Method Post `
  -Headers @{ "X-Tenant-ID" = "tenant-demo" }
```

Only `failed` jobs can be retried manually. Only `pending` jobs can be canceled;
`processing` jobs are already running in the worker and return `409 Conflict`.

## Search

```powershell
$body = @{
  query = "Quais endpoints existem no projeto?"
  top_k = 3
  score_threshold = 0.7
  metadata_filters = @{
    source = "manual.pdf"
  }
} | ConvertTo-Json

Invoke-RestMethod http://localhost:8000/search `
  -Method Post `
  -Body $body `
  -ContentType "application/json" `
  -Headers @{ "X-Tenant-ID" = "tenant-demo" }
```

When `DEBUG=true`, the response includes retrieval diagnostics:

```json
{
  "query": "Quais endpoints existem no projeto?",
  "results": [],
  "diagnostics": {
    "requested_top_k": 3,
    "fetch_limit": 12,
    "returned_count": 0,
    "tenant_id": "tenant-demo",
    "score_threshold": 0.7,
    "metadata_filters": {
      "source": "manual.pdf"
    },
    "embedding_provider": "ollama",
    "reranker_provider": "none",
    "reranker_applied": false
  }
}
```

To enable Cohere reranking for search/chat, configure:

```powershell
$env:RERANKER_PROVIDER="cohere"
$env:COHERE_API_KEY="your-cohere-key"
$env:COHERE_RERANK_MODEL="rerank-v4.0-pro"
```

When enabled, diagnostics show `"reranker_provider": "cohere"` and
`"reranker_applied": true`.

## Documents

List tenant documents:

```powershell
Invoke-RestMethod http://localhost:8000/documents `
  -Headers @{ "X-Tenant-ID" = "tenant-demo" }
```

Filter by source/content type:

```powershell
Invoke-RestMethod "http://localhost:8000/documents?source=manual&content_type=application/pdf" `
  -Headers @{ "X-Tenant-ID" = "tenant-demo" }
```

Example response:

```json
{
  "documents": [
    {
      "id": "67a96a52-3b77-4efa-b6eb-e065ca66c4f4",
      "file_name": "manual.pdf",
      "content_type": "application/pdf",
      "file_size": 2048,
      "chunks_count": 4,
      "tenant_id": "tenant-demo",
      "created_at": "2026-06-01T12:00:00",
      "metadata": {
        "source": "manual.pdf"
      }
    }
  ]
}
```

Inspect one document:

```powershell
Invoke-RestMethod http://localhost:8000/documents/67a96a52-3b77-4efa-b6eb-e065ca66c4f4 `
  -Headers @{ "X-Tenant-ID" = "tenant-demo" }
```

Inspect chunks:

```powershell
Invoke-RestMethod "http://localhost:8000/documents/67a96a52-3b77-4efa-b6eb-e065ca66c4f4/chunks?page=1&page_size=20" `
  -Headers @{ "X-Tenant-ID" = "tenant-demo" }
```

Delete a document and its chunks:

```powershell
Invoke-RestMethod http://localhost:8000/documents/67a96a52-3b77-4efa-b6eb-e065ca66c4f4 `
  -Method Delete `
  -Headers @{ "X-Tenant-ID" = "tenant-demo" }
```

All document management endpoints are tenant-scoped. A document uploaded by
`tenant-other` returns `404` when accessed from `tenant-demo`.

## Chat

```powershell
$body = @{
  question = "Quais endpoints existem no projeto?"
  top_k = 3
  score_threshold = 0.7
  metadata_filters = @{
    source = "manual.pdf"
  }
} | ConvertTo-Json

Invoke-RestMethod http://localhost:8000/chat `
  -Method Post `
  -Body $body `
  -ContentType "application/json" `
  -Headers @{ "X-Tenant-ID" = "tenant-demo" }
```

If `API_AUTH_TOKEN` is configured:

```powershell
$headers = @{
  "X-Tenant-ID" = "tenant-demo"
  "Authorization" = "Bearer your-token"
}
```

Role-aware administrative checks use optional `X-User-ID` and comma-separated
`X-User-Roles` headers.

## Demo Flow

For an end-to-end product demo, start the stack and run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/demo_flow.ps1
```

The script creates local PDF/DOCX/HTML fixtures in `.demo/`, uploads them with
`X-Tenant-ID: tenant-demo`, runs search/chat, prints source metadata, and checks
tenant isolation against `tenant-other`.

If `API_AUTH_TOKEN` is configured:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/demo_flow.ps1 -ApiToken your-token
```

## Tenant Isolation Check

Search from `tenant-demo` for a file uploaded by `tenant-other`:

```powershell
$body = @{
  query = "other tenant quarterly revenue target"
  top_k = 3
  score_threshold = -1.0
  metadata_filters = @{
    source = "tenant-other-secret.txt"
  }
} | ConvertTo-Json -Depth 6

Invoke-RestMethod http://localhost:8000/search `
  -Method Post `
  -Body $body `
  -ContentType "application/json" `
  -Headers @{ "X-Tenant-ID" = "tenant-demo" }
```

Expected result: an empty `results` array. Use the same body with
`X-Tenant-ID: tenant-other` to confirm the owning tenant can retrieve it.
