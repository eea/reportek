#!/bin/sh

if [ -z "$RABBITMQ_HOST" ]; then
  export RABBITMQ_HOST="rabbitmq"
fi

while ! nc -z ${RABBITMQ_HOST} 5672; do
  echo "Waiting for RabbitMQ server at '$RABBITMQ_HOST' to accept connections on port 5672..."
  sleep 1s
done

if [ -z "$POSTGRES_HOST" ]; then
  export POSTGRES_HOST="postgres"
fi

while ! nc -z ${POSTGRES_HOST} 5432; do
  echo "Waiting for Postgres server at '$POSTGRES_HOST' to accept connections on port 5432..."
  sleep 1s
done

if [ -z "$REPORTEK_HOST" ]; then
  export REPORTEK_HOST="app"
fi

if [ -z "$REPORTEK_GUNICORN_PORT" ]; then
  export REPORTEK_GUNICORN_PORT=8000
fi

while ! nc -z ${REPORTEK_HOST} ${REPORTEK_GUNICORN_PORT}; do
  echo "Waiting for app server at '$REPORTEK_HOST' to accept connections on port $REPORTEK_GUNICORN_PORT..."
  sleep 1s
done

exec celery -A reportek.site worker -l info -P gevent
