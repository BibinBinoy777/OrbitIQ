# syntax=docker/dockerfile:1
FROM ghcr.io/astral-sh/uv:0.12.23@sha256:61d393e44e249f2e4b526b6c7ddcecce245946826e608e11c93ad4f5bba55b21 AS uv
FROM python:3.12-slim-bookworm@sha256:34386ef0cb081344d7ec1c103ba398e6e9f64e9ab3a1509accc92a4e24a07258 AS api
COPY --from=uv /uv /usr/local/bin/uv
WORKDIR /app
ENV UV_PYTHON_DOWNLOADS=never UV_LINK_MODE=copy PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 PYTHONPATH=/app/backend PATH=/app/.venv/bin:$PATH
COPY pyproject.toml uv.lock ./
# Optional session CA mount: preserve verification, never embed proxy trust/secrets.
RUN --mount=type=secret,id=proxy_ca \
    if [ -f /run/secrets/proxy_ca ]; then export SSL_CERT_FILE=/run/secrets/proxy_ca; fi; \
    uv sync --locked --no-dev --no-managed-python && rm -rf /root/.cache/uv
COPY backend/orbitiq ./backend/orbitiq
COPY --chmod=644 deploy/logging.json ./deploy/logging.json
RUN chmod -R a+rX /app/backend /app/deploy
USER 10001:10001
EXPOSE 8000
CMD ["uvicorn", "orbitiq.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--no-proxy-headers", "--no-access-log", "--limit-concurrency", "32", "--timeout-keep-alive", "5", "--timeout-graceful-shutdown", "30", "--log-config", "deploy/logging.json"]

FROM node:24-bookworm-slim@sha256:a5f4366e834695d5f363b920c104953a535d3a9864d1bdf74566a0ebe01daee5 AS frontend-build
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN --mount=type=secret,id=proxy_ca \
    if [ -f /run/secrets/proxy_ca ]; then export NODE_EXTRA_CA_CERTS=/run/secrets/proxy_ca; fi; \
    npm ci --strict-ssl=true
COPY frontend/ ./
RUN npm run build

FROM nginxinc/nginx-unprivileged:1.28-alpine@sha256:7377697a821c131a924a7105fafbe7414db4e9fcc77a6f08f776f33f141ec3f8 AS web
COPY --chmod=644 deploy/nginx.conf /etc/nginx/nginx.conf
COPY --chmod=644 deploy/api-proxy.conf /etc/nginx/api-proxy.conf
COPY --chmod=644 deploy/security-headers.conf /etc/nginx/security-headers.conf
COPY --chmod=644 deploy/server-routes.conf /etc/nginx/server-routes.conf
COPY --from=frontend-build --chown=101:101 /app/dist /usr/share/nginx/html
EXPOSE 8080
