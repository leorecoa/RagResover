$ErrorActionPreference = "Stop"

Write-Host "Checking Python syntax..."
venv\Scripts\python.exe -m compileall -q app main.py config.py ingestion_service.py storage_service.py

Write-Host "Checking FastAPI app import..."
venv\Scripts\python.exe -c "from app.core.app import create_app; create_app()"

Write-Host "Running backend tests..."
venv\Scripts\python.exe -m unittest discover -s tests

Write-Host "Checking Python dependencies..."
venv\Scripts\pip.exe check

Write-Host "Checking frontend JavaScript..."
node --check frontend\app.js
node --check frontend\server.js

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
