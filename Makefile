# Makefile for LGS Stock Checker development

.PHONY: help install-dev test lint format clean-py run-dev stop-dev migrate

# Use python3 as the default interpreter
PYTHON := python3

# Define the virtual environment directory within the backend folder
VENV_DIR := backend/.venv
VENV_PYTHON := $(VENV_DIR)/bin/python

# Default target when running `make`
help:
	@echo "------------------------------------------------------------------------"
	@echo "LGS Stock Checker Development Makefile"
	@echo "------------------------------------------------------------------------"
	@echo "Available commands:"
	@echo "  make install-dev   - Creates a Python virtual environment and installs dev dependencies."
	@echo "  make test          - Runs backend unit tests using pytest."
	@echo "  make lint          - Lints the backend Python code with flake8."
	@echo "  make format        - Formats the backend Python code with Black."
	@echo "  make clean-py      - Removes the Python virtual environment and __pycache__ directories."
	@echo "  make run-dev       - Starts the local development environment using Docker Compose."
	@echo "  make stop-dev      - Stops the local development environment."
	@echo ""

# Use a timestamp file to track if dependencies are installed
$(VENV_DIR)/.installed: backend/requirements.txt backend/requirements-dev.txt
	@echo "Creating virtual environment in $(VENV_DIR)..."
	$(PYTHON) -m venv $(VENV_DIR)
	@echo "Installing development dependencies..."
	$(VENV_PYTHON) -m pip install -r backend/requirements.txt
	$(VENV_PYTHON) -m pip install -r backend/requirements-dev.txt
	touch $@

install-dev: $(VENV_DIR)/.installed
	@echo "Development environment is ready."

test: install-dev
	@echo "Running backend tests..."
	$(VENV_PYTHON) -m pytest backend/ --cov

lint: install-dev
	@echo "Linting backend code..."
	$(VENV_PYTHON) -m flake8 backend/ --exclude=$(VENV_DIR)

format: install-dev
	@echo "Formatting backend code with Black..."
	$(VENV_PYTHON) -m black backend/

clean-py:
	@echo "Cleaning Python artifacts..."
	rm -rf $(VENV_DIR)
	find . -type d -name "__pycache__" -exec rm -r {} +

run-dev:
	@echo "Starting development containers..."
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build

stop-dev:
	@echo "Stopping development containers..."
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml down