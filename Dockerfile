FROM python:3.14-slim

ARG DEBUG=False
ARG USE_R2=True
ARG ALLOWED_HOSTS=
ARG CSRF_TRUSTED_ORIGINS=
ARG R2_PUBLIC_MEDIA_URL=
ARG PORT=8000
ARG GUNICORN_WORKERS=3
ARG GUNICORN_TIMEOUT=120

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_SYSTEM_PYTHON=1 \
    DEBUG=${DEBUG} \
    USE_R2=${USE_R2} \
    ALLOWED_HOSTS=${ALLOWED_HOSTS} \
    CSRF_TRUSTED_ORIGINS=${CSRF_TRUSTED_ORIGINS} \
    R2_PUBLIC_MEDIA_URL=${R2_PUBLIC_MEDIA_URL} \
    PORT=${PORT} \
    GUNICORN_WORKERS=${GUNICORN_WORKERS} \
    GUNICORN_TIMEOUT=${GUNICORN_TIMEOUT}

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

COPY requirements.txt ./
RUN uv pip install --system -r requirements.txt \
    && uv pip install --system django-storages boto3

COPY . .

RUN chmod +x docker/entrypoint.sh

EXPOSE 8000

CMD ["sh", "docker/entrypoint.sh"]
