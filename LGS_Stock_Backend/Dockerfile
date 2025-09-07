# --- Stage 1: Builder ---
# Use the full Python image which includes all the necessary build tools.
FROM python:3.9 as builder

# Set the working directory
WORKDIR /app

# Create and activate a virtual environment for clean dependency management
ENV VIRTUAL_ENV=/app/venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Copy requirements first to leverage Docker layer caching
COPY ./LGS_Stock_Backend/requirements.txt .

# Install pre-compiled system packages for dependencies that are slow to build from source.
# Then, install the rest of the Python packages with pip.
RUN apt-get update && \
    apt-get install -y --no-install-recommends python3-lxml && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt


# --- Stage 2: Final Image ---
# Start fresh with the slim image for a small final footprint.
FROM python:3.9-slim

WORKDIR /app

# Copy the virtual environment from the builder stage. This contains all our installed packages.
COPY --from=builder /app/venv /app/venv

# Copy the backend source code and the WSGI entrypoint
COPY ./LGS_Stock_Backend ./LGS_Stock_Backend
COPY ./wsgi.py .

# Activate the virtual environment by adding it to the PATH.
ENV PATH="/app/venv/bin:$PATH"

# Expose the port the app runs on
EXPOSE 5000
# Run the app using gunicorn. It will find the 'app' object in 'wsgi.py'.
CMD ["gunicorn", "--worker-class", "eventlet", "-w", "1", "--bind", "0.0.0.0:5000", "wsgi:app"]
