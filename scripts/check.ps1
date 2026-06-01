$ErrorActionPreference = "Stop"

Write-Host "Checking Python syntax..."
venv\Scripts\python.exe -m compileall -q app main.py config.py ingestion_service.py storage_service.py

Write-Host "Checking FastAPI app import..."
venv\Scripts\python.exe -c "from app.core.app import create_app; create_app()"

Write-Host "Checking Python dependencies..."
venv\Scripts\pip.exe check

Write-Host "Checking frontend JavaScript..."
node --check frontend\app.js
node --check frontend\server.js

Write-Host "Checking Docker Compose config..."
docker compose config | Out-Null

Write-Host "All checks passed."
