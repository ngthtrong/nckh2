@echo off
title Flood Rescue Mock Server (Port 8000)
cd /d "%~dp0"

echo =================================================
echo    KHOI DONG FLOOD RESCUE MOCK SERVER (:8000)   
echo =================================================

if not exist ".venv\Scripts\python.exe" (
    echo Dang tao moi truong ao .venv...
    py -3.11 -m venv .venv
    .venv\Scripts\python.exe -m pip install -r requirements.txt
)

echo Dang chay server tai http://0.0.0.0:8000...
echo Dashboard: http://localhost:8000/
echo Swagger Docs: http://localhost:8000/docs
echo Nhan Ctrl + C de dung server.
echo.

.venv\Scripts\python.exe main.py
pause
