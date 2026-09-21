$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path

& (Join-Path $PSScriptRoot "test_backend.ps1")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& (Join-Path $PSScriptRoot "export_web_model.ps1")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& (Join-Path $PSScriptRoot "prepare_frontend_runtime.ps1")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Push-Location (Join-Path $root "web_fullstack\frontend")
try {
    flutter test
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    flutter analyze
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    flutter build web --release --dart-define=API_BASE_URL=http://127.0.0.1:8000
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    @(
        "build\web\models\flood_mobilenetv3_large.onnx",
        "build\web\models\model_manifest.json",
        "build\web\onnx_bridge.js",
        "build\web\vendor\ort\ort.all.min.js",
        "build\web\vendor\ort\ort-wasm-simd-threaded.wasm"
    ) | ForEach-Object {
        if (-not (Test-Path -LiteralPath $_)) { throw "Missing release artifact: $_" }
    }
}
finally { Pop-Location }

Push-Location $root
try {
    git diff --exit-code -- fe/app
    if ($LASTEXITCODE -ne 0) { throw "Android source changed inside the isolated worktree." }
}
finally { Pop-Location }

Write-Host "Verification complete: backend, model, Flutter tests, analyze and release build passed."

