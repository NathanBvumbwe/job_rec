#!/usr/bin/env bash
# exit on error
set -o errexit

# move into the directory containing manage.py
cd job_rec

# apply database migrations
python manage.py migrate

# collect static files
python manage.py collectstatic --noinput

# start the gunicorn server
gunicorn job_rec.wsgi:application --workers 1 --bind 0.0.0.0:$PORT --timeout 120