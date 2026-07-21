#!/bin/bash
set -e
set -o pipefail

# Railway provides DATABASE_URL and PORT as service variables.
python manage.py migrate --noinput
python manage.py bootstrap_business_domain

# Collect at runtime so STORAGE=S3 and Railway Bucket credentials are available.
python manage.py collectstatic --noinput

WORKERS=${GUNICORN_WORKERS:-2}
THREADS=${GUNICORN_THREADS:-2}

echo "Starting gunicorn with WORKERS=$WORKERS, THREADS=$THREADS"

exec gunicorn ruoom.wsgi:application \
    --bind 0.0.0.0:${PORT:-8080} \
    --workers "$WORKERS" \
    --threads "$THREADS" \
    --timeout 120
