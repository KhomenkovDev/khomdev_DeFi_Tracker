FROM python:3.9-slim

WORKDIR /app

# Ensure output is unbuffered
ENV PYTHONUNBUFFERED=1

# Install system dependencies if required for pandas/numpy
RUN apt-get update && apt-get install -y build-essential curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Collect static files (assuming static root is configured)
RUN python manage.py collectstatic --noinput || true

# Run migrations (for SQLite in container)
RUN python manage.py migrate

# Expose dynamic PORT for GCP
EXPOSE $PORT

# Start the application using Gunicorn
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 finance_multitool.wsgi:application
