#!/bin/bash

# Auto-detect docker compose command
if command -v docker-compose &> /dev/null; then
    # docker-compose (standalone) is available
    COMPOSER="docker-compose"
elif command -v docker &> /dev/null && docker compose version &> /dev/null; then
    # docker compose (plugin) is available
    COMPOSER="docker compose"
else
    echo "❌ Neither 'docker-compose' nor 'docker compose' command found. Aborting deployment."
    exit 1
fi

# Set default branch to 'dev' if no argument is provided
BRANCH=${1:-dev}

echo "🚀 Deploying branch: $BRANCH"

# Navigate to the repo
cd ~/LGS-Stock-Checker || exit 1

# Fetch latest updates from the remote repository
echo "📡 Fetching latest updates from origin..."
git fetch origin

# Switch to the target branch and reset it to match the remote version exactly.
# This discards any local changes, ensuring a clean deployment state.
echo "🔄 Checking out and resetting branch '$BRANCH'..."
git checkout "$BRANCH"
git reset --hard "origin/$BRANCH"

# Build the new image first to ensure all dependencies are included.
echo "🏗️ Building Docker images..."
if ! $COMPOSER build; then
    echo "❌ Docker build failed. Aborting deployment."
    exit 1
fi

# Run tests against the newly built image.
echo "🧪 Running tests..."
# Run tests inside a temporary 'backend' service container to ensure environment consistency.
# The '--rm' flag removes the container after the test run.
if ! $COMPOSER run --rm backend pytest -m "not smoke"; then
    echo "❌ Tests failed. Aborting deployment."
    exit 1
fi

# If tests pass, bring up the services with the new image.
echo "🚀 Starting services..."
$COMPOSER up -d

echo "✅ Deployment of '$BRANCH' completed!"