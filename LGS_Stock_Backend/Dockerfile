FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Set PYTHONPATH to the project root inside the container
ENV PYTHONPATH=/app

# Copy requirements first to leverage Docker layer caching
COPY ./LGS_Stock_Backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend source code and the WSGI entrypoint
COPY ./LGS_Stock_Backend ./LGS_Stock_Backend
COPY ./wsgi.py .

# Expose the port the app runs on
EXPOSE 5000

# Run the app using gunicorn. It will find the 'app' object in 'wsgi.py'.
CMD ["gunicorn", "--worker-class", "eventlet", "-w", "1", "--bind", "0.0.0.0:5000", "wsgi:app"]