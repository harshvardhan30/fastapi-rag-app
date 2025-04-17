# Stage 1: Build Stage
FROM python:3.10-slim AS builder

WORKDIR /app

COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Final Stage
FROM python:3.10-slim

WORKDIR /app

# Copy dependencies from the builder stage
COPY --from=builder /app /app

# Expose port 80 for FastAPI app
EXPOSE 80

# Expose port 8001 for Prometheus metrics
EXPOSE 8001

# Define environment variable to make sure output is not buffered
ENV PYTHONUNBUFFERED 1

# Healthcheck
HEALTHCHECK CMD curl --fail http://localhost/health || exit 1

# Run FastAPI using Uvicorn when the container launches
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
