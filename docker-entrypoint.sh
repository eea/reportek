#!/bin/sh

if [ -z "$POSTGRES_ADDR" ]; then
  export POSTGRES_ADDR="postgres"
fi

while ! nc -z $POSTGRES_ADDR 5432; do
  echo "Waiting for Postgres server at '$POSTGRES_ADDR' to accept connections on port 5432..."
  sleep 1s
done

python manage.py migrate

case "$1" in
    manage)
        exec python manage.py "$1"
        ;;
    run)
        exec gunicorn reportek.site.wsgi:application \
            --name reportek \
            --bind 0.0.0.0:80 \
            --workers 3 \
            --access-logfile - \
            --error-logfile -
        ;;
    *)
esac
