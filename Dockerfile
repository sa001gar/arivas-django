FROM ghcr.io/astral-sh/uv:latest AS uv
FROM python:3.14-slim

ARG DEBUG=False
ARG USE_R2=True
ARG ALLOWED_HOSTS=
ARG CSRF_TRUSTED_ORIGINS=
ARG R2_PUBLIC_MEDIA_URL=
ARG PORT=8080
ARG GUNICORN_WORKERS=3
ARG GUNICORN_TIMEOUT=120

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_SYSTEM_PYTHON=1 \
    UV_LINK_MODE=copy \
    DEBUG=${DEBUG} \
    USE_R2=${USE_R2} \
    ALLOWED_HOSTS=${ALLOWED_HOSTS} \
    CSRF_TRUSTED_ORIGINS=${CSRF_TRUSTED_ORIGINS} \
    R2_PUBLIC_MEDIA_URL=${R2_PUBLIC_MEDIA_URL} \
    PORT=${PORT} \
    GUNICORN_WORKERS=${GUNICORN_WORKERS} \
    GUNICORN_TIMEOUT=${GUNICORN_TIMEOUT}

WORKDIR /app

COPY --from=uv /uv /usr/local/bin/uv

COPY requirements.txt ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip sync --system requirements.txt

COPY . .

RUN chmod +x docker/entrypoint.sh

CMD ["sh", "docker/entrypoint.sh"]
