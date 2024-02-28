
from typing import Optional

from django.http import HttpRequest


def get_current_app(request: HttpRequest) -> Optional[str]:
    """
    Attempt to find the current app, the same way the url template tag does.

    In a template::

        {# URL for current app. instance #}
        {% url 'application:view' %}

    In a view function:

        # Default instance URL only :-(
        url = reverse('application:view')

        # Current instance URL :-)
        current_app = get_current_app(self.request)
        url = reverse('application:view', current_app=current_app)

    See:
        https://docs.djangoproject.com/en/stable/topics/http/urls/#topics-http-reversing-url-namespaces

    Returns:
        Name of current_app, or None if app instance feature not used.
    """
    try:
        current_app = request.current_app
    except AttributeError:
        try:
            current_app = request.resolver_match.namespace  # type:ignore[union-attr]
        except AttributeError:
            return None
    return str(current_app)
