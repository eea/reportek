import pytest

from django.core.management import call_command


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    pass


@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        call_command('loaddata', 'data/fixtures/countries.yaml')
        # call_command('loaddata', 'data/fixtures/instruments.yaml')
        # call_command('loaddata', 'data/fixtures/issues.yaml')
        # call_command('loaddata', 'data/fixtures/clients.yaml')
        # call_command('loaddata', 'data/fixtures/obligations.yaml')


