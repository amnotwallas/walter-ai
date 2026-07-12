# Stage 1: build deps with uv
FROM python:3.13-slim AS builder

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files first (layer cache)
COPY pyproject.toml .
COPY requirements.txt* ./

# Install dependencies into /app/.venv
RUN uv sync --no-dev --frozen 2>/dev/null || uv sync --no-dev

# Stage 2: runtime image
FROM python:3.13-slim AS runtime

WORKDIR /app

# Copy venv from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY main.py .
COPY app/ app/
COPY data/ data/

# Use venv python
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
