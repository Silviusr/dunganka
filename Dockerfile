FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 DJANGO_DB_PATH=/app/data/db.sqlite3
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && useradd --create-home app
COPY --chown=app:app . .
RUN mkdir -p /app/data && chown app:app /app/data
USER app
RUN python manage.py collectstatic --noinput
EXPOSE 8000
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py seed_demo && exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 1 --threads 2 --timeout 30"]
