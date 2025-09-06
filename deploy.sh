#!/bin/bash

# Set default branch to 'dev' if no argument is provided
BRANCH=${1:-dev}

echo "🚀 Deploying branch: $BRANCH"

# Navigate to the repo
cd ~/LGS-Stock-Checker || exit 1

# Fetch latest updates
git fetch origin

# Check if the branch exists on remote
if git ls-remote --exit-code --heads origin "$BRANCH"; then
    git checkout "$BRANCH"
    git pull origin "$BRANCH"
else
    echo "❌ Branch '$BRANCH' not found on remote. Exiting..."
    exit 1
fi

# Run tests before deploying
echo "🧪 Running tests..."
# Run tests inside a temporary 'backend' service container to ensure environment consistency.
# The '--rm' flag removes the container after the test run.
if ! docker compose run --rm backend pytest; then
    echo "❌ Tests failed. Aborting deployment."
    exit 1
fi

# Rebuild and restart containers
docker compose up -d --build

echo "✅ Deployment of '$BRANCH' completed!"