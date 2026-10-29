# Use an official lightweight Python image
FROM python:3.12-slim

# Prevent Python from writing .pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory inside the container
WORKDIR /app

# Install system dependencies required for Pillow, PostgreSQL, and Certificate fonts
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libjpeg-dev \
    zlib1g-dev \
    libpq-dev \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project files
COPY . /app/

# Collect static files during build (using dummy env vars so settings.py doesn't require live secrets at build time)
RUN SECRET_KEY="build-dummy-key" DEBUG="False" python manage.py collectstatic --no-input

# Expose port 8000 for Back4App Containers
EXPOSE 8000

# Run migrations and start Gunicorn with increased timeout for Cloudinary uploads
CMD ["sh", "-c", "python manage.py migrate --no-input && gunicorn core.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 3 --timeout 120"]