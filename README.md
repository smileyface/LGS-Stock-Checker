# LGS Stock Checker

An application to check card availability and pricing at your local gaming stores. Features a modern Vue.js frontend, a robust Flask backend API, and a background worker system for handling intensive tasks like web scraping.

## Features

*   **User Accounts:** Secure user registration and login system.
*   **Card Tracking:** Users can create and manage a list of cards they want to track.
*   **Store Preference:** Users can select which local stores they want to monitor.
*   **Real-time Availability:** Background workers check for card availability and push updates to the user via WebSockets.
*   **Modern UI:** A responsive and interactive Single Page Application (SPA) built with Vue.js.

## Tech Stack

*   **Frontend:** Vue.js, Vite, Axios, Bootstrap
*   **Backend:** Flask, Gunicorn, Flask-Login, Flask-SocketIO
*   **Database:** PostgreSQL
*   **Caching & Task Queue:** Redis
*   **Containerization:** Docker, Docker Compose

## Getting Started

### Prerequisites

Before you begin, ensure you have the following installed on your machine:

*   [Git](https://git-scm.com/)
*   [Docker](https://docs.docker.com/engine/install/)
*   [Docker Compose](https://docs.docker.com/compose/install/)

### Local Development

This project is configured for a seamless local development experience with hot-reloading for both the frontend and backend.

1.  **Clone the repository:**
    ```bash
    git clone <your-repository-url> LGS-Stock-Checker
    cd LGS-Stock-Checker
    ```

2.  **Run the development environment:**
    The root `package.json` provides a convenience script for this.
    ```bash
    npm install # Only needed once to install 'concurrently'
    npm run dev
    ```
    Alternatively, you can use Docker Compose directly:
    ```bash
    docker compose up --build
    docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
    ```

This command will:
*   Build the necessary Docker images.
*   Start all services (`frontend`, `backend`, `worker`, `db`, `redis`).
*   Use the `docker-compose.override.yml` file to enable hot-reloading.
*   The frontend will be accessible at `http://localhost:5173`.
*   The backend API (through the frontend proxy) will be available at `http://localhost:5173/api`.

### Production Deployment

The `deploy.sh` script is designed to automate deployments to a **production or test server environment**. It handles building production-ready images and configuring the application for remote access.

1.  **Initial Setup on Server:**
    Clone the repository onto your server.
    ```bash
    git clone <your-repository-url> ~/LGS-Stock-Checker
    cd ~/LGS-Stock-Checker
    ```

2.  **Firewall Configuration (Important!):**
    Ensure your server's firewall allows incoming traffic on port `8000`. For example, on Ubuntu with `ufw`:
    ```bash
    sudo ufw allow 8000/tcp
    ```

2.  **Make the script executable (only needs to be done once):**
    ```bash
    chmod +x deploy.sh
    ```

3.  **Run the Deployment Script:**
    To deploy, pass the branch name as the first argument and an optional log level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) as the second.
    *   Deploying `master` will run the test suite before deploying.
    *   Deploying any other branch will skip tests for a faster cycle.

    ```bash
    # Deploy the 'master' branch (runs tests) with default INFO logging
    ./deploy.sh master

    # Deploy a feature branch (skips tests) with DEBUG logging
    ./deploy.sh my-feature-branch DEBUG
    ```

The script will automatically detect the server's primary IP address, configure CORS, pull the latest code, build production images, run tests (if applicable), and restart the services.

After deployment, the application will be accessible from any machine on your network at `http://<your-server-ip>:8000`.


## Configuration

Application configuration is managed via environment variables set in the `docker-compose.yml` file. No `.env` file is required by default.

Key variables include:
*   `DATABASE_URL`: The connection string for the PostgreSQL database.
*   `REDIS_URL`: The connection string for the Redis server.
*   `CORS_ALLOWED_ORIGINS`: A comma-separated list of origins allowed to make requests to the backend API. This is crucial for connecting the frontend to the backend.
*   `FLASK_CONFIG`: Sets the application environment (e.g., `production` or `development`).
*   `LOG_LEVEL`: Controls the application's logging verbosity.

For production, you may want to move sensitive values out of the `docker-compose.yml` file and into a `.env` file, which should be excluded from version control.

## API Overview

The backend provides a JSON-based RESTful API. Key endpoints include:

*   `POST /api/login`: Authenticates a user and creates a session.
    *   **Body:** `{ "username": "...", "password": "..." }`
*   `POST /api/logout`: Logs out the current user.
*   `GET /api/user_data`: Retrieves the logged-in user's profile, including their list of preferred stores. (Requires authentication)
*   `GET /api/stores`: Returns a list of all available store slugs. (Requires authentication)
*   `POST /api/account/update_username`: Updates the logged-in user's username. (Requires authentication)
*   `POST /api/account/update_password`: Updates the logged-in user's password. (Requires authentication)
*   `POST /api/account/update_stores`: Updates the logged-in user's list of preferred stores. (Requires authentication)

Socket.IO is used for real-time communication, such as adding/editing/deleting tracked cards and receiving availability updates.
