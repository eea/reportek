"""
Django settings for reportek_site project.

Generated by 'django-admin startproject' using Django 1.11.7.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/
"""

import os
from pathlib import Path
from django_jinja.builtins import DEFAULT_EXTENSIONS as JINJA_DEFAULT_EXTENSIONS
import ldap
from django.core.exceptions import ImproperlyConfigured
from django_auth_ldap.config import (
    LDAPSearch,
    NestedGroupOfUniqueNamesType
)


def get_env_var(var_name, default=None):
    var = os.getenv(var_name, default)
    if var is None and default is None:
        raise ImproperlyConfigured(f'Set the {var_name} environment variable')
    return var


def get_bool_env_var(var_name, default=None):
    var = get_env_var(var_name, default)
    return var.lower() == 'yes'


def split_env_var(var_name, sep=','):
    var = get_env_var(var_name)
    return [e.strip() for e in var.split(sep)]


# <project>/reportek
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Project dir
ROOT_DIR = BASE_DIR.parent

# Outside project
PARENT_DIR = ROOT_DIR.parent


if os.getenv('TRAVIS'):
    POSTGRES_HOST = 'localhost'
    POSTGRES_DB = 'postgres'
    POSTGRES_USER = 'postgres'
    POSTGRES_PASSWORD = ''
else:
    POSTGRES_HOST = get_env_var('POSTGRES_HOST')
    POSTGRES_DB = get_env_var('POSTGRES_DB')
    POSTGRES_USER = get_env_var('POSTGRES_USER')
    POSTGRES_PASSWORD = get_env_var('POSTGRES_PASSWORD')

REPORTEK_DOMAIN = get_env_var('REPORTEK_DOMAIN')
REPORTEK_USE_TLS = get_bool_env_var('REPORTEK_USE_TLS')

TUSD_UPLOADS_DIR = get_env_var('TUSD_UPLOADS_DIR')
ALLOWED_UPLOADS_ARCHIVE_EXTENSIONS = split_env_var('ALLOWED_UPLOADS_ARCHIVE_EXTENSIONS')
ALLOWED_UPLOADS_EXTENSIONS = split_env_var('ALLOWED_UPLOADS_EXTENSIONS')

# QA
QA_DEFAULT_XMLRPC_URI = get_env_var('QA_DEFAULT_XMLRPC_URI')

# ROD
ROD_ROOT_URL = 'http://rod.eionet.europa.eu'

# Toggles preservation of archive paths in names of unpacked files,
# i.e. 'dir1/dir2/file.xml' becomes 'dir1_dir2_file.xml'.
# This provides overwrite protection for cases where the archive
# contains files with the same name in several directories.
ARCHIVE_PATH_PREFIX = get_bool_env_var('ARCHIVE_PATH_PREFIX', 'yes')

SECRET_KEY = get_env_var('SECRET_KEY')

DEBUG = get_bool_env_var('DEBUG', 'no')

ALLOWED_HOSTS = split_env_var('ALLOWED_HOSTS')


# https://django-guardian.readthedocs.io/en/stable/userguide/custom-user-model.html#custom-user-model
GUARDIAN_MONKEY_PATCH = False


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
    'guardian',
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
            ROOT_DIR / 'templates',
        ],
        'APP_DIRS': False,
        'OPTIONS': {
            # everything under our template dir is a jinja template
            'match_extension': None,
            'extensions': JINJA_DEFAULT_EXTENSIONS + [
                'webpack_loader.contrib.jinja2ext.WebpackExtension',
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


AUTH_USER_MODEL = 'core.ReportekUser'

AUTH_LDAP_SERVER_URI = get_env_var('LDAP_URI')

AUTH_LDAP_CONNECTION_OPTIONS = {
    ldap.OPT_REFERRALS: 0
}

AUTH_LDAP_BIND_DN = get_env_var('LDAP_BIND_DN')
AUTH_LDAP_BIND_PASSWORD = get_env_var('LDAP_BIND_PASSWORD')
AUTH_LDAP_USER_DN_TEMPLATE = get_env_var('LDAP_USER_DN_TEMPLATE')

AUTH_LDAP_GROUP_SEARCH = LDAPSearch(
    get_env_var('LDAP_ROLES_DN'),
    ldap.SCOPE_SUBTREE,
    '(objectClass=groupOfUniqueNames)'
)
AUTH_LDAP_GROUP_TYPE = NestedGroupOfUniqueNamesType(name_attr='cn')
AUTH_LDAP_REQUIRE_GROUP = get_env_var('LDAP_ROLES_DN')

AUTH_LDAP_ALWAYS_UPDATE_USER = True

AUTH_LDAP_FIND_GROUP_PERMS = True

AUTH_LDAP_CACHE_GROUPS = False
# AUTH_LDAP_GROUP_CACHE_TIMEOUT = 300

AUTH_LDAP_USER_ATTR_MAP = {
    'first_name': 'givenName',
    'last_name': 'sn',
    'email': 'mail'
}

AUTHENTICATION_BACKENDS = [
    'django_auth_ldap.backend.LDAPBackend',
    'django.contrib.auth.backends.ModelBackend',
    'guardian.backends.ObjectPermissionBackend',
]

ANONYMOUS_USER_NAME = 'anonymous'

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

TIME_ZONE = get_env_var('REPORTEK_TZ', 'UTC')

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

STATIC_ROOT = PARENT_DIR / 'static'
STATIC_URL = '/static/'

MEDIA_ROOT = PARENT_DIR / 'uploads'
MEDIA_URL = '/files/'

PROTECTED_ROOT = PARENT_DIR / 'protected_uploads'
PROTECTED_URL = '/protected-files/'

# TODO: this part should be synchronized with Webpack
# (see /frontend/config/conf.js)
_WEBPACK_DIST_DIR = ROOT_DIR / 'frontend' / 'dist'

# TODO: enable this only in production. (this is just a hack
# because the staticfiles app breaks if the directory doesn't exist.)
_WEBPACK_BUILD_DIR = _WEBPACK_DIST_DIR / 'build'
if _WEBPACK_BUILD_DIR.is_dir():
    STATICFILES_DIRS = (
        _WEBPACK_BUILD_DIR,
    )

WEBPACK_LOADER = {
    'DEFAULT': {
        'BUNDLE_DIR_NAME': '',
        'STATS_FILE': _WEBPACK_DIST_DIR / 'stats.json',
    },
}


FIXTURE_DIRS = [
    ROOT_DIR / 'data' / 'fixtures'
]


# Celery
CELERY_BROKER_HOST = get_env_var('RABBITMQ_HOST')
CELERY_BROKER_VHOST = get_env_var('RABBITMQ_DEFAULT_VHOST')
CELERY_BROKER_USER = get_env_var('RABBITMQ_DEFAULT_USER')
CELERY_BROKER_PWD = get_env_var('RABBITMQ_DEFAULT_PASS')
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
            'level': get_env_var('DJANGO_LOG_LEVEL', 'INFO'),
        },
        'django_auth_ldap': {
            'handlers': ['console'],
            'level': get_env_var('LDAP_LOG_LEVEL', 'INFO'),
        },
        'reportek.workflows': {
            'handlers': ['console'],
            'level': get_env_var('DJANGO_LOG_LEVEL', 'INFO'),
        },
        'reportek.perms': {
            'handlers': ['console'],
            'level': get_env_var('PERMS_LOG_LEVEL', 'INFO'),
        },
        'reportek.qa': {
            'handlers': ['console'],
            'level': get_env_var('DJANGO_LOG_LEVEL', 'INFO'),
        },
        'reportek.tasks': {
            'handlers': ['console'],
            'level': get_env_var('DJANGO_LOG_LEVEL', 'INFO'),
        },
    },
}