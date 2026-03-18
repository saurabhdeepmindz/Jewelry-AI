FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency spec first (layer caching)
COPY pyproject.toml .
RUN pip install --no-cache-dir -e ".[dev]"

# Copy source code
COPY . .

# Default command — overridden per service in docker-compose.yml
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
