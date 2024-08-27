
from decimal import Decimal
from pathlib import Path
import os
from typing import Any, Dict, Tuple


DEBUG = False
TESTING = True

DEFAULT_EMAIL = 'webmaster@example.com'
DEFAULT_PHONE = '818 555 1234'
SITE_DOMAIN = 'localhost'
SITE_NAME = "Animal3"
SITE_ROOT = Path(__file__).parents[1]

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

# Time/date
USE_TZ = True
TIME_ZONE = 'Pacific/Auckland'
