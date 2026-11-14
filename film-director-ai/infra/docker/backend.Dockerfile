# One image: builds the website, then serves it and the API from the same FastAPI process.
FROM node:22-slim AS web
WORKDIR /w
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

FROM python:3.13-slim
ARG INSTALL_BLENDER=false
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg libegl1 libgl1 libfontconfig1 libglib2.0-0 postgresql postgresql-contrib \
    && apt-get install -y --no-install-recommends "postgresql-$(ls /usr/lib/postgresql | tail -1)-pgvector" \
    && if [ "$INSTALL_BLENDER" = "true" ]; then apt-get install -y --no-install-recommends blender; fi \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .
COPY --from=web /w/out /app/web
ENV PYTHONUNBUFFERED=1
EXPOSE 8000
COPY infra/docker/start.sh /start.sh
RUN chmod +x /start.sh
CMD ["/start.sh"]
