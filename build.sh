#!/usr/bin/env bash
# Exit immediately if a command exits with a non-zero status
set -o errexit

# Install production dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Collect static files with WhiteNoise
python manage.py collectstatic --no-input

# Apply database migrations (e.g. Neon PostgreSQL)
python manage.py migrate

