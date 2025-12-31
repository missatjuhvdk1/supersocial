# ============================================
# Industry-Standard Python FastAPI Dockerfile
# Multi-stage build with security hardening
# Includes Playwright + FFmpeg for video processing
# ============================================

# Build argument for user configuration
ARG USER_UID=10001
ARG USER_GID=10001

# Stage 1: Base image with system dependencies
FROM python:3.11-slim-bookworm AS base

# Security: Set build arguments
ARG USER_UID
ARG USER_GID

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # FFmpeg for video processing
    ffmpeg \
    # Playwright browser dependencies (Debian Bookworm)
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libatspi2.0-0 \
    libxshmfence1 \
    # Essential utilities
    curl \
    ca-certificates \
    # Fonts for proper rendering
    fonts-liberation \
    fonts-noto-color-emoji \
    # libmagic for python-magic
    libmagic1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Create app directory
WORKDIR /app

# Stage 2: Builder - compile dependencies
FROM base AS builder

# Install build tools (only in builder stage)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    make \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip wheel --no-cache-dir --wheel-dir=/wheels -r requirements.txt

# Stage 3: Development image
FROM base AS development

ARG USER_UID
ARG USER_GID

# Copy wheels from builder
COPY --from=builder /wheels /wheels
COPY requirements.txt .

# Install from wheels (faster, no compilation needed)
RUN pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt && \
    rm -rf /wheels

# Install Playwright browsers
RUN playwright install chromium --with-deps

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/uploads /app/sessions /app/logs && \
    chmod -R 755 /app/uploads /app/sessions /app/logs

# Expose port
EXPOSE 8000

# Run with hot-reload for development
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Stage 4: Production image
FROM base AS production

ARG USER_UID
ARG USER_GID

# Copy wheels from builder
COPY --from=builder /wheels /wheels
COPY requirements.txt .

# Install from wheels (faster, no compilation needed)
RUN pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt && \
    rm -rf /wheels

# Security: Create non-root user BEFORE installing playwright
RUN groupadd --gid ${USER_GID} appuser && \
    useradd --uid ${USER_UID} --gid ${USER_GID} -m -s /bin/bash appuser && \
    # Create app directories with proper permissions
    mkdir -p /app/uploads /app/sessions /app/logs && \
    chown -R appuser:appuser /app && \
    # Create playwright cache directory for non-root user
    mkdir -p /home/appuser/.cache && \
    chown -R appuser:appuser /home/appuser

# Security: Switch to non-root user for browser installation
USER appuser

# Install Playwright browsers as non-root user
RUN playwright install chromium

# Copy application code
COPY --chown=appuser:appuser . .

# Set restrictive permissions
RUN chmod -R 750 /app && \
    chmod -R 770 /app/uploads /app/sessions /app/logs

# Expose port
EXPOSE 8000

# Health check using Python (no curl needed in production)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=5)" || exit 1

# Run application with Gunicorn and Uvicorn workers
# Workers configurable via environment variable
CMD ["sh", "-c", "gunicorn app.main:app \
    --workers ${GUNICORN_WORKERS:-4} \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --timeout 120 \
    --graceful-timeout 30 \
    --keep-alive 5 \
    --access-logfile - \
    --error-logfile - \
    --log-level ${LOG_LEVEL:-info} \
    --capture-output"]
