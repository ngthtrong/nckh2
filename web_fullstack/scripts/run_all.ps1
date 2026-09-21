$ErrorActionPreference = "Stop"
$backendScript = (Resolve-Path (Join-Path $PSScriptRoot "run_backend.ps1")).Path
$backend = Start-Process powershell -WindowStyle Hidden -PassThru -ArgumentList @(
    "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $backendScript
)
try {
    $ready = $false
    for ($attempt = 0; $attempt -lt 60; $attempt++) {
        try {
            $health = Invoke-RestMethod "http://127.0.0.1:8000/health" -TimeoutSec 1
            if ($health.status -eq "ok") { $ready = $true; break }
        } catch { Start-Sleep -Milliseconds 500 }
    }
    if (-not $ready) { throw "Backend did not become ready at http://127.0.0.1:8000." }
    & (Join-Path $PSScriptRoot "run_frontend.ps1")
}
finally {
    if (-not $backend.HasExited) { Stop-Process -Id $backend.Id }
}

