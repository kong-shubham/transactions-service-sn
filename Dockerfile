# Use Python 3.13 as base image
FROM python:3.13.4-alpine3.22 AS builder

# Install Poetry
RUN pip install --no-cache-dir poetry==2.1.3

# Set working directory
WORKDIR /app

# Copy project files needed for installation
COPY pyproject.toml ./
COPY README.md ./

# Generate lock file and install dependencies
RUN poetry config virtualenvs.create false && \
    poetry lock && \
    poetry install --only main --no-interaction --no-root

# Final stage
FROM python:3.13.4-alpine3.22

WORKDIR /app

# Copy installed packages from builder stage
COPY --from=builder /usr/local/lib/python3.13/site-packages/ /usr/local/lib/python3.13/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Create transactions directory
RUN mkdir -p /app/transactions

# Copy application code
COPY transactions/ ./transactions/
COPY README.md ./

# Install curl for health checks
RUN apk add --no-cache \
        libffi \
        curl

# Expose API port
EXPOSE 8082

# Run the application
CMD ["uvicorn", "transactions.main:app", "--host", "0.0.0.0", "--port", "8082"]
