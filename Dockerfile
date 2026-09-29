FROM node:20-bookworm-slim AS builder

ENV NEXT_TELEMETRY_DISABLED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-venv \
    python3-pip \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml README.md ./
COPY backend ./backend
COPY data ./data
RUN python3 -m venv /opt/foresight-venv \
    && /opt/foresight-venv/bin/pip install --no-cache-dir .

WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
ARG FORESIGHT_API_PROXY_TARGET=http://127.0.0.1:8000
ENV FORESIGHT_API_PROXY_TARGET=${FORESIGHT_API_PROXY_TARGET}
ENV NODE_ENV=production
RUN npm run build \
    && mkdir -p .next/standalone/public \
    && if [ -d public ]; then cp -R public/. .next/standalone/public/; fi

FROM node:20-bookworm-slim AS runner
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    HOSTNAME=0.0.0.0 \
    PORT=10000 \
    FORESIGHT_MODE=offline \
    PYTHONUNBUFFERED=1 \
    PATH=/opt/foresight-venv/bin:$PATH

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --from=builder /opt/foresight-venv /opt/foresight-venv
COPY pyproject.toml README.md ./
COPY backend ./backend
COPY data ./data
COPY scripts/start_web.sh ./scripts/start_web.sh
COPY --from=builder /app/frontend/.next/standalone ./
COPY --from=builder /app/frontend/.next/static ./.next/static

EXPOSE 10000
CMD ["/bin/sh", "/app/scripts/start_web.sh"]
