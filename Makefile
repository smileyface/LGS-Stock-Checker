# Makefile for LGS Stock Checker development

.PHONY: help install-dev test lint format clean-py clean run-dev stop-dev reset-db db-init db-migrate db-upgrade

# Use python3 as the default interpreter
ifeq ($(OS),Windows_NT)
	PYTHON := python
else
	PYTHON := python3
endif

# Define the virtual environment directory within the backend folder
VENV_DIR := backend/.venv
ifeq ($(OS),Windows_NT)
	VENV_PYTHON := $(VENV_DIR)/Scripts/python
else
	VENV_PYTHON := $(VENV_DIR)/bin/python
endif

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
	@echo "  make clean         - Removes build artifacts from both frontend and backend."
	@echo "  make run-dev       - Starts the local development environment using Docker Compose."
	@echo "  make stop-dev      - Stops the local development environment."
	@echo "  make reset-db      - Stops containers and removes the database volume (WARNING: Data loss)."
	@echo "  make db-init       - Initializes the migration repository (run once)."
	@echo "  make db-migrate    - Generates a new migration script (usage: make db-migrate MSG=\"message\")."
	@echo "  make db-upgrade    - Applies pending migrations to the database."
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

clean: clean-py
	@echo "Cleaning frontend artifacts..."
	rm -rf frontend/node_modules frontend/dist frontend/build frontend/.next

run-dev:
	@echo "Starting development containers..."
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build

stop-dev:
	@echo "Stopping development containers..."
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml down

reset-db:
	@echo "Stopping containers and removing volumes (database reset)..."
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml down -v

db-init:
	@echo "Initializing migrations..."
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec backend flask db init

db-migrate:
	@echo "Generating migration..."
	@if [ -z "$(MSG)" ]; then echo "Error: MSG is not set. Usage: make db-migrate MSG=\"message\""; exit 1; fi
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec backend flask db migrate -m "$(MSG)"

db-upgrade:
	@echo "Applying migrations..."
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec backend flask db upgrade