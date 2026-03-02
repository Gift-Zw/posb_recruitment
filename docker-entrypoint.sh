#!/bin/bash
set -e

# Wait for postgres to be ready (when using docker-compose)
if [ -n "$DB_HOST" ]; then
  echo "Waiting for database at $DB_HOST..."
  while ! python -c "
import socket
import os
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
  s.connect((os.environ.get('DB_HOST','localhost'), int(os.environ.get('DB_PORT', 5432))))
  s.close()
  exit(0)
except Exception:
  exit(1)
" 2>/dev/null; do
    sleep 1
  done
  echo "Database is up."
fi

python manage.py migrate --noinput
python manage.py collectstatic --noinput --clear --no-color 2>/dev/null || true

exec "$@"
