FROM node:20-alpine AS builder

WORKDIR /app

ARG FORESIGHT_API_PROXY_TARGET=http://127.0.0.1:8000
ENV FORESIGHT_API_PROXY_TARGET=${FORESIGHT_API_PROXY_TARGET}

COPY package.json package-lock.json ./
RUN npm ci

COPY ./ ./

ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_ENV=production

RUN npm run build && mkdir -p .next/standalone/public && if [ -d public ]; then cp -R public/. .next/standalone/public/; fi

FROM node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3000
ENV HOSTNAME=0.0.0.0

COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/package.json ./package.json

EXPOSE 3000

CMD ["node", "server.js"]
