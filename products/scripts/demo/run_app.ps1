# Chay Flutter app (fe\app) tro toi mock server tren Windows PowerShell.
#
#   .\scripts\demo\run_app.ps1 -Device windows
#   .\scripts\demo\run_app.ps1 -Device emulator-5554            # tu dung http://10.0.2.2:8000
#   .\scripts\demo\run_app.ps1 -Device <id> -ServerUrl http://192.168.1.20:8000   # dien thoai that
#
# Server URL truyen qua --dart-define=SERVER_URL (xem fe\app\lib\config.dart), khong can sua code.
param(
    [string]$Device = "",
    [string]$ServerUrl = "",
    [int]$Port = 8000,
    [switch]$Release
)
$ErrorActionPreference = "Stop"

if (-not (Get-Command flutter -ErrorAction SilentlyContinue)) { throw "Khong tim thay flutter trong PATH." }

$root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$app = Join-Path $root "fe\app"

if (-not $ServerUrl) {
    if ($Device -like "emulator-*") {
        $ServerUrl = "http://10.0.2.2:$Port"
    } elseif ($Device -in @("", "windows", "chrome", "edge", "web-server")) {
        $ServerUrl = "http://localhost:$Port"
    } else {
        $lanIp = (Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
            Where-Object { $_.IPAddress -notlike "127.*" -and $_.IPAddress -notlike "169.254.*" -and $_.PrefixOrigin -ne "WellKnown" } |
            Select-Object -First 1).IPAddress
        if (-not $lanIp) { $lanIp = "localhost" }
        $ServerUrl = "http://${lanIp}:$Port"
        Write-Host "!! Thiet bi that: tu doan SERVER_URL=$ServerUrl - sai thi truyen -ServerUrl." -ForegroundColor Yellow
    }
}

$models = Join-Path $app "assets\models"
if (-not (Test-Path (Join-Path $models "model.onnx")) -or -not (Test-Path (Join-Path $models "model_manifest.json"))) {
    Write-Host "!! Chua co model trong fe\app\assets\models\ -> app chay duoc nhung AI on-device tat." -ForegroundColor Yellow
    Write-Host "   Xem docs\huong_dan_chay_demo.md muc 4." -ForegroundColor Yellow
}

Set-Location $app
flutter pub get
if ($LASTEXITCODE -ne 0) { throw "flutter pub get that bai." }

$fArgs = @("run", $(if ($Release) { "--release" } else { "--debug" }), "--dart-define=SERVER_URL=$ServerUrl")
if ($Device) { $fArgs += @("-d", $Device) }
Write-Host ">> flutter $($fArgs -join ' ')" -ForegroundColor Cyan
flutter @fArgs
