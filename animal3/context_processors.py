"""
A set of request processors that return dictionaries to be merged into a
template context.
"""

from typing import Any, Dict

from django.conf import settings
from django.http import HttpRequest
from django.utils.html import escape
from django.utils.timezone import now


def constants(request: HttpRequest) -> Dict[str, Any]:
    """
    Adds various constants every template's context
    """
    copyright_ = now().strftime(settings.META_COPYRIGHT)
    return {
        'DEFAULT_EMAIL': escape(settings.DEFAULT_EMAIL),
        'DEFAULT_PHONE': escape(settings.DEFAULT_PHONE),
        'SITE_NAME': escape(settings.SITE_NAME),
        'META_COPYRIGHT': escape(copyright_),
        'META_DESCRIPTION': escape(settings.META_DESCRIPTION),
        'META_KEYWORDS': escape(settings.META_KEYWORDS),
        'META_TITLE': escape(settings.META_TITLE),
    }
