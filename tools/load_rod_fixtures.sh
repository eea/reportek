#!/usr/bin/env sh

python manage.py loaddata data/fixtures/countries.yaml
python manage.py loaddata data/fixtures/instruments.yaml
python manage.py loaddata data/fixtures/issues.yaml
python manage.py loaddata data/fixtures/clients.yaml
python manage.py loaddata data/fixtures/obligations.yaml
