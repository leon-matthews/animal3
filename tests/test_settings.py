
from decimal import Decimal
from pathlib import Path
import os
from typing import Any, Dict, List, Tuple


DEBUG = False
TESTING = True

DEFAULT_EMAIL = 'webmaster@example.com'
DEFAULT_PHONE = '818 555 1234'
SITE_DOMAIN = 'localhost'
SITE_NAME = "Animal3"
SITE_ROOT = Path(__file__).parents[1]
STATIC_ROOT = SITE_ROOT
SOURCE_ROOT = SITE_ROOT

ALLOWED_HOSTS = ('localhost',)
ALLOWED_ROOTS: Tuple[os.PathLike, ...]  = (
    SITE_ROOT,
)
META_COPYRIGHT = 'Copyright %Y, all rights reserved'
META_DESCRIPTION = ""
META_KEYWORDS = ""
META_TITLE = ""
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
LANGUAGE_CODE = 'en-gb'
LOGIN_URL = 'admin:login'
MIGRATE = False
ROOT_URLCONF = 'tests.urls'

SECRET_KEY = "fake-key"
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',
    'animal3'
]

# Databases
DATABASES = {
    'default': {
        'ATOMIC_REQUESTS': False,
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    },
}

# Dates
# https://docs.djangoproject.com/en/stable/ref/templates/builtins/#date
DATE_FORMAT = 'D N jS Y'
DATETIME_FORMAT = 'D j M Y g:iA e'
SHORT_DATE_FORMAT = 'j N Y'
SHORT_DATETIME_FORMAT = 'Y-m-d g:iA'
DATE_INPUT_FORMATS = [
    '%Y-%m-%d',     # 2019-02-23
    '%d %b %Y',     # 23 Feb 2019
    '%d %B %Y',     # 23 February 2019
    '%d/%m/%Y',     # 23/02/2019
    '%d/%m/%y',     # 23/02/19
]

# Middleware
MIDDLEWARE = [
    'animal3.middleware.common.append_slash',
    'animal3.middleware.common.forbid_client_side_caching',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'animal3.middleware.common.StagingPasswordMiddleware',
]

# Misc.
GST = Decimal('0.15')

# Pipeline
PIPELINE: Dict[str, Any] = {
    'COMPILERS': (),
    'CSS_COMPRESSOR': None,
    'DISABLE_WRAPPER': True,
    'JS_COMPRESSOR': None,
    'JAVASCRIPT': {},
    'PIPELINE_COLLECTOR_ENABLED': False,
    'SHOW_ERRORS_INLINE': False,
    'STYLESHEETS': {},
}

# Session
SESSION_ENGINE = "django.contrib.sessions.backends.cache"

# Templates
TEMPLATES: List[Dict[str, Any]] = [{
    'APP_DIRS': True,
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [SITE_ROOT / 'templates'],
    'OPTIONS': {
        'builtins': [
            'django.templatetags.static',
            'animal3.templatetags.animal3_builtins',
            'sorl.thumbnail.templatetags.thumbnail',
        ],
        'context_processors': [
            'animal3.context_processors.constants',
            'django.template.context_processors.debug',
            'django.template.context_processors.request',
            'django.template.context_processors.media',
            'django.contrib.auth.context_processors.auth',
            'django.contrib.messages.context_processors.messages',
        ],
    },
}]


# Time/date
USE_TZ = True
TIME_ZONE = 'Pacific/Auckland'
