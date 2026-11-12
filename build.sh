#!/usr/bin/env bash
set -o errexit
pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
# Creates the admin user on first deploy if DJANGO_SUPERUSER_PASSWORD is set in Render env vars
if [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
  python manage.py createsuperuser --noinput --username "${DJANGO_SUPERUSER_USERNAME:-admin}" --email "${DJANGO_SUPERUSER_EMAIL:-}" || true
fi
