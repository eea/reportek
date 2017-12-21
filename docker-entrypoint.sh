#!/bin/sh

if [ -z "$POSTGRES_HOST" ]; then
  export POSTGRES_HOST="postgres"
fi

while ! nc -z ${POSTGRES_HOST} 5432; do
  echo "Waiting for Postgres server at '$POSTGRES_HOST' to accept connections on port 5432..."
  sleep 1s
done

if [ "x$DJANGO_MIGRATE" = 'xyes' ]; then
    python manage.py migrate --noinput
fi

if [ "x$DJANGO_LOAD_ROD_FIXTURES" = 'xyes' ]; then
    python manage.py load_rod_fixtures
fi

case "$1" in
    manage)
        exec python manage.py "$1"
        ;;
    run)
        exec gunicorn reportek.site.wsgi:application \
            --name reportek \
            --bind 0.0.0.0:${REPORTEK_GUNICORN_PORT:-8000} \
            --workers 3 \
            --access-logfile - \
            --error-logfile -
        ;;
    *)
esac
