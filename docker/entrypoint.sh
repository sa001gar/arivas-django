#!/bin/sh
set -e

mkdir -p /app/staticfiles

python manage.py migrate --noinput
python manage.py collectstatic --noinput --clear --verbosity 2

exec gunicorn arivas.wsgi:application \
  --bind 0.0.0.0:${PORT:-8080} \
  --workers ${GUNICORN_WORKERS:-3} \
  --timeout ${GUNICORN_TIMEOUT:-120}
