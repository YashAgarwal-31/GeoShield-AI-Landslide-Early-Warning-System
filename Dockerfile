# syntax=docker/dockerfile:1

FROM node:22-alpine AS frontend-builder
WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build


FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    APP_ENV=production \
    WEATHER_LIVE_ENABLED=false \
    MODEL_TRAINING_ENABLED=false

WORKDIR /app

COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

RUN addgroup --system geoshield && \
    adduser --system --ingroup geoshield --home /app geoshield && \
    mkdir -p /app/data

COPY --chown=geoshield:geoshield backend/ /app/backend/
COPY --chown=geoshield:geoshield datasets/ /app/datasets/
COPY --from=frontend-builder --chown=geoshield:geoshield /build/frontend/dist /app/frontend/dist

USER geoshield
WORKDIR /app/backend

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=3)"

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
