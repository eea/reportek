FROM python:3.6-alpine3.6

ARG REQUIREMENTS_FILE

ENV PROJ_DIR=/var/local/reportek/

RUN runDeps="gcc musl-dev postgresql-dev postgresql-client libressl-dev libxml2-dev libxslt-dev openldap git" \
    && apk add --no-cache $runDeps

RUN apk add --no-cache --virtual .build-deps \
        gcc musl-dev postgresql-dev libressl-dev libxml2-dev libxslt-dev openldap-dev \
    && mkdir -p $PROJ_DIR

RUN apk add --no-cache yarn nodejs-npm

# Add requirements.txt before rest of repo for caching
COPY $REQUIREMENTS_FILE $PROJ_DIR
WORKDIR $PROJ_DIR

RUN pip install --no-cache-dir -r REQUIREMENTS_FILE \
    && apk del .build-deps

COPY . $PROJ_DIR

RUN if [ "x$DJANGO_COLLECT_STATIC" = "xyes" ] ; then python manage.py collectstatic --noinput ; fi

# RUN python setup.py build_sphinx

ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["run"]
