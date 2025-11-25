# Use the stable Ubuntu 22.04 (Jammy) base image
FROM mcr.microsoft.com/devcontainers/base:ubuntu-22.04

# Avoid warnings by switching to non-interactive
ENV DEBIAN_FRONTEND=noninteractive

# Update and install Python 3, pip, venv, and basic build tools
# We also install flake8 here directly to replace the feature
RUN apt-get update \
    && apt-get -y install --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    build-essential \
    && apt-get clean -y && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install flake8 globally so the VS Code extension can find it
RUN python3 -m pip install --upgrade pip flake8

# Switch back to dialog for any ad-hoc use of apt-get
ENV DEBIAN_FRONTEND=dialog