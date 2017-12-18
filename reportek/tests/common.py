from contextlib import contextmanager
import base64
from django.contrib.auth.models import User
from rest_framework import (
    HTTP_HEADER_ENCODING
)
from rest_framework.authtoken.models import Token
from rest_framework.test import (
    APIRequestFactory,
    APIClient,
)

from faker import Faker


api_factory = APIRequestFactory()
api_client = APIClient()

fake = Faker()


def fake_name(prefix):
    return f'{prefix}{fake.ean8()}'


def basic_auth(username):
    user = User.objects.get(username=username)
    credentials = ('%s:%s' % (user.username, user.password))
    base64_credentials = base64.b64encode(
        credentials.encode(HTTP_HEADER_ENCODING)
    ).decode(HTTP_HEADER_ENCODING)
    auth = 'Basic %s' % base64_credentials
    return auth


@contextmanager
def forced_auth(username):
    user = User.objects.get(username=username)
    api_client.force_authenticate(user=user)
    yield
    api_client.force_authenticate(user=None)


@contextmanager
def user_credentials(user):
    token = Token.objects.get(user__username=user)
    api_client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
    yield
    api_client.credentials()


@contextmanager
def user_session(username, password):
    api_client.login(username=username, password=password)
    yield
    api_client.logout()
