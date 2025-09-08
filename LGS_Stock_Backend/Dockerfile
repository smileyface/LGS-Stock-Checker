# --- Stage 1: Builder ---
# Use the full Python image which includes all the necessary build tools.
FROM python:3.9 as builder

# Set the working directory
WORKDIR /app

# Copy requirements first to leverage Docker layer caching
COPY ./LGS_Stock_Backend/requirements.txt .

# Install pre-compiled system packages for dependencies that are slow to build from source,
# then install the rest of the Python packages with pip into the global site-packages.
RUN apt-get update && \
    apt-get install -y --no-install-recommends python3-lxml && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# --- Stage 2: Final Image ---
# Start fresh with the slim image for a small final footprint.
FROM python:3.9-slim

WORKDIR /app/LGS_Stock_Backend

# Copy the installed packages and executables from the builder stage.
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy the backend source code. The WORKDIR is already set to the package root.
COPY ./LGS_Stock_Backend .

# Copy the frontend's templates and static assets into the backend's package
# directory. This allows Flask's `render_template` and `url_for` to find them.
COPY ./LGS_Stock_Frontend/templates ./templates
COPY ./LGS_Stock_Frontend/static ./static

# Expose the port the app runs on
EXPOSE 5000
# Run the app using gunicorn. It will find the 'app' object in the 'run.py' file.
CMD ["gunicorn", "--worker-class", "eventlet", "-w", "1", "--bind", "0.0.0.0:5000", "run:app"]
