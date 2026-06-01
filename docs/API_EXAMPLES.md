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
  -F "file=@README.md;type=text/markdown"
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
} | ConvertTo-Json

Invoke-RestMethod http://localhost:8000/search `
  -Method Post `
  -Body $body `
  -ContentType "application/json"
```

## Chat

```powershell
$body = @{
  question = "Quais endpoints existem no projeto?"
  top_k = 3
} | ConvertTo-Json

Invoke-RestMethod http://localhost:8000/chat `
  -Method Post `
  -Body $body `
  -ContentType "application/json"
```
