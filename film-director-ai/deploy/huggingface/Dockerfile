# Hugging Face Space image: website + API + built-in PostgreSQL in one container, running as uid 1000.
FROM node:22-slim AS web
WORKDIR /w
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

FROM python:3.13-slim
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg libegl1 libgl1 libfontconfig1 libglib2.0-0 postgresql postgresql-contrib \
    && apt-get install -y --no-install-recommends "postgresql-$(ls /usr/lib/postgresql | tail -1)-pgvector" \
    && rm -rf /var/lib/apt/lists/*
RUN useradd -m -u 1000 user || true
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=1000 backend/ .
COPY --from=web --chown=1000 /w/out /app/web
COPY --chown=1000 infra/docker/start.sh /start.sh
RUN chmod +x /start.sh && mkdir -p /data && chown -R 1000 /data /app
USER 1000
ENV PYTHONUNBUFFERED=1 PORT=7860 HOME=/home/user FDA_ENV=production FDA_USE_CELERY=false FDA_STORAGE_BACKEND=db \
    FDA_STORAGE_DIR=/data/storage FDA_PG_DIR=/data/pg FDA_PG_SOCK=/data/pgsock FDA_RENDER_WORKERS=2
EXPOSE 7860
CMD ["/start.sh"]
