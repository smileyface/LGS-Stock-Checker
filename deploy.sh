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

# --- Deployment Arguments ---
# Set default branch to 'master' if no first argument is provided.
BRANCH=${1:-master}
# Set default log level to 'INFO' if no second argument is provided.
LOG_LEVEL=${2:-INFO}
# Export LOG_LEVEL so docker-compose can access it.
export LOG_LEVEL

echo "🚀 Deploying branch: '$BRANCH' with log level: $LOG_LEVEL"

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
if ! $COMPOSER -f docker-compose.yml build; then
    echo "❌ Docker build failed. Aborting deployment."
    exit 1
fi

# --- Conditional Test Execution ---
# Only run tests for the 'master' branch, which is considered a release deployment.
if [ "$BRANCH" = "master" ]; then
    echo "🔬 This is a release deployment to 'master'. Running tests..."
    # Install test dependencies and run tests against the newly built image.
    # The '--rm' flag removes the container after the test run.
    if ! $COMPOSER -f docker-compose.yml run --rm backend sh -c "pip install -r LGS_Stock_Backend/requirements.txt -r LGS_Stock_Backend/requirements-dev.txt && pytest"; then
        echo "❌ Tests failed. Aborting release deployment."
        exit 1
    fi
else
    echo "⏩ This is a test deployment to '$BRANCH'. Skipping tests."
fi

# If we reach here, either tests passed or were skipped.
# First, tear down any existing services to free up ports and ensure a clean start.
echo "🛑 Stopping and removing old containers..."
# The '--remove-orphans' flag cleans up any containers for services that are
# no longer defined in the docker-compose file.
$COMPOSER -f docker-compose.yml down --remove-orphans

# Now, bring up the new services in detached mode.
echo "🚀 Starting services..."
$COMPOSER -f docker-compose.yml up -d

# Clean up old, unused Docker images to save disk space.
echo "🧹 Cleaning up old Docker images..."
docker image prune -af

echo "✅ Deployment of '$BRANCH' completed!"