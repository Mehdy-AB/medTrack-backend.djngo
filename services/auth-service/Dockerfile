# Python 3.12 slim base image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY src/ .

# Copy consul registration script
COPY register_service.py .
COPY consul/ ./consul/

# Expose port
EXPOSE 8000

# Start command - run migrations, register with consul, then start gunicorn
CMD python manage.py migrate --noinput && \
    python register_service.py && \
    gunicorn auth_service.wsgi:application --bind 0.0.0.0:8000 --workers 2 --threads 4
