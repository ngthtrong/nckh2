@echo off
title Flood Rescue Mock Server (Port 8000)
cd /d "%~dp0"

echo =================================================
echo    KHOI DONG FLOOD RESCUE MOCK SERVER (:8000)   
echo =================================================

if not exist ".venv\Scripts\python.exe" (
    echo Dang tao moi truong ao .venv...
    py -3.11 -m venv .venv
)

echo Dang dong bo dependencies...
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 (
    echo [LOI] Khong the cai dependencies. Kiem tra lai Python va ket noi mang.
    pause
    exit /b 1
)

echo Dang chay server tai http://0.0.0.0:8000...
echo Dashboard: http://localhost:8000/
echo Swagger Docs: http://localhost:8000/docs
echo Nhan Ctrl + C de dung server.
echo.

.venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000
pause
