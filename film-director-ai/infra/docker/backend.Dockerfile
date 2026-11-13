FROM python:3.13-slim
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg libegl1 libgl1 libfontconfig1 blender && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .
ENV PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && uvicorn fda.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
