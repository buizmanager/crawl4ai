FROM python:3.12-slim-bookworm

# Set environment variables
ENV PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100 \
    DEBIAN_FRONTEND=noninteractive \
    REDIS_HOST=localhost \
    REDIS_PORT=6379

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    wget \
    gnupg \
    git \
    cmake \
    pkg-config \
    python3-dev \
    libjpeg-dev \
    redis-server \
    supervisor \
    && apt-get clean \ 
    && rm -rf /var/lib/apt/lists/*

# Install browser dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxcb1 \
    libxkbcommon0 \
    libx11-6 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libatspi2.0-0 \
    && apt-get clean \ 
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user and group
RUN groupadd -r appuser && useradd --no-log-init -r -g appuser appuser

# Create and set permissions for appuser home directory
RUN mkdir -p /home/appuser && chown -R appuser:appuser /home/appuser

# Set working directory
WORKDIR /app

# Copy requirements files
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright and browsers
RUN playwright install --with-deps chromium

# Set up Playwright for the non-root user
RUN mkdir -p /home/appuser/.cache/ms-playwright \
    && cp -r /root/.cache/ms-playwright/chromium-* /home/appuser/.cache/ms-playwright/ \
    && chown -R appuser:appuser /home/appuser/.cache/ms-playwright

# Copy application files
COPY . /app/

# Create directories for Redis
RUN mkdir -p /var/lib/redis /var/log/redis && chown -R appuser:appuser /var/lib/redis /var/log/redis

# Copy supervisor configuration
COPY supervisord.conf /app/supervisord.conf

# Change ownership of the application directory to the non-root user
RUN chown -R appuser:appuser /app

# Expose the API port
EXPOSE 7860

# Set environment variables to production
ENV PYTHON_ENV=production 

# Switch to the non-root user
USER appuser

# Start the application using supervisord
CMD ["supervisord", "-c", "supervisord.conf"]