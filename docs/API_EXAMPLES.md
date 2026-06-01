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
  "document_id": "67a96a52-3b77-4efa-b6eb-e065ca66c4f4",
  "filename": "README.md",
  "status": "success",
  "chunks_count": 7,
  "message": "Documento processado e pronto para indexacao."
}
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
