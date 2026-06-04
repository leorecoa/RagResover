$ErrorActionPreference = "Stop"

Write-Host "Checking Python syntax..."
venv\Scripts\python.exe -m compileall -q app migrations tests main.py config.py ingestion_service.py storage_service.py

Write-Host "Checking FastAPI app import..."
venv\Scripts\python.exe -c "from app.core.app import create_app; create_app()"

Write-Host "Running backend tests..."
venv\Scripts\python.exe -m pytest tests

Write-Host "Checking Alembic offline migration SQL..."
$previousErrorActionPreference = $ErrorActionPreference
$ErrorActionPreference = "Continue"
venv\Scripts\alembic.exe upgrade head --sql > $null 2> $null
$alembicExitCode = $LASTEXITCODE
$ErrorActionPreference = $previousErrorActionPreference
if ($alembicExitCode -ne 0) {
    throw "Alembic offline migration SQL check failed with exit code $alembicExitCode."
}

Write-Host "Checking Alembic offline downgrade SQL..."
$previousErrorActionPreference = $ErrorActionPreference
$ErrorActionPreference = "Continue"
venv\Scripts\alembic.exe downgrade head:base --sql > $null 2> $null
$alembicDowngradeExitCode = $LASTEXITCODE
$ErrorActionPreference = $previousErrorActionPreference
if ($alembicDowngradeExitCode -ne 0) {
    throw "Alembic offline downgrade SQL check failed with exit code $alembicDowngradeExitCode."
}

Write-Host "Checking Python dependencies..."
venv\Scripts\pip.exe check

Write-Host "Checking frontend build and E2E tests..."
Push-Location frontend
try {
    npm.cmd run build
    npm.cmd run test:e2e
}
finally {
    Pop-Location
}

Write-Host "Checking PowerShell scripts..."
[void][scriptblock]::Create((Get-Content scripts\demo_flow.ps1 -Raw))

Write-Host "Checking Docker Compose config..."
$previousDockerConfig = $env:DOCKER_CONFIG
$localDockerConfig = Join-Path $PWD ".docker-check"
New-Item -ItemType Directory -Force -Path $localDockerConfig | Out-Null
try {
    $env:DOCKER_CONFIG = $localDockerConfig
    docker compose config | Out-Null
}
finally {
    $env:DOCKER_CONFIG = $previousDockerConfig
}

Write-Host "All checks passed."
