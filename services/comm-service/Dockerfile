# Python 3.12 slim base image
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ .
COPY register_service.py .
COPY consul/ ./consul/

EXPOSE 8000

CMD python manage.py migrate --noinput && \
    python register_service.py && \
    gunicorn comm_service.wsgi:application --bind 0.0.0.0:8000 --workers 2 --threads 4
