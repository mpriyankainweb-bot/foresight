FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy configuration and package files
COPY pyproject.toml README.md ./
COPY backend ./backend
COPY data ./data

# Install Python dependencies and package
RUN pip install --no-cache-dir -e .

EXPOSE 8000

ENV PYTHONUNBUFFERED=1
ENV FORESIGHT_MODE=offline
ENV PORT=8000

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
