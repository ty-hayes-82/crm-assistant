# Multi-stage Dockerfile for CRM Assistant
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create non-root user
RUN groupadd -r crm && useradd -r -g crm -d /app -s /bin/bash crm

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt pyproject.toml ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Development stage
FROM base as development

# Install development dependencies
RUN pip install --no-cache-dir pytest pytest-asyncio pytest-cov black isort mypy

# Copy source code
COPY . .

# Change ownership to non-root user
RUN chown -R crm:crm /app

# Switch to non-root user
USER crm

# Expose ports
EXPOSE 10000 9090

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:10000/health || exit 1

# Default command for development
CMD ["python", "-m", "crm_agent.a2a.http_server", "--host", "0.0.0.0", "--port", "10000"]

# Production stage
FROM base as production

# Copy only necessary files for production
COPY crm_agent/ ./crm_agent/
COPY crm_fastmcp_server/ ./crm_fastmcp_server/
COPY scripts/ ./scripts/
COPY requirements.txt pyproject.toml ./

# Create logs directory
RUN mkdir -p logs && chown -R crm:crm /app

# Switch to non-root user
USER crm

# Expose A2A server port
EXPOSE 10000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:10000/health || exit 1

# Production command
CMD ["python", "-m", "crm_agent.a2a.http_server"]
