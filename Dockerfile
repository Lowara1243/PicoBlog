# Build stage for CSS
FROM node:18-alpine AS css-builder

WORKDIR /app
COPY package.json package-lock.json tailwind.config.js ./
COPY app/static/input.css ./app/static/
COPY app/templates ./app/templates

RUN npm ci
RUN npm run build:css

# Final stage
FROM python:3.10-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    FLASK_APP=app \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy Python dependencies
COPY pyproject.toml uv.lock ./

# Sync dependencies
# We use --frozen to ensure strict consistency with the lockfile
RUN uv sync --frozen --no-dev

# Copy application code
COPY . .

# Copy built CSS from css-builder
COPY --from=css-builder /app/app/static/css/style.css ./app/static/css/style.css

# Create necessary directories
RUN mkdir -p data app/static/uploads

# Create a non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["gunicorn", "--workers", "4", "--bind", "0.0.0.0:8000", "run:app"]
