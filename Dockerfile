# FROM python:3.13-slim

# WORKDIR /app

# RUN apt-get update && apt-get install -y --no-install-recommends \
#     build-essential \
#     libpq-dev \
#     && rm -rf /var/lib/apt/lists/*

# ENV PYTHONPATH=/app

# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt

# COPY . .

# # Optional (can remove or change to 8080)
# EXPOSE 8080

# CMD ["sh", "-c", "uvicorn src.api.rest.app:app --host 0.0.0.0 --port ${PORT:-8080}"]
FROM python:3.12-slim

# Create non-root user
RUN adduser --disabled-password --gecos "" appuser

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy dependency files first for layer caching
COPY pyproject.toml uv.lock ./

# Install production dependencies only
RUN uv sync --frozen --no-dev

# Copy source
COPY src/ ./src/

ENV PYTHONPATH=/app

# Switch to non-root user
USER appuser

EXPOSE 8080

CMD ["sh", "-c", "uv run uvicorn src.api.rest.app:app --host 0.0.0.0 --port ${PORT:-8080}"]