#!/bin/sh

if [ -z "$POSTGRES_HOST" ]; then
  export POSTGRES_HOST="postgres"
fi

while ! nc -z ${POSTGRES_HOST} 5432; do
  echo "Waiting for Postgres server at '$POSTGRES_HOST' to accept connections on port 5432..."
  sleep 1s
done

python manage.py migrate

if [ -z "$REPORETEK_GUNICORN_PORT" ]; then
  export REPORTEK_GUNICORN_PORT=8000
fi

case "$1" in
    manage)
        exec python manage.py "$1"
        ;;
    run)
        exec gunicorn reportek.site.wsgi:application \
            --name reportek \
            --bind 0.0.0.0:${REPORTEK_GUNICORN_PORT} \
            --workers 3 \
            --access-logfile - \
            --error-logfile -
        ;;
    *)
esac
