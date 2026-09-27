# Khoi chay FastAPI mock server (be/) tren Windows PowerShell.
#
#   .\scripts\demo\run_server.ps1                  # du lieu mau da commit (be\data\rescue_reports.db)
#   .\scripts\demo\run_server.ps1 -Demo -Seed      # DB demo rieng + nap run_001 ban tong hop
#   .\scripts\demo\run_server.ps1 -Port 8001 -NoReload
#
# Neu bi chan script: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
param(
    [switch]$Demo,
    [switch]$Seed,
    [int]$Run = 1,
    [string]$BindHost = "0.0.0.0",
    [int]$Port = 8000,
    [switch]$NoReload
)
$ErrorActionPreference = "Stop"

$root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$be = Join-Path $root "be"
Set-Location $be

$py = Join-Path $be ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) {
    Write-Host ">> Tao moi truong ao be\.venv ..." -ForegroundColor Yellow
    if (Get-Command py -ErrorAction SilentlyContinue) { py -3 -m venv .venv } else { python -m venv .venv }
    if ($LASTEXITCODE -ne 0) { throw "Khong tao duoc venv (can Python >= 3.10)." }
}
$stamp = Join-Path $be ".venv\.requirements.stamp"
$req = Join-Path $be "requirements.txt"
if (-not (Test-Path $stamp) -or (Get-Item $req).LastWriteTime -gt (Get-Item $stamp).LastWriteTime) {
    Write-Host ">> Cai dependencies tu be\requirements.txt ..." -ForegroundColor Yellow
    & $py -m pip install -q --upgrade pip
    & $py -m pip install -q -r requirements.txt
    if ($LASTEXITCODE -ne 0) { throw "pip install that bai." }
    New-Item -ItemType File -Force $stamp | Out-Null
}

if ($Seed) { $Demo = $true }
if ($Demo) {
    $env:RESCUE_DB_FILE = "data/demo.db"
    $env:RESCUE_UPLOADS_DIR = "uploads_demo"
    Write-Host ">> Che do DEMO: DB=be\data\demo.db, anh=be\uploads_demo\" -ForegroundColor Cyan
} else {
    Remove-Item Env:RESCUE_DB_FILE, Env:RESCUE_UPLOADS_DIR -ErrorAction SilentlyContinue
}
if ($Seed) {
    Write-Host (">> Nap du lieu BAN TONG HOP run_{0:D3} (source=synthetic) ..." -f $Run) -ForegroundColor Cyan
    & $py seed_demo.py --run $Run --reset
    if ($LASTEXITCODE -ne 0) { throw "seed_demo.py that bai." }
}

$lanIp = (Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
    Where-Object { $_.IPAddress -notlike "127.*" -and $_.IPAddress -notlike "169.254.*" -and $_.PrefixOrigin -ne "WellKnown" } |
    Select-Object -First 1).IPAddress
Write-Host "================================================="
Write-Host " Flood Rescue Mock Server"
Write-Host "  Dashboard : http://localhost:$Port/"
Write-Host "  Swagger   : http://localhost:$Port/docs"
if ($lanIp) { Write-Host "  LAN       : http://${lanIp}:$Port  (dien thoai that; mo firewall cong $Port)" }
Write-Host "  Emulator  : http://10.0.2.2:$Port"
Write-Host " Nhan Ctrl+C de dung."
Write-Host "================================================="

$uvArgs = @("-m", "uvicorn", "main:app", "--host", $BindHost, "--port", "$Port")
if (-not $NoReload) { $uvArgs += "--reload" }
& $py @uvArgs
