$ErrorActionPreference = "Stop"

$backendDir = (Resolve-Path (Join-Path $PSScriptRoot "..\backend")).Path
$venvPython = Join-Path $backendDir ".venv\Scripts\python.exe"
$envFile = Join-Path $backendDir ".env"
$envExample = Join-Path $backendDir ".env.example"

if (-not (Test-Path -LiteralPath $venvPython)) {
    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($null -eq $python) {
        throw "Python 3.11+ was not found. Install Python, then run this script again."
    }
    & $python.Source -m venv (Join-Path $backendDir ".venv")
}

if (-not (Test-Path -LiteralPath $envFile)) {
    Copy-Item -LiteralPath $envExample -Destination $envFile
    Write-Host "Created backend/.env from .env.example. SMS remains disabled."
}

Push-Location $backendDir
try {
    & $venvPython -m pip install -e "."
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & $venvPython -m uvicorn app.main:app --host 127.0.0.1 --port 8000
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}

