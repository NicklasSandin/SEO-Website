# Build the web interface, then ship it inside the Flask image.
# NOTE: written but not built in the environment where it was authored (no image pulls were done there).

FROM node:22-alpine AS web
WORKDIR /web
COPY seo-service-website/package.json seo-service-website/package-lock.json seo-service-website/.npmrc ./
RUN npm ci --no-audit --no-fund
COPY seo-service-website/ ./
RUN npm run build

FROM python:3.12-slim AS app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_ENV=production \
    STATIC_DIR=/app/static \
    DATABASE_URL=sqlite:////data/siktio.db
WORKDIR /app
COPY seo-backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY seo-backend/src ./src
COPY --from=web /web/dist ./static
RUN useradd --system --uid 10001 siktio && mkdir /data && chown siktio /data
USER siktio
VOLUME /data
EXPOSE 8000

# SECRET_KEY has no default on purpose: in production mode the app refuses to start without one.
# One worker with threads keeps the in-memory login throttle accurate; analyses run inside the request, hence the long timeout.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
  CMD python -c "import urllib.request, sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=4).status == 200 else 1)"
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "1", "--threads", "4", "--timeout", "300", "src.app:create_app()"]
