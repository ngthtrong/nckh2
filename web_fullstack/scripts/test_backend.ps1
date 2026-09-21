$ErrorActionPreference = "Stop"

$backendDir = (Resolve-Path (Join-Path $PSScriptRoot "..\backend")).Path
$venvPython = Join-Path $backendDir ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $venvPython)) {
    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($null -eq $python) {
        throw "Python 3.11+ was not found. Install Python, then run this script again."
    }
    & $python.Source -m venv (Join-Path $backendDir ".venv")
}

Push-Location $backendDir
try {
    & $venvPython -m pip install -e ".[dev]"
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & $venvPython -m pytest -v
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}

