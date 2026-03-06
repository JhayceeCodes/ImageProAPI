#!/bin/sh
set -e

if [ "$SERVICE_TYPE" = "web" ]; then
    echo "Running migrations..."
    python manage.py migrate --noinput

    echo "Collecting static files..."
    python manage.py collectstatic --noinput

    echo "Starting Gunicorn..."
    exec gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 3 --threads 2

elif [ "$SERVICE_TYPE" = "worker" ]; then
    if [ "$CELERY_ROLE" = "beat" ]; then
        echo "Starting Celery Beat..."
        exec celery -A config beat -l info
    else
        echo "Starting Celery Worker..."
        exec celery -A config worker -l info --concurrency=4
    fi

fi

exec "$@"