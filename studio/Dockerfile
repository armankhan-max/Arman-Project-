FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg fontconfig \
    && rm -rf /var/lib/apt/lists/*
RUN useradd -m -u 1000 user
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=user . .
RUN mkdir -p /app/data && chown -R user /app
USER user
ENV STUDIO_DATA=/app/data PORT=7860 PYTHONUNBUFFERED=1
EXPOSE 7860
CMD ["python", "app.py"]
