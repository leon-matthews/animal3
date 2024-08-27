
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
MIGRATE = False
ROOT_URLCONF = 'tests.urls'

SECRET_KEY = "fake-key"
INSTALLED_APPS = [
    # ~ 'django.contrib.admin',
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
