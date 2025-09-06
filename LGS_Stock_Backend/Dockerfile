FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Set PYTHONPATH to the project root inside the container
ENV PYTHONPATH=/app

# Copy requirements first to leverage Docker layer caching
COPY ./LGS_Stock_Backend/requirements.txt .

# Install build-time system dependencies for packages like lxml, install Python packages,
# then remove the build dependencies to keep the final image slim.
RUN apt-get update && \ 
    apt-get install -y --no-install-recommends build-essential libxml2-dev libxslt1-dev libpq-dev && \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    apt-get purge -y --auto-remove build-essential && \
    rm -rf /var/lib/apt/lists/*

# Copy the backend source code and the WSGI entrypoint
COPY ./LGS_Stock_Backend ./LGS_Stock_Backend
COPY ./wsgi.py .

# Expose the port the app runs on
EXPOSE 5000
# Run the app using gunicorn. It will find the 'app' object in 'wsgi.py'.
CMD ["gunicorn", "--worker-class", "eventlet", "-w", "1", "--bind", "0.0.0.0:5000", "wsgi:app"]
