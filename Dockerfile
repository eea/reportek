FROM python:3.6-alpine3.6

# Can be overriden by compose
ARG REQUIREMENTS_FILE=requirements.txt

ENV PROJ_DIR=/var/local/reportek/
ENV MEDIA_ROOT=/var/local/uploads/
ENV PROTECTED_ROOT = /var/local/protected_uploads
ENV DOWNLOAD_STAGING_ROOT = /var/local/download_staging

RUN runDeps="gcc musl-dev postgresql-dev postgresql-client libressl-dev libxml2-dev libxslt-dev openldap git" \
    && apk add --no-cache $runDeps

RUN apk add --no-cache --virtual .build-deps \
        gcc musl-dev postgresql-dev libressl-dev libxml2-dev libxslt-dev openldap-dev yarn nodejs-npm \
    && mkdir -p $PROJ_DIR

# Add requirements.txt before rest of repo for caching
COPY *requirements.txt $PROJ_DIR
WORKDIR $PROJ_DIR

RUN pip install --no-cache-dir -r $REQUIREMENTS_FILE

# Only add yarn sources for caching
COPY yarn.lock package*.json $PROJ_DIR

# Yarn the madness
RUN yarn

# And now finally copy everything
COPY . $PROJ_DIR

# Build the webpack
RUN npm build

RUN mkdir -p $MEDIA_ROOT $PROTECTED_ROOT $DOWNLOAD_STAGING_ROOT

# Delete the build deps
RUN apk del .build-deps

ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["run"]
