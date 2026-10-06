# Script khởi chạy Mock Server trên PowerShell
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host "   KHỞI ĐỘNG FLOOD RESCUE MOCK SERVER (:8000)   " -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

$venvPython = Join-Path $scriptDir ".venv\Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    Write-Host "Đang tạo môi trường ảo .venv..." -ForegroundColor Yellow
    if (Get-Command py -ErrorAction SilentlyContinue) { py -3.11 -m venv .venv } else { python -m venv .venv }
}

Write-Host "Đang đồng bộ dependencies..." -ForegroundColor Yellow
& $venvPython -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Error "Không thể cài dependencies. Kiểm tra lại Python và kết nối mạng."
    exit 1
}

Write-Host "Đang chạy server tại http://0.0.0.0:8000..." -ForegroundColor Green
Write-Host "Dashboard: http://localhost:8000/" -ForegroundColor Yellow
Write-Host "Swagger Docs: http://localhost:8000/docs" -ForegroundColor Yellow
Write-Host "Nhấn Ctrl + C để dừng server.`n" -ForegroundColor Gray

& $venvPython -m uvicorn main:app --host 0.0.0.0 --port 8000
