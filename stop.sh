#!/usr/bin/env bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "======================================================================"
echo "                FinVerify - Full Stack Shutdown Script"
echo "======================================================================"
echo ""

echo "[*] Stopping and tearing down all FinVerify Docker containers..."
docker compose down

echo "[+] All FinVerify services have been successfully stopped."
echo ""
