"""
Django settings for reportek_site project.

Generated by 'django-admin startproject' using Django 1.11.7.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/
"""

import os
from django_jinja.builtins import DEFAULT_EXTENSIONS as JINJA_DEFAULT_EXTENSIONS


def split_env_var(name, sep=','):
    env_var = os.getenv(name, '')
    return [e.strip() for e in env_var.split(sep)]


def get_bool_env_var(name, default=None):
    env_var = os.getenv(name)
    if env_var is None:
        return default or None
    return env_var.lower() == 'yes'


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# repo root dir
ROOT_DIR = os.path.dirname(BASE_DIR)
PARENT_DIR = os.path.dirname(ROOT_DIR)


if os.getenv('TRAVIS'):
    POSTGRES_HOST = 'localhost'
    POSTGRES_DB = 'postgres'
    POSTGRES_USER = 'postgres'
    POSTGRES_PASSWORD = ''
else:
    POSTGRES_HOST = os.getenv('POSTGRES_HOST')
    POSTGRES_DB = os.getenv('POSTGRES_DB')
    POSTGRES_USER = os.getenv('POSTGRES_USER')
    POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')

REPORTEK_DOMAIN = os.getenv('REPORTEK_DOMAIN')
REPORTEK_USE_TLS = get_bool_env_var('REPORTEK_USE_TLS')

TUSD_UPLOADS_DIR = os.getenv('TUSD_UPLOADS_DIR')
ALLOWED_UPLOADS_ARCHIVE_EXTENSIONS = split_env_var('ALLOWED_UPLOADS_ARCHIVE_EXTENSIONS')
ALLOWED_UPLOADS_EXTENSIONS = split_env_var('ALLOWED_UPLOADS_EXTENSIONS')

# QA
QA_DEFAULT_XMLRPC_URI = os.getenv('QA_DEFAULT_XMLRPC_URI')

# ROD
ROD_ROOT_URL = 'http://rod.eionet.europa.eu'

# Toggles preservation of archive paths in names of unpacked files,
# i.e. 'dir1/dir2/file.xml' becomes 'dir1_dir2_file.xml'.
# This provides overwrite protection for cases where the archive
# contains files with the same name in several directories.
ARCHIVE_PATH_PREFIX = get_bool_env_var('ARCHIVE_PATH_PREFIX', True)


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'secret-key')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = get_bool_env_var('DEBUG', False)

ALLOWED_HOSTS = split_env_var('ALLOWED_HOSTS')


# Application definition

INSTALLED_APPS = [
    'reportek.core.apps.Config',
    'django_xworkflows',
    'typedmodels',
    'rest_framework',
    'rest_framework.authtoken',
    'django_jinja',
    'django_celery_beat',
    'django_extensions',
    'django_object_actions',
    'corsheaders',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'webpack_loader',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

CORS_ALLOW_CREDENTIALS = True

ROOT_URLCONF = 'reportek.site.urls'

TEMPLATES = [
    {
        'BACKEND': 'django_jinja.backend.Jinja2',
        'DIRS': [
            os.path.join(ROOT_DIR, 'templates'),
        ],
        'APP_DIRS': False,
        'OPTIONS': {
            # everything under our template dir is a jinja template
            "match_extension": None,
            "extensions": JINJA_DEFAULT_EXTENSIONS + [
                "webpack_loader.contrib.jinja2ext.WebpackExtension",
            ],
            # TODO: enable bytecode cache in production
        },
    },
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'reportek.site.wsgi.application'


# DRF

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ),
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
}


# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': POSTGRES_DB,
        'HOST': POSTGRES_HOST,
        'USER': POSTGRES_USER,
        'PASSWORD': POSTGRES_PASSWORD
    }
}


SILENCED_SYSTEM_CHECKS = [
    'fields.W342',  # Disable OneToOneField recommendation
]


# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = os.getenv('REPORTEK_TZ', 'UTC')

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

STATIC_ROOT = os.path.join(PARENT_DIR, 'static')
STATIC_URL = '/static/'

MEDIA_ROOT = os.path.join(PARENT_DIR, 'uploads')
MEDIA_URL = '/files/'

PROTECTED_ROOT = os.path.join(PARENT_DIR, 'protected_uploads')
PROTECTED_URL = '/protected-files/'

# TODO: this part should be synchronized with Webpack
# (see /frontend/config/conf.js)
_WEBPACK_DIST_DIR = os.path.join(ROOT_DIR, 'frontend', 'dist')

STATICFILES_DIRS = (
    (os.path.join(_WEBPACK_DIST_DIR, 'build')),
)

WEBPACK_LOADER = {
    'DEFAULT': {
        'BUNDLE_DIR_NAME': '',
        'STATS_FILE': os.path.join(_WEBPACK_DIST_DIR, 'stats.json'),
    },
}


FIXTURE_DIRS = [
    os.path.join(ROOT_DIR, 'data', 'fixtures')
]


# Celery
CELERY_BROKER_HOST = os.getenv('RABBITMQ_HOST')
CELERY_BROKER_VHOST = os.getenv('RABBITMQ_DEFAULT_VHOST')
CELERY_BROKER_USER = os.getenv('RABBITMQ_DEFAULT_USER')
CELERY_BROKER_PWD = os.getenv('RABBITMQ_DEFAULT_PASS')
CELERY_BROKER_URL = f'amqp://{CELERY_BROKER_USER}:{CELERY_BROKER_PWD}@{CELERY_BROKER_HOST}/{CELERY_BROKER_VHOST}'
CELERY_RESULT_BACKEND = 'amqp'

CELERY_TASK_DEFAULT_QUEUE = 'reportek'
CELERY_TASK_DEFAULT_EXCHANGE = 'reportek'
CELERY_TASK_DEFAULT_ROUTING_KEY = 'reportek'

CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_IGNORE_RESULT = True
CELERY_ACKS_LATE = True
CELERY_DISABLE_RATE_LIMITS = False
CELERY_IGNORE_RESULT = True
CELERY_TASK_RESULT_EXPIRES = 600

CELERY_ACCEPT_CONTENT = ['application/json']

CELERYD_HIJACK_ROOT_LOGGER = False
CELERYD_PREFETCH_MULTIPLIER = 1
CELERYD_MAX_TASKS_PER_CHILD = 1000


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '%(asctime)s [%(levelname)s] %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
        },
        'reportek.workflows': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
        },
        'reportek.qa': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
        },
        'reportek.tasks': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
        },
    },
}


try:
    from .localsettings import *
except ImportError:
    pass
