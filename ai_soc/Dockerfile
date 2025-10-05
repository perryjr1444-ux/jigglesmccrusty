# AI SOC Service Dockerfile
FROM python:3.11-slim

LABEL maintainer="AI-SOC Team"
LABEL description="AI-powered Security Operations Center microservice"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry==1.8.0

# Create app directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml ./

# Configure Poetry to not create virtual environment
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry install --no-interaction --no-ansi --no-root

# Copy application code
COPY ai_soc ./ai_soc

# Install the application
RUN poetry install --no-interaction --no-ansi

# Create secrets directory
RUN mkdir -p /run/secrets

# Create non-root user
RUN useradd -m -u 1000 aisoc && \
    chown -R aisoc:aisoc /app

USER aisoc

# Expose port
EXPOSE 9000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:9000/health || exit 1

# Run the application
CMD ["uvicorn", "ai_soc.main:app", "--host", "0.0.0.0", "--port", "9000"]
