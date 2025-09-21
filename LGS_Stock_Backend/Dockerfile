# --- Stage 1: Builder ---
# Use the full Python image which includes all the necessary build tools.
FROM python:3.9 as builder

# Set the working directory
WORKDIR /app

# Copy requirements first to leverage Docker layer caching
COPY ./LGS_Stock_Backend/requirements.txt .

# Install system dependencies and Python packages
# Using --no-install-recommends keeps the layer smaller.
# Cleaning apt cache is a good practice.
RUN apt-get update && \
    apt-get install -y --no-install-recommends python3-lxml && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# --- Stage 2: Final Image ---
# Start fresh with the slim image for a small final footprint.
FROM python:3.9-slim

# Set a more conventional working directory
WORKDIR /app

# Install runtime dependencies for psycopg2.
# The psycopg2 library requires the PostgreSQL client library (libpq).
RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq5 && \
    rm -rf /var/lib/apt/lists/*

# Create a non-root user and group for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy installed packages from the builder stage
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy the application source code into the container
COPY ./LGS_Stock_Backend .

# Copy the frontend's templates and static assets into the backend's package
# directory. This allows Flask's `render_template` and `url_for` to find them.
# These paths are relative to the WORKDIR (/app)
COPY ./frontend/templates ./templates
COPY ./frontend/src ./frontend_static
COPY ./frontend/public ./public

# Change ownership of the app directory to the non-root user
# This includes the persistent_data directory we created for the volume.
RUN chown -R appuser:appuser /app

# Switch to the non-root user
USER appuser

# Expose the port the app runs on
EXPOSE 5000

# Run the app using gunicorn. It will find the 'app' object in the 'run.py' file.
# The WORKDIR is /app, so gunicorn will find run.py there.
CMD ["gunicorn", "--worker-class", "eventlet", "-w", "1", "--bind", "0.0.0.0:5000", "server_entrypoint:app"]
