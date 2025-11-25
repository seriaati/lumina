# Dockerfile for Lumina Discord Bot
# Multi-stage build optimized for production deployment

# Build stage: Install dependencies and compile bytecode
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

# Enable bytecode compilation for faster startup and copy link mode for multi-stage
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# Disable Python downloads - use the system Python interpreter
# This ensures consistency between build and runtime images
ENV UV_PYTHON_DOWNLOADS=0

WORKDIR /app

# Install dependencies first (separate layer for better caching)
# This layer will be cached unless uv.lock or pyproject.toml changes
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-dev

# Copy application source code
COPY . /app

# Install the project itself (changes frequently, separate layer)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev

# Final runtime stage: Minimal image without uv
FROM python:3.12-slim-bookworm

# Set production environment
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Create non-root user for security
RUN groupadd --system --gid 999 lumina \
 && useradd --system --gid 999 --uid 999 --create-home lumina

# Copy the application and virtual environment from builder
COPY --from=builder --chown=lumina:lumina /app /app

# Place virtual environment executables at the front of PATH
ENV PATH="/app/.venv/bin:$PATH"

# Create required directories with proper permissions
RUN mkdir -p /app/logs && chown -R lumina:lumina /app/logs

# Switch to non-root user
USER lumina

# Set working directory
WORKDIR /app

# Health check (optional - adjust port if you add a health endpoint)
# HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
#   CMD python -c "import sys; sys.exit(0)"

# Run the application
CMD ["python", "run.py"]
