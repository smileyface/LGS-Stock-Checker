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
BRANCH=${1:-master}

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

# Build the new images first to ensure all dependencies are included.
echo "🏗️ Building Docker images..."
if ! $COMPOSER build; then
    echo "❌ Docker build failed. Aborting deployment."
    exit 1
fi

# --- Conditional Test Execution ---
# Only run tests for the 'master' branch, which is considered a release deployment.
if [ "$BRANCH" = "master" ]; then
    echo "🔬 This is a release deployment to 'master'. Running tests..."
    # Install test dependencies and run tests against the newly built image.
    # The '--rm' flag removes the container after the test run.
    if ! $COMPOSER run --rm backend sh -c "pip install -r LGS_Stock_Backend/requirements-dev.txt && pytest -m 'not smoke'"; then
        echo "❌ Tests failed. Aborting release deployment."
        exit 1
    fi
else
    echo "⏩ This is a test deployment to '$BRANCH'. Skipping tests."
fi

# If we reach here, either tests passed or were skipped.
# First, tear down any existing services to free up ports and ensure a clean start.
echo "🛑 Stopping and removing old containers..."
$COMPOSER down --remove-orphans

# --- Aggressive Cleanup for Stubborn Port Conflicts ---
# The "port is already allocated" error, even when 'lsof' shows the port is free,
# suggests Docker's internal networking state might be corrupt. Restarting the Docker
# daemon is the most reliable way to clear this "ghost" allocation.
# WARNING: This will temporarily stop ALL Docker containers on this machine.
echo "⚠️ Performing aggressive cleanup to prevent port conflicts: Restarting Docker daemon..."
sudo systemctl restart docker
# Wait for the daemon to be fully ready again.
echo "⏳ Waiting for Docker daemon to restart..."
sleep 5

# Now, bring up the new services in detached mode.
echo "🚀 Starting services..."
$COMPOSER up -d

# Clean up old, unused Docker images to save disk space.
echo "🧹 Cleaning up old Docker images..."
docker image prune -af

echo "✅ Deployment of '$BRANCH' completed!"