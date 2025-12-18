# Multi-stage Dockerfile for Python FastAPI backend with Playwright and FFmpeg
# Using Ubuntu for better Playwright compatibility

# Stage 1: Base image with system dependencies
FROM python:3.11-bookworm AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies including FFmpeg and Playwright requirements
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Build tools
    gcc \
    g++ \
    make \
    # FFmpeg for video processing
    ffmpeg \
    # Playwright browser dependencies (Debian Bookworm packages)
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
    # Additional utilities
    curl \
    wget \
    # Fonts
    fonts-liberation \
    fonts-noto-color-emoji \
    fonts-unifont \
    # libmagic for python-magic
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Stage 2: Dependencies installation
FROM base AS dependencies

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# Install Playwright browsers (skip system deps - we installed them above)
RUN playwright install chromium --with-deps || playwright install chromium

# Stage 3: Development image
FROM dependencies AS development

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
FROM dependencies AS production

# Copy application code
COPY . .

# Create necessary directories with proper permissions
RUN mkdir -p /app/uploads /app/sessions /app/logs && \
    chmod -R 755 /app/uploads /app/sessions /app/logs && \
    # Create non-root user for security
    useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app && \
    # Copy playwright browsers to user directory
    mkdir -p /home/appuser/.cache && \
    cp -r /root/.cache/ms-playwright /home/appuser/.cache/ 2>/dev/null || true && \
    chown -R appuser:appuser /home/appuser/.cache

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run application with Gunicorn and Uvicorn workers
CMD ["gunicorn", "app.main:app", \
     "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--log-level", "info"]
