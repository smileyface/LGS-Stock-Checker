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

To update the running application with the latest code from a specific branch, you can follow these manual steps.

1.  **Navigate to the project directory:**
    ```bash
    cd ~/LGS-Stock-Checker
    ```

2.  **Check out the desired branch and pull the latest changes:**
    ```bash
    # Replace 'dev' with your desired branch (e.g., 'main', 'production')
    git checkout dev
    git pull origin dev
    ```

3.  **Rebuild and restart the containers:**
    ```bash
    docker compose up -d --build
    ```

### Automated Deployment Script

For convenience, you can use the `deploy.sh` script to automate the update process.

1.  **Make the script executable (only needs to be done once):**
    ```bash
    chmod +x deploy.sh
    ```

2.  **Run the script:**
    To deploy a specific branch, pass its name as an argument. If no branch is specified, it defaults to `dev`.
    ```bash
    # Deploy the 'main' branch
    ./deploy.sh main

    # Deploy the 'dev' branch (default)
    ./deploy.sh
    ```
