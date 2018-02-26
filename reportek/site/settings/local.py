from .base import *


DEBUG = True

INTERNAL_IPS = ['127.0.0.1']

INSTALLED_APPS += [
    'debug_toolbar',
]

MIDDLEWARE = [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
] + MIDDLEWARE

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'reportek',
        'HOST': '127.0.0.1',
        'USER': 'reportek',
        'PASSWORD': 'reportek'
    }
}

CORS_ORIGIN_WHITELIST += [
    'localhost:8080',
]

CELERY_BROKER_HEARTBEAT = 0
