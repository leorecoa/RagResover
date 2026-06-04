# Local Demo Flow

This guide runs a complete RagResover demo without exposing `OPENAI_API_KEY`.
It uses the local-first Ollama configuration from `.env.example`, generates
sample PDF/DOCX/HTML files locally, indexes them, runs search/chat, shows retrieval
diagnostics, and validates tenant isolation.

## Prerequisites

- Docker Desktop running.
- Ollama running on the host machine.
- Python dependencies installed in `venv`.
- Local models downloaded:

```powershell
ollama pull llama3.2:3b
ollama pull nomic-embed-text
```

## Environment

Create `.env` from the template if it does not exist:

```powershell
Copy-Item .env.example .env
```

For a private local demo, keep the relevant settings like this:

```dotenv
DEBUG=true
OPENAI_API_KEY=
LLM_PROVIDER=ollama
EMBEDDING_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
LLM_MODEL=llama3.2:3b
EMBEDDING_MODEL=nomic-embed-text
EMBEDDING_DIMENSIONS=768
ALLOW_ANONYMOUS_ACCESS=true
API_AUTH_TOKEN=
```

If you set `API_AUTH_TOKEN=demo-token`, pass the same token to the demo script
with `-ApiToken demo-token`.

## Start The Stack

In the project root:

```powershell
docker compose up --build
```

Wait until the backend is available at:

```text
http://localhost:8000/docs
```

Docker Compose also starts the Redis-backed ingestion worker. If you run the API
outside Compose, either start `python -m app.workers.ingestion_worker` or set
`INGESTION_QUEUE_PROVIDER=inline` for a simple local shell.

Optional frontend:

```powershell
cd frontend
npm run dev
```

Open:

```text
http://localhost:3000
```

## Run The Automated Demo

In another terminal, from the project root:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/demo_flow.ps1
```

With token authentication:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/demo_flow.ps1 -ApiToken demo-token
```

The script creates these local demo artifacts under `.demo/`:

- `ragresover-demo.pdf`
- `ragresover-demo.docx`
- `ragresover-demo.html`
- `tenant-other-secret.txt`

Then it performs:

- `GET /health`
- `GET /ready`
- `POST /upload` for PDF with `X-Tenant-ID: tenant-demo`
- `GET /uploads/{job_id}` until the PDF job is `completed`
- `POST /upload` for DOCX with `X-Tenant-ID: tenant-demo`
- `GET /uploads/{job_id}` until the DOCX job is `completed`
- `POST /upload` for HTML with `X-Tenant-ID: tenant-demo`
- `GET /uploads/{job_id}` until the HTML job is `completed`
- `POST /search` with `metadata_filters.source = ragresover-demo.pdf`
- `POST /search` with `metadata_filters.source = ragresover-demo.html`
- `POST /chat` with source metadata enabled
- tenant isolation check by uploading a private file to `tenant-other`
- negative search from `tenant-demo` for the other tenant file
- positive search from `tenant-other` for its own file

## Expected Evidence

When `DEBUG=true`, search and chat responses include a `diagnostics` object with
values similar to:

```json
{
  "tenant_id": "tenant-demo",
  "requested_top_k": 5,
  "fetch_limit": 20,
  "returned_count": 1,
  "score_threshold": -1.0,
  "metadata_filters": {
    "source": "ragresover-demo.pdf"
  },
  "embedding_provider": "ollama",
  "reranker_provider": "none",
  "reranker_applied": false
}
```

Search results and chat sources should also include metadata such as:

```json
{
  "source": "ragresover-demo.pdf",
  "content_type": "application/pdf",
  "page": 1,
  "page_count": 1
}
```

The tenant isolation check should return zero results for `tenant-demo` when it
searches for `tenant-other-secret.txt`, then at least one result for
`tenant-other`.

## Manual API Examples

Upload PDF:

```powershell
curl.exe -X POST http://localhost:8000/upload `
  -H "X-Tenant-ID: tenant-demo" `
  -F "file=@.demo/ragresover-demo.pdf;type=application/pdf"
```

The response returns a `job_id`. Poll it until `status` is `completed`:

```powershell
Invoke-RestMethod http://localhost:8000/uploads/<job_id> `
  -Headers @{ "X-Tenant-ID" = "tenant-demo" }
```

Upload DOCX:

```powershell
curl.exe -X POST http://localhost:8000/upload `
  -H "X-Tenant-ID: tenant-demo" `
  -F "file=@.demo/ragresover-demo.docx;type=application/vnd.openxmlformats-officedocument.wordprocessingml.document"
```

Upload HTML:

```powershell
curl.exe -X POST http://localhost:8000/upload `
  -H "X-Tenant-ID: tenant-demo" `
  -F "file=@.demo/ragresover-demo.html;type=text/html"
```

Search with diagnostics:

```powershell
$body = @{
  query = "What retention window is described for tenant alpha?"
  top_k = 5
  score_threshold = -1.0
  metadata_filters = @{
    source = "ragresover-demo.pdf"
  }
} | ConvertTo-Json -Depth 6

Invoke-RestMethod http://localhost:8000/search `
  -Method Post `
  -Body $body `
  -ContentType "application/json" `
  -Headers @{ "X-Tenant-ID" = "tenant-demo" }
```

Chat with sources:

```powershell
$body = @{
  question = "What is the retention window in the demo document?"
  top_k = 5
  score_threshold = -1.0
  metadata_filters = @{
    source = "ragresover-demo.pdf"
  }
} | ConvertTo-Json -Depth 6

Invoke-RestMethod http://localhost:8000/chat `
  -Method Post `
  -Body $body `
  -ContentType "application/json" `
  -Headers @{ "X-Tenant-ID" = "tenant-demo" }
```

Tenant isolation check:

```powershell
$body = @{
  query = "other tenant quarterly revenue"
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

The response should contain no results. Use `X-Tenant-ID: tenant-other` with the
same body to confirm that the owning tenant can retrieve its own file.
