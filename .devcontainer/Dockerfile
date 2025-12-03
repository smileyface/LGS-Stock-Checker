# Use the stable Ubuntu 22.04 (Jammy) base image
FROM mcr.microsoft.com/devcontainers/base:ubuntu-22.04

# Avoid warnings by switching to non-interactive
ENV DEBIAN_FRONTEND=noninteractive

RUN mkdir -p /workspaces/LGS-Stock-Checker \
    && chown -R vscode:vscode /workspaces/LGS-Stock-Checker
WORKDIR /workspaces/LGS-Stock-Checker

# Update and install Python 3, pip, venv, and basic build tools
# We also install flake8 here directly to replace the feature
RUN apt-get update \
    && apt-get -y install --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    build-essential \
    curl \
    wget \
    ca-certificates \
    dos2unix \
    && apt-get clean -y && rm -rf /var/lib/apt/lists/*


# Add Node
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && npm install -g npm@latest

# Upgrade pip and install flake8 globally so the VS Code extension can find it
RUN python3 -m pip install --upgrade pip flake8

# Switch back to dialog for any ad-hoc use of apt-get
ENV DEBIAN_FRONTEND=dialog
