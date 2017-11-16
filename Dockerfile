FROM python:3.6
ENV PYTHONUNBUFFERED 1
ENV DJANGO_ENV=prod
ENV DOCKER_CONTAINER=1
RUN mkdir /opt/reportek
ADD requirements.txt /opt/reportek/
WORKDIR /opt/reportek
RUN pip3 install uwsgi
RUN pip3 install -r requirements.txt
ADD . /opt/reportek/
