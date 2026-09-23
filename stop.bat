@echo off
setlocal enabledelayedexpansion

echo ======================================================================
echo                 FinVerify - Full Stack Shutdown Script
echo ======================================================================
echo.

cd /d "%~dp0"

echo [*] Stopping and tearing down all FinVerify Docker containers...
docker compose down

if %ERRORLEVEL% NEQ 0 (
    echo [!] Warning: Some containers might not have stopped cleanly.
) else (
    echo [+] All FinVerify services have been successfully stopped.
)

echo.
pause
