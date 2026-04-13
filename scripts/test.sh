#!/bin/bash
set -e

echo "============================================"
echo "🤖 Starting Local AI Evaluation Robot suite"
echo "============================================"

# Ensure containers are up
docker-compose up -d

echo "⏳ Waiting 3 seconds for databases to be ready..."
sleep 3

echo "🧪 Running Pytest inside the risk_auditor_backend container..."
docker exec -it risk_auditor_backend bash -c "pytest tests/ -v -s --asyncio-mode=auto"

echo "============================================"
echo "✅ All tests passed! The CI pipeline will be green."
echo "============================================"
