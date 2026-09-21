$ErrorActionPreference = "Stop"

$toolsDir = (Resolve-Path (Join-Path $PSScriptRoot "..\model_tools")).Path
$venvPython = Join-Path $toolsDir ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $venvPython)) {
    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($null -eq $python) {
        throw "Python 3.11+ was not found. Install Python, then run this script again."
    }
    & $python.Source -m venv (Join-Path $toolsDir ".venv")
}

Push-Location $toolsDir
try {
    & $venvPython -m pip install -e ".[dev]"
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & $venvPython -m pytest -q
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & $venvPython export_model.py
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
