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
    local log_level=${2:-INFO}
    export LOG_LEVEL=$log_level # Export for docker-compose

    echo "🚀 Deploying branch: '$branch' with log level: $LOG_LEVEL"

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


    echo "�📡 Fetching latest updates from origin..."
    git fetch origin
    echo "� Checking out and resetting branch '$branch'..."
    git checkout "$branch"
    git reset --hard "origin/$branch"
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
        # Note: For better performance, consider creating a dedicated 'test' stage
        # in your Dockerfile that includes dev dependencies, avoiding runtime installation.
        local test_command="pip install -r LGS_Stock_Backend/requirements-dev.txt && pytest"
        if ! $composer_cmd -f docker-compose.yml run --rm backend sh -c "$test_command"; then
            echo "❌ Tests failed. Aborting release deployment." >&2
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