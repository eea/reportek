#!/bin/sh

if [ -z "$POSTGRES_HOST" ]; then
  export POSTGRES_HOST="postgres"
fi

while ! nc -z ${POSTGRES_HOST} 5432; do
  echo "Waiting for Postgres server at '$POSTGRES_HOST' to accept connections on port 5432..."
  sleep 1s
done

if [ -z "$REDIS_HOST" ]; then
  export REDIS_HOST="redis"
fi

while ! nc -z ${REDIS_HOST} 6379; do
  echo "Waiting for Redis server at '$REDIS_HOST' to accept connections on port 6379..."
  sleep 1s
done

if [ "x$DJANGO_MIGRATE" = 'xyes' ]; then
    python manage.py migrate --noinput
fi

if [ "x$DJANGO_COLLECT_STATIC" = "xyes" ]; then
  python manage.py collectstatic --noinput
fi

if [ "x$DJANGO_LOAD_ROD_FIXTURES" = 'xyes' ]; then
    python manage.py load_rod_fixtures
fi

case "$1" in
    manage)
        exec python manage.py "$1"
        ;;
    run)
        if [ "x$DEBUG" = 'xyes' ]; then
            exec python manage.py runserver 0.0.0.0:${REPORTEK_GUNICORN_PORT:-8000}
        else
            exec daphne reportek.site.asgi:application \
                --bind 0.0.0.0 \
                --port ${REPORTEK_GUNICORN_PORT:-8000} \
                --unix-socket /tmp/daphne.sock \
                --access-log - \
                --proxy-headers
            ;;
    *)
esac
