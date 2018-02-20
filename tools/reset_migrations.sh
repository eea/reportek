#!/usr/bin/env bash

read -p "Are you sure you want to drop the tables and reset migrations? (y/N)" -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
  python manage.py migrate core zero
  find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
  find . -path "*/migrations/*.pyc"  -delete
  python manage.py makemigrations
  python manage.py migrate
fi
