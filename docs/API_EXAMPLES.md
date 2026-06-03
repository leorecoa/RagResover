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
  "document_id": null,
  "created_at": "2026-06-03T12:00:00",
  "updated_at": "2026-06-03T12:00:00",
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
  "document_id": "67a96a52-3b77-4efa-b6eb-e065ca66c4f4",
  "created_at": "2026-06-03T12:00:00",
  "updated_at": "2026-06-03T12:00:04",
  "message": "Upload recebido para processamento."
}
```

List recent upload jobs for the tenant:

```powershell
Invoke-RestMethod "http://localhost:8000/uploads?limit=20" `
  -Headers @{ "X-Tenant-ID" = "tenant-demo" }
```

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

## Demo Flow

For an end-to-end product demo, start the stack and run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/demo_flow.ps1
```

The script creates local PDF/DOCX fixtures in `.demo/`, uploads them with
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
