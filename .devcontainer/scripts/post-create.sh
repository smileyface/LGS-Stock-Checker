#!/bin/bash
set -e

echo "Installing Backend Requirements..."
if [ -f "backend/requirements-dev.txt" ]; then
    pip install -r backend/requirements-dev.txt
fi

echo "Installing Frontend Dependencies..."
if [ -d "frontend" ]; then
    cd frontend && npm install
fi

# Make the tunnel script executable automatically
chmod +x .devcontainer/scripts/start-tunnel.sh

echo "Setup Complete!"