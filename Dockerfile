# Stage 1: Build Next.js Frontend
FROM node:20-slim AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
# Enable static export for Next.js
ENV NEXT_TELEMETRY_DISABLED=1
ENV NEXT_OUTPUT=export
RUN npm run build

# Stage 2: Final Production Container (Python + FastAPI serving Static Frontend)
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy configuration and backend package files
COPY pyproject.toml README.md ./
COPY backend ./backend
COPY data ./data

# Copy built frontend static export
COPY --from=frontend-builder /app/frontend/out ./frontend/out

# Install Python package and dependencies
RUN pip install --no-cache-dir -e .

EXPOSE 8000

ENV PYTHONUNBUFFERED=1
ENV FORESIGHT_MODE=offline
ENV PORT=8000

CMD ["sh", "-c", "uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
