#!/usr/bin/env bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "======================================================================"
echo "                FinVerify - Full Stack Startup Script"
echo "======================================================================"
echo ""

if [ ! -f ".env" ]; then
    echo "[*] .env not found. Creating from .env.example..."
    cp .env.example .env
    echo "[+] .env created successfully."
else
    echo "[+] Found existing .env file."
fi

echo "[*] Checking Docker daemon status..."
if ! docker info >/dev/null 2>&1; then
    echo "[!] ERROR: Docker daemon is not running or docker command is not found."
    exit 1
fi
echo "[+] Docker daemon is running."

echo "[*] Building and starting all Docker services..."
docker compose up --build -d

echo ""
echo "======================================================================"
echo "                FinVerify is Running!"
echo "======================================================================"
echo ""
echo "  [*] Frontend Dashboard:       http://localhost:3000"
echo "  [*] FastAPI Swagger Docs:     http://localhost:8000/docs"
echo "  [*] FastAPI Health Check:     http://localhost:8000/health"
echo "  [*] Temporal Orchestrator UI: http://localhost:8233"
echo ""
echo "  To view live logs:           docker compose logs -f"
echo "  To stop all services:        ./stop.sh"
echo "======================================================================"
echo ""
