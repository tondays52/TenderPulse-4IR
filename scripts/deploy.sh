#!/usr/bin/env bash
# ==============================================================================
# TenderPulse 4IR - Automated Production Deployment Script (Linux / Cloud VPS)
# ==============================================================================

set -e

echo -e "\033[0;36m==========================================================\033[0m"
echo -e "\033[0;36m  TenderPulse 4IR - Production Container Deployment       \033[0m"
echo -e "\033[0;36m==========================================================\033[0m"

# Handle CLI arguments
if [ "$1" == "down" ]; then
    echo -e "\033[0;33m[*] Stopping containers...\033[0m"
    docker-compose down
    echo -e "\033[0;32m[+] Stopped.\033[0m"
    exit 0
fi

if [ "$1" == "logs" ]; then
    docker-compose logs -f
    exit 0
fi

# Ensure .env exists
if [ ! -f .env ]; then
    echo -e "\033[0;33m[!] .env not found, generating from .env.example...\033[0m"
    cp .env.example .env
fi

# Ensure data directory exists
mkdir -p data

echo -e "\033[0;33m[*] Building production images...\033[0m"
docker-compose build

if [ "$1" == "build" ]; then
    echo -e "\033[0;32m[+] Build complete.\033[0m"
    exit 0
fi

echo -e "\033[0;33m[*] Starting stack (App + Nginx + Redis)...\033[0m"
docker-compose up -d

echo -e "\033[0;33m[*] Polling application healthcheck...\033[0m"
sleep 5

HEALTH=$(curl -s http://127.0.0.1:8080/api/health || true)
if echo "$HEALTH" | grep -q "ONLINE"; then
    echo -e "\033[0;32m[+] Deployment SUCCESSFUL! Service is ONLINE on http://127.0.0.1:8080/\033[0m"
else
    echo -e "\033[0;31m[!] Healthcheck not responding. Inspect container logs via: docker-compose logs\033[0m"
fi
