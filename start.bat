@echo off
setlocal enabledelayedexpansion

echo ======================================================================
echo                 FinVerify - Full Stack Startup Script
echo ======================================================================
echo.

cd /d "%~dp0"

:: 1. Check if .env exists, copy from .env.example if missing
if not exist ".env" (
    echo [*] .env not found. Creating from .env.example...
    copy .env.example .env >nul
    echo [+] .env created successfully.
) else (
    echo [+] Found existing .env file.
)

:: 2. Check if Docker is installed and running
echo [*] Checking Docker daemon status...
docker info >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [!] ERROR: Docker daemon is not running or docker command is not found.
    echo     Please start Docker Desktop and try running start.bat again.
    pause
    exit /b 1
)
echo [+] Docker daemon is running.

:: 3. Build and launch all container services
echo [*] Building and starting all Docker services (PostgreSQL, Redis, Temporal, API, Workers, Frontend)...
docker compose up --build -d

if %ERRORLEVEL% NEQ 0 (
    echo [!] ERROR: Failed to start docker containers.
    pause
    exit /b 1
)

echo.
echo ======================================================================
echo                 FinVerify is Running!
echo ======================================================================
echo.
echo   [*] Frontend Dashboard:       http://localhost:3000
echo   [*] FastAPI Swagger Docs:     http://localhost:8000/docs
echo   [*] FastAPI Health Check:     http://localhost:8000/health
echo   [*] Temporal Orchestrator UI: http://localhost:8233
echo.
echo   To view live logs:           docker compose logs -f
echo   To stop all services:        run stop.bat
echo ======================================================================
echo.
pause
