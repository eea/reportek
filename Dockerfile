FROM python:3.6-alpine3.6

ENV PROJ_DIR=/var/local/reportek/

RUN runDeps="gcc musl-dev postgresql-dev postgresql-client libressl-dev git" \
    && apk add --no-cache $runDeps

RUN apk add --no-cache --virtual .build-deps \
        gcc musl-dev postgresql-dev libressl-dev \
    && mkdir -p $PROJ_DIR

# Add requirements.txt before rest of repo for caching
COPY requirements.txt $PROJ_DIR
WORKDIR $PROJ_DIR

RUN pip install --no-cache-dir -r requirements.txt \
    && apk del .build-deps

COPY . $PROJ_DIR

RUN python manage.py collectstatic --noinput

RUN python setup.py build_sphinx

ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["run"]
