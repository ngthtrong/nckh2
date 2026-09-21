$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path

Push-Location $root
try {
    $androidDiffBefore = (git diff --binary -- fe/app | Out-String)
    $androidStatusBefore = (git status --porcelain=v1 --untracked-files=all -- fe/app | Out-String)
}
finally { Pop-Location }

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
    $androidDiffAfter = (git diff --binary -- fe/app | Out-String)
    $androidStatusAfter = (git status --porcelain=v1 --untracked-files=all -- fe/app | Out-String)
    if ($androidDiffAfter -ne $androidDiffBefore -or $androidStatusAfter -ne $androidStatusBefore) {
        throw "Android source changed while the web verification was running."
    }
}
finally { Pop-Location }

Write-Host "Verification complete: backend, model, Flutter tests, analyze and release build passed."

