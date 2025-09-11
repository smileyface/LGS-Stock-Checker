# LGS Stock Checker

*Check your local gaming stores for cards you need before you get there!*

## Server Deployment

This guide outlines the steps to deploy and run the LGS Stock Checker application on a server using Docker.

### Prerequisites

Before you begin, ensure you have the following installed on your server:

*   [Git](https://git-scm.com/)
*   [Docker](https://docs.docker.com/engine/install/)
*   [Docker Compose](https://docs.docker.com/compose/install/)

### 1. Initial Setup

First, clone the repository to your server. It's recommended to place it in the home directory (`~/`) for consistency with the deployment script.

```bash
git clone <your-repository-url> ~/LGS-Stock-Checker
cd ~/LGS-Stock-Checker
```
*Replace `<your-repository-url>` with the actual URL of your Git repository.*

### 2. Configuration

This application uses Docker Compose, which often relies on an environment file for configuration (e.g., API keys, database credentials, etc.).

1.  **Create an environment file:**
    If an example environment file (e.g., `.env.example`) exists in the repository, copy it to a new `.env` file.
    ```bash
    cp .env.example .env
    ```
    If no example file exists, you will need to create the `.env` file from scratch based on the variables required by the `docker-compose.yml` file.

2.  **Edit the environment file:**
    Open the `.env` file with your preferred text editor (like `nano` or `vim`) and fill in the required values.
    ```bash
    nano .env
    ```
    You will need to set variables like `SECRET_KEY`. For the future email service, you would also add:
    ```
    SMTP_SERVER=smtp.gmail.com
    SMTP_PORT=587
    EMAIL_SENDER=your-email@gmail.com
    EMAIL_PASSWORD=your-app-password
    EMAIL_RECIPIENT=admin-email@example.com
    ```

### 3. Running the Application

Once the repository is cloned and the `.env` file is configured, you can build and start the application containers.

```bash
docker compose up -d --build
```

*   `docker compose up`: This command creates and starts the services defined in your `docker-compose.yml` file.
*   `-d` (or `--detach`): Runs the containers in the background.
*   `--build`: Forces Docker to rebuild the images before starting the containers. This is crucial for ensuring your latest code changes are applied.

After running this command, the application should be up and running. You can check the status of your containers with:

```bash
docker compose ps
```

To view the application logs, run:

```bash
docker compose logs -f
```

### 4. Updating the Application (Deployment)

To update the running application with the latest code from a specific branch, use the provided `deploy.sh` script.

The script supports two types of deployments based on the branch name:
*   **Release Deployments:** Triggered by deploying the `master` branch. This will build the images, run the full test suite, and then start the services.
*   **Test Deployments:** Triggered by deploying any other branch (e.g., a feature branch). This will build the images and start the services, but it will *skip* the test suite for a faster deployment cycle.

### Automated Deployment Script

For convenience, you can use the `deploy.sh` script to automate the update process.

1.  **Make the script executable (only needs to be done once):**
    ```bash
    chmod +x deploy.sh
    ```

2.  **Run the script:**
    To deploy a specific branch, pass its name as an argument. If no branch is specified, it defaults to `master` for a release deployment.
    ```bash
    # Deploy the 'master' branch (runs tests)
    ./deploy.sh master

    # Deploy a feature branch (skips tests)
    ./deploy.sh my-feature-branch
    ```
