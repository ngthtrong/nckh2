$ErrorActionPreference = "Stop"
& (Join-Path $PSScriptRoot "prepare_frontend_runtime.ps1")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
$root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$appDir = (Resolve-Path (Join-Path $root "fe\app")).Path
Push-Location $appDir
try {
    flutter run -d web-server --web-hostname 127.0.0.1 --web-port 8080 `
        --dart-define=API_BASE_URL=http://127.0.0.1:8000
    exit $LASTEXITCODE
}
finally { Pop-Location }

