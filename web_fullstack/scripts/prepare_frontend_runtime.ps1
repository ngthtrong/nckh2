$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$appDir = (Resolve-Path (Join-Path $root "fe\app")).Path
$runtimeDir = (Resolve-Path (Join-Path $appDir "web_runtime")).Path
Push-Location $runtimeDir
try {
    npm ci
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    $source = Join-Path $runtimeDir "node_modules\onnxruntime-web\dist"
    $target = Join-Path $appDir "web\vendor\ort"
    New-Item -ItemType Directory -Force -Path $target | Out-Null
    @(
        "ort.all.min.js",
        "ort-wasm-simd-threaded.mjs",
        "ort-wasm-simd-threaded.wasm",
        "ort-wasm-simd-threaded.jsep.mjs",
        "ort-wasm-simd-threaded.jsep.wasm"
    ) | ForEach-Object {
        $sourceFile = Join-Path $source $_
        $targetFile = Join-Path $target $_
        $needsCopy = -not (Test-Path -LiteralPath $targetFile)
        if (-not $needsCopy) {
            $needsCopy = (Get-FileHash -LiteralPath $sourceFile).Hash -ne `
                (Get-FileHash -LiteralPath $targetFile).Hash
        }
        if ($needsCopy) {
            Copy-Item -LiteralPath $sourceFile -Destination $targetFile -Force
        }
    }
}
finally { Pop-Location }

