$ErrorActionPreference = "Stop"
$frontendDir = (Resolve-Path (Join-Path $PSScriptRoot "..\frontend")).Path
Push-Location $frontendDir
try {
    npm install
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    $source = Join-Path $frontendDir "node_modules\onnxruntime-web\dist"
    $target = Join-Path $frontendDir "web\vendor\ort"
    New-Item -ItemType Directory -Force -Path $target | Out-Null
    @(
        "ort.all.min.js",
        "ort-wasm-simd-threaded.mjs",
        "ort-wasm-simd-threaded.wasm",
        "ort-wasm-simd-threaded.jsep.mjs",
        "ort-wasm-simd-threaded.jsep.wasm"
    ) | ForEach-Object {
        Copy-Item -LiteralPath (Join-Path $source $_) -Destination (Join-Path $target $_) -Force
    }
}
finally { Pop-Location }

