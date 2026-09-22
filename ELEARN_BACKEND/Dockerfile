# Backend image: Django + Daphne (ASGI), also used for the celery worker and beat.
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# psycopg ships its own libpq in the [binary] wheel, so no build toolchain is needed
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# celery and daphne must not run as root. chmod because a checkout on Windows
# does not carry the executable bit.
RUN chmod +x /app/docker-entrypoint.sh \
 && useradd --create-home --uid 10001 app \
 && mkdir -p /srv/media /srv/static \
 && chown -R app:app /app /srv/media /srv/static
USER app

EXPOSE 8000

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "ELEARN_BACKEND.asgi:application"]
