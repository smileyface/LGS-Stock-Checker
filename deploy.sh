#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
# Treat unset variables as an error when substituting.
# The return value of a pipeline is the status of the last command to exit with a non-zero status.
set -euo pipefail

# --- Main execution function ---
main() {
    # Get the directory of this script, which is assumed to be the repository root.
    # This makes the script portable and not dependent on a hardcoded path.
    cd "$( dirname "${BASH_SOURCE[0]}" )"

    local composer_cmd
    composer_cmd=$(detect_composer)

    # --- Deployment Arguments ---
    local branch=${1:-master}
    export LOG_LEVEL=${2:-INFO} # Export for docker-compose

    # --- Configure Environment for Deployment ---
    # Detect server's primary IP address for remote access
    local server_ip
    server_ip=$(hostname -I | awk '{print $1}')
    # Construct the CORS origins string and export it for docker-compose
    export CORS_ALLOWED_ORIGINS="http://localhost:8000,http://${server_ip}:8000"

    echo "🚀 Deploying branch: '$branch' with log level: $LOG_LEVEL on server IP: $server_ip"

    git_pull "$branch"
    build_images "$composer_cmd"
    run_tests_if_needed "$composer_cmd" "$branch"
    redeploy_services "$composer_cmd"
    cleanup_docker

    echo "✅ Deployment of '$branch' completed!"
}

# --- Helper Functions ---

detect_composer() {
    if command -v docker-compose &> /dev/null; then
        echo "docker-compose"
    elif command -v docker &> /dev/null && docker compose version &> /dev/null; then
        echo "docker compose"
    else
        echo "❌ Neither 'docker-compose' nor 'docker compose' command found. Aborting deployment." >&2
        exit 1
    fi
}

git_pull() {
    local branch=$1
    echo "📡 Fetching latest updates from origin..."
    # Fetch all branches and tags from the remote
    git fetch origin --force --tags

    echo " Checking out ref '$branch'..."
    # First, attempt to check out the ref. This works for both branches and tags.
    git checkout "$branch"

    # If it's a branch (not a tag), then reset it to match the remote.
    # We check if a remote branch with that name exists.
    if git show-ref --verify --quiet "refs/remotes/origin/$branch"; then
        echo " -> '$branch' is a branch. Resetting to match 'origin/$branch'..."
        git reset --hard "origin/$branch"
    fi
}

build_images() {
    local composer_cmd=$1
    echo "🏗️ Building Docker images..."
    if ! $composer_cmd -f docker-compose.yml build; then
        echo "❌ Docker build failed. Aborting deployment." >&2
        exit 1
    fi
}

run_tests_if_needed() {
    local composer_cmd=$1
    local branch=$2
    if [ "$branch" = "master" ]; then
        echo "🔬 This is a release deployment to 'master'. Running tests..."

        echo "   - Running backend tests..."
        # Build the 'backend' service, stopping at the 'test' stage.
        # This is more efficient than `docker-compose run` as it uses the build cache.
        # Assumes a 'test' stage exists in the backend Dockerfile.
        if ! $composer_cmd -f docker-compose.yml build --build-arg BUILDKIT_INLINE_CACHE=1 --target test backend; then
            echo "❌ Backend tests failed. Aborting release deployment." >&2
            exit 1
        fi

        echo "   - Running frontend tests..."
        if ! $composer_cmd -f docker-compose.yml build --build-arg BUILDKIT_INLINE_CACHE=1 --target test frontend; then
            echo "❌ Frontend tests failed. Aborting release deployment." >&2
            exit 1
        fi
    else
        echo "⏩ This is a test deployment to '$branch'. Skipping tests."
    fi
}

redeploy_services() {
    local composer_cmd=$1
    echo "🛑 Stopping and removing old containers..."
    $composer_cmd -f docker-compose.yml down --remove-orphans

    echo "🚀 Starting services..."
    $composer_cmd -f docker-compose.yml up -d
}

cleanup_docker() {
    echo "🧹 Cleaning up old Docker images..."
    docker image prune -af
}

# --- Script Entrypoint ---
# Call the main function with all script arguments
main "$@"