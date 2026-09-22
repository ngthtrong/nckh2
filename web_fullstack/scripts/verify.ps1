$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path

$runFrontend = Get-Content (Join-Path $PSScriptRoot "run_frontend.ps1") -Raw
if ($runFrontend -notmatch 'fe\\app') {
    throw "run_frontend.ps1 does not target the shared fe/app package."
}

& (Join-Path $PSScriptRoot "test_backend.ps1")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& (Join-Path $PSScriptRoot "export_web_model.ps1")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& (Join-Path $PSScriptRoot "prepare_frontend_runtime.ps1")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Push-Location (Join-Path $root "fe\app")
try {
    flutter test
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    flutter analyze
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    flutter build apk --debug
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    flutter build web --release --dart-define=API_BASE_URL=http://127.0.0.1:8000
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    @(
        "build\app\outputs\flutter-apk\app-debug.apk",
        "build\web\main.dart.js",
        "build\web\models\model.onnx",
        "build\web\models\model_manifest.json",
        "build\web\onnx_bridge.js",
        "build\web\vendor\ort\ort.all.min.js",
        "build\web\vendor\ort\ort-wasm-simd-threaded.wasm"
    ) | ForEach-Object {
        if (-not (Test-Path -LiteralPath $_)) { throw "Missing release artifact: $_" }
    }
}
finally { Pop-Location }

Write-Host "Verification complete: backend, model, shared Flutter tests, analyze, APK and web release build passed."

