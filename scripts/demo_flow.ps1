[CmdletBinding()]
param(
    [string]$BaseUrl = "http://localhost:8000",
    [string]$TenantId = "tenant-demo",
    [string]$OtherTenantId = "tenant-other",
    [string]$ApiToken = "",
    [switch]$SkipChat
)

$ErrorActionPreference = "Stop"
$BaseUrl = $BaseUrl.TrimEnd("/")

function Write-Step {
    param([string]$Message)

    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Resolve-DemoPython {
    $repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
    $venvPython = Join-Path $repoRoot "venv\Scripts\python.exe"
    if (Test-Path $venvPython) {
        return $venvPython
    }

    return "python"
}

function New-DemoHeaders {
    param([string]$Tenant)

    $headers = @{
        "X-Tenant-ID" = $Tenant
    }

    if ($ApiToken.Trim()) {
        $headers["Authorization"] = "Bearer $ApiToken"
    }

    return $headers
}

function Invoke-JsonRequest {
    param(
        [ValidateSet("GET", "POST")]
        [string]$Method,
        [string]$Path,
        [hashtable]$Body = $null,
        [string]$Tenant = $TenantId
    )

    $uri = "$BaseUrl$Path"
    $headers = New-DemoHeaders -Tenant $Tenant

    if ($null -eq $Body) {
        return Invoke-RestMethod -Uri $uri -Method $Method -Headers $headers
    }

    $jsonBody = $Body | ConvertTo-Json -Depth 12
    return Invoke-RestMethod `
        -Uri $uri `
        -Method $Method `
        -Headers $headers `
        -Body $jsonBody `
        -ContentType "application/json"
}

function Invoke-DemoUpload {
    param(
        [string]$FilePath,
        [string]$ContentType,
        [string]$Tenant
    )

    $responseFile = New-TemporaryFile
    try {
        $curlArgs = @(
            "-sS",
            "-o",
            $responseFile.FullName,
            "-w",
            "%{http_code}",
            "-X",
            "POST",
            "$BaseUrl/upload",
            "-H",
            "X-Tenant-ID: $Tenant"
        )

        if ($ApiToken.Trim()) {
            $curlArgs += @("-H", "Authorization: Bearer $ApiToken")
        }

        $curlArgs += @("-F", "file=@$FilePath;type=$ContentType")

        $statusCodeText = & curl.exe @curlArgs
        $curlExitCode = $LASTEXITCODE
        $responseBody = Get-Content $responseFile.FullName -Raw

        if ($curlExitCode -ne 0) {
            throw "curl.exe failed with exit code $curlExitCode."
        }

        $statusCode = [int]$statusCodeText
        if ($statusCode -ge 400) {
            throw "Upload failed with HTTP ${statusCode}: $responseBody"
        }

        return $responseBody | ConvertFrom-Json
    }
    finally {
        Remove-Item -LiteralPath $responseFile.FullName -Force -ErrorAction SilentlyContinue
    }
}

function Wait-DemoUploadJob {
    param(
        [object]$Job,
        [string]$Tenant,
        [int]$TimeoutSeconds = 120
    )

    if (-not $Job.job_id) {
        return $Job
    }

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    do {
        $current = Invoke-JsonRequest `
            -Method "GET" `
            -Path "/uploads/$($Job.job_id)" `
            -Tenant $Tenant

        if ($current.status -eq "completed") {
            return $current
        }

        if ($current.status -eq "failed") {
            throw "Upload job $($Job.job_id) failed: $($current.error_message)"
        }

        Start-Sleep -Seconds 2
    } while ((Get-Date) -lt $deadline)

    throw "Upload job $($Job.job_id) did not finish within $TimeoutSeconds seconds."
}

function Show-DemoJson {
    param(
        [string]$Title,
        [object]$Value
    )

    Write-Host ""
    Write-Host $Title -ForegroundColor Yellow
    $Value | ConvertTo-Json -Depth 12
}

function Get-ResultCount {
    param([object]$Results)

    if ($null -eq $Results) {
        return 0
    }

    return @($Results).Count
}

function Assert-HasResults {
    param(
        [object]$Payload,
        [string]$Label
    )

    $count = Get-ResultCount -Results $Payload.results
    if ($count -lt 1) {
        throw "$Label returned no results."
    }
}

function Assert-HasSources {
    param(
        [object]$Payload,
        [string]$Label
    )

    $count = Get-ResultCount -Results $Payload.sources
    if ($count -lt 1) {
        throw "$Label returned no sources."
    }
}

function New-DemoFiles {
    $repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
    $demoDir = Join-Path $repoRoot ".demo"
    New-Item -ItemType Directory -Force -Path $demoDir | Out-Null

    $python = Resolve-DemoPython
    $env:DEMO_OUTPUT_DIR = $demoDir

    $generator = @'
import os
import pathlib

from docx import Document


def make_minimal_pdf(text: str) -> bytes:
    escaped_text = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    objects = [
        "1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n",
        "2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n",
        (
            "3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            "/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj\n"
        ),
        "4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n",
    ]
    stream = f"BT /F1 16 Tf 72 720 Td ({escaped_text}) Tj ET"
    objects.append(
        f"5 0 obj << /Length {len(stream.encode('utf-8'))} >> stream\n"
        f"{stream}\n"
        "endstream endobj\n"
    )

    pdf = "%PDF-1.4\n"
    offsets = [0]
    for item in objects:
        offsets.append(len(pdf.encode("utf-8")))
        pdf += item

    xref_offset = len(pdf.encode("utf-8"))
    pdf += f"xref\n0 {len(objects) + 1}\n"
    pdf += "0000000000 65535 f \n"
    for offset in offsets[1:]:
        pdf += f"{offset:010d} 00000 n \n"
    pdf += (
        "trailer << /Size 6 /Root 1 0 R >>\n"
        f"startxref\n{xref_offset}\n"
        "%%EOF\n"
    )
    return pdf.encode("utf-8")


out = pathlib.Path(os.environ["DEMO_OUTPUT_DIR"])
out.mkdir(parents=True, exist_ok=True)

pdf_text = (
    "RagResover demo tenant alpha validates PDF upload source metadata "
    "retrieval diagnostics and tenant isolation. Retention window is 180 days."
)
(out / "ragresover-demo.pdf").write_bytes(make_minimal_pdf(pdf_text))

doc = Document()
doc.add_heading("RagResover Demo Playbook", level=1)
doc.add_paragraph(
    "The DOCX sample proves section metadata extraction for tenant alpha. "
    "The escalation channel is support operations and the owner is Alice."
)
doc.add_paragraph(
    "Search and chat should cite this DOCX file when metadata source filters "
    "target ragresover-demo.docx."
)
doc.save(out / "ragresover-demo.docx")

(out / "ragresover-demo.html").write_text(
    """<!doctype html>
<html>
  <head><title>RagResover HTML Demo</title></head>
  <body>
    <h1>HTML Knowledge Base</h1>
    <p>The HTML sample validates title and section metadata extraction.</p>
    <p>The escalation window for HTML content is 48 hours.</p>
  </body>
</html>
""",
    encoding="utf-8",
)

(out / "tenant-other-secret.txt").write_text(
    "Other tenant private note. Quarterly revenue target is isolated from tenant demo.",
    encoding="utf-8",
)
'@

    $generator | & $python -
    if ($LASTEXITCODE -ne 0) {
        throw "Could not generate local demo files. Confirm Python dependencies are installed in venv."
    }

    return @{
        Pdf = Join-Path $demoDir "ragresover-demo.pdf"
        Docx = Join-Path $demoDir "ragresover-demo.docx"
        Html = Join-Path $demoDir "ragresover-demo.html"
        OtherTenantText = Join-Path $demoDir "tenant-other-secret.txt"
    }
}

Write-Step "Generating local PDF, DOCX, HTML, and tenant isolation fixtures"
$files = New-DemoFiles
Show-DemoJson -Title "Generated files" -Value $files

Write-Step "Checking API health"
try {
    $health = Invoke-JsonRequest -Method "GET" -Path "/health"
    Show-DemoJson -Title "Health response" -Value $health
}
catch {
    throw "Backend is not reachable at $BaseUrl. Start it with: docker compose up --build. Original error: $_"
}

Write-Step "Checking dependency readiness"
try {
    $ready = Invoke-JsonRequest -Method "GET" -Path "/ready"
    Show-DemoJson -Title "Readiness response" -Value $ready
}
catch {
    throw "Readiness failed. Confirm Postgres, MinIO, and migrations are healthy in docker compose. Original error: $_"
}

Write-Step "Uploading PDF for $TenantId"
$pdfUpload = Invoke-DemoUpload `
    -FilePath $files.Pdf `
    -ContentType "application/pdf" `
    -Tenant $TenantId
Show-DemoJson -Title "PDF upload response" -Value $pdfUpload
$pdfUpload = Wait-DemoUploadJob -Job $pdfUpload -Tenant $TenantId
Show-DemoJson -Title "PDF upload job completed" -Value $pdfUpload

Write-Step "Uploading DOCX for $TenantId"
$docxUpload = Invoke-DemoUpload `
    -FilePath $files.Docx `
    -ContentType "application/vnd.openxmlformats-officedocument.wordprocessingml.document" `
    -Tenant $TenantId
Show-DemoJson -Title "DOCX upload response" -Value $docxUpload
$docxUpload = Wait-DemoUploadJob -Job $docxUpload -Tenant $TenantId
Show-DemoJson -Title "DOCX upload job completed" -Value $docxUpload

Write-Step "Uploading HTML for $TenantId"
$htmlUpload = Invoke-DemoUpload `
    -FilePath $files.Html `
    -ContentType "text/html" `
    -Tenant $TenantId
Show-DemoJson -Title "HTML upload response" -Value $htmlUpload
$htmlUpload = Wait-DemoUploadJob -Job $htmlUpload -Tenant $TenantId
Show-DemoJson -Title "HTML upload job completed" -Value $htmlUpload

Write-Step "Searching indexed PDF with metadata filter and diagnostics"
$pdfSearch = Invoke-JsonRequest `
    -Method "POST" `
    -Path "/search" `
    -Tenant $TenantId `
    -Body @{
        query = "What retention window is described for tenant alpha?"
        top_k = 5
        score_threshold = -1.0
        metadata_filters = @{
            source = "ragresover-demo.pdf"
        }
    }
Assert-HasResults -Payload $pdfSearch -Label "PDF search"
Show-DemoJson -Title "PDF search response" -Value $pdfSearch

Write-Step "Searching indexed DOCX with metadata filter"
$docxSearch = Invoke-JsonRequest `
    -Method "POST" `
    -Path "/search" `
    -Tenant $TenantId `
    -Body @{
        query = "Who owns the escalation channel in the demo playbook?"
        top_k = 5
        score_threshold = -1.0
        metadata_filters = @{
            source = "ragresover-demo.docx"
        }
    }
Assert-HasResults -Payload $docxSearch -Label "DOCX search"
Show-DemoJson -Title "DOCX search response" -Value $docxSearch

Write-Step "Searching indexed HTML with metadata filter"
$htmlSearch = Invoke-JsonRequest `
    -Method "POST" `
    -Path "/search" `
    -Tenant $TenantId `
    -Body @{
        query = "What is the escalation window for HTML content?"
        top_k = 5
        score_threshold = -1.0
        metadata_filters = @{
            source = "ragresover-demo.html"
        }
    }
Assert-HasResults -Payload $htmlSearch -Label "HTML search"
Show-DemoJson -Title "HTML search response" -Value $htmlSearch

if (-not $SkipChat) {
    Write-Step "Asking chat over the indexed PDF"
    $chat = Invoke-JsonRequest `
        -Method "POST" `
        -Path "/chat" `
        -Tenant $TenantId `
        -Body @{
            question = "What is the retention window in the demo document?"
            top_k = 5
            score_threshold = -1.0
            metadata_filters = @{
                source = "ragresover-demo.pdf"
            }
        }
    Assert-HasSources -Payload $chat -Label "Chat"
    Show-DemoJson -Title "Chat response" -Value $chat
}

Write-Step "Uploading a private document for $OtherTenantId"
$otherUpload = Invoke-DemoUpload `
    -FilePath $files.OtherTenantText `
    -ContentType "text/plain" `
    -Tenant $OtherTenantId
Show-DemoJson -Title "Other tenant upload response" -Value $otherUpload
$otherUpload = Wait-DemoUploadJob -Job $otherUpload -Tenant $OtherTenantId
Show-DemoJson -Title "Other tenant upload job completed" -Value $otherUpload

Write-Step "Verifying $TenantId cannot retrieve $OtherTenantId data"
$isolationMiss = Invoke-JsonRequest `
    -Method "POST" `
    -Path "/search" `
    -Tenant $TenantId `
    -Body @{
        query = "other tenant quarterly revenue target"
        top_k = 3
        score_threshold = -1.0
        metadata_filters = @{
            source = "tenant-other-secret.txt"
        }
    }
$missCount = Get-ResultCount -Results $isolationMiss.results
if ($missCount -ne 0) {
    throw "Tenant isolation failed. $TenantId retrieved $missCount result(s) from $OtherTenantId."
}
Show-DemoJson -Title "Cross-tenant search response" -Value $isolationMiss

Write-Step "Verifying $OtherTenantId can retrieve its own data"
$isolationHit = Invoke-JsonRequest `
    -Method "POST" `
    -Path "/search" `
    -Tenant $OtherTenantId `
    -Body @{
        query = "other tenant quarterly revenue target"
        top_k = 3
        score_threshold = -1.0
        metadata_filters = @{
            source = "tenant-other-secret.txt"
        }
    }
Assert-HasResults -Payload $isolationHit -Label "Owning tenant search"
Show-DemoJson -Title "Owning tenant search response" -Value $isolationHit

Write-Host ""
Write-Host "Demo flow completed successfully." -ForegroundColor Green
