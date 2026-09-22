#!/bin/sh
# Waits for the database, then brings the schema and the static files up to date before
# handing over to the command (daphne, celery worker, celery beat, manage.py, ...).
#
# Only the web container should migrate. The worker and beat containers set
# RUN_MIGRATIONS=0 so three containers do not race each other on start-up.
set -e

RUN_MIGRATIONS="${RUN_MIGRATIONS:-1}"
COLLECT_STATIC="${COLLECT_STATIC:-$RUN_MIGRATIONS}"

python - <<'PY'
import os
import sys
import time

if os.environ.get('DJANGO_DB_ENGINE') != 'postgres':
    sys.exit(0)

import socket

host = os.environ.get('POSTGRES_HOST', 'db')
port = int(os.environ.get('POSTGRES_PORT', '5432'))
deadline = time.time() + int(os.environ.get('DB_WAIT_SECONDS', '60'))
while time.time() < deadline:
    try:
        with socket.create_connection((host, port), timeout=2):
            print(f'database {host}:{port} is up')
            sys.exit(0)
    except OSError:
        time.sleep(1)
print(f'database {host}:{port} did not come up in time', file=sys.stderr)
sys.exit(1)
PY

if [ "$RUN_MIGRATIONS" = "1" ]; then
  echo "applying migrations"
  python manage.py migrate --noinput
fi

if [ "$COLLECT_STATIC" = "1" ]; then
  echo "collecting static files"
  python manage.py collectstatic --noinput
fi

exec "$@"
