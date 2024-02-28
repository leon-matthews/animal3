
from typing import Any, Callable

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, MiddlewareNotUsed
from django.http import HttpRequest, HttpResponseRedirect
from django.http.response import HttpResponseBase
from django.utils.cache import add_never_cache_headers

from animal3.utils.algorithms import compare_digests, create_digest


def append_slash(get_response: Callable) -> Any:
    """
    Append a trailing slash to 404 requests without one, then redirect.

    Simpler behaviour than Django's built-in CommonMiddleware and without
    any of its non-slash related functionality.
    """
    # Prompt to uninstall this middleware if settings incompatible (avoid
    # completely the performance hit of running this middleware).
    if not settings.APPEND_SLASH:
        message = (
            "{}.{} middleware is installed but APPEND_SLASH is False."
            " Uninstall instead.".format(__name__, append_slash.__name__))
        raise ImproperlyConfigured(message)

    def middleware(request: HttpRequest) -> HttpResponseBase:
        response = get_response(request)
        assert isinstance(response, HttpResponseBase), f"Bad response type: {response!r}"

        # Ignore uninteresting requests and responses.
        # We can't preserve data from a POST, so a redirect is not useful.
        if (
            response.status_code != 404
            or request.path.endswith('/')
            or request.method == 'POST'
        ):
            return response

        # Actually append the slash
        url = request.build_absolute_uri(request.path + '/')

        # Append any query string, then redirect!
        if request.META.get('QUERY_STRING'):
            url += '?' + request.META['QUERY_STRING']
        return HttpResponseRedirect(url)

    return middleware


def forbid_client_side_caching(get_response: Callable) -> Any:
    """
    Middleware to forbid client-side caching of by default.

    This can be overridden per-view level for functional views::

        from django.views.decorators.cache import cache_control

        @cache_control(max_age=3600, public=True)
        def price_list_json(request):
            ...

    And class-based views::

        from animal3.cbv.mixins AllowCachingMixin

        class PriceListJSON(AllowCachingMixin, ListView):
            ...

    """
    def middleware(request: HttpRequest) -> HttpResponseBase:
        response = get_response(request)
        assert isinstance(response, HttpResponseBase), f"Bad response type: {response!r}"

        if not response.has_header('Cache-Control'):
            add_never_cache_headers(response)
        return response

    return middleware


class StagingPasswordMiddleware:
    """
    Optionally lock down staging site with password.

    Uninstalls itself if the STAGING_PASSWORD setting is none.

    Adds the attribute 'staging_password_required' to the request so that
    you may conditionally include the overlay snippet.

        {% if request.staging_password_required %}
            {% include "common/snippets/staging_pasword_overlay.html" %}
        {% endif %}

    """
    allowed_urls = ('/', '/staging-password/')
    session_name = 'staging-password'

    def __init__(self, get_response: Callable):
        """
        Initialisation.

        Raises:
            MiddlewareNotUsed:
                If not running on staging, or if STAGING_PASSWORD is none,
                raise exception to cause middleware to uninstall itself.

        """
        # Uninstall middleware if not needed
        if settings.TESTING:
            raise MiddlewareNotUsed("Running unit tests")

        self.password = settings.STAGING_PASSWORD
        if not self.password:
            raise MiddlewareNotUsed("No password set")

        if settings.DEBUG:
            raise MiddlewareNotUsed("Site in debug mode")

        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponseBase:
        """
        Wrap request/response view.

        Note that because the middleware has not been uninstalled, we can
        assume that it is needed.
        """
        # Skip media and static files
        if (request.path.startswith(settings.MEDIA_URL)
                or request.path.startswith(settings.STATIC_URL)):
            return self.get_response(request)               # type: ignore[no-any-return]

        # Check submitted password
        passwords_match = False
        submitted = request.session.get(self.session_name)
        if submitted:
            assert isinstance(settings.STAGING_PASSWORD, str)
            expected = create_digest(settings.STAGING_PASSWORD, 32)
            passwords_match = compare_digests(submitted, expected)

        # Force homepage & show password form
        if not passwords_match:
            request.staging_password_required = True        # type: ignore[attr-defined]
            if request.path not in self.allowed_urls:
                return HttpResponseRedirect('/')

        # Resume normal service
        response = self.get_response(request)
        return response                                     # type: ignore[no-any-return]
