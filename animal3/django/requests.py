
from typing import Dict, Optional
from urllib.parse import urlsplit, urlunsplit

from django.conf import settings
from django.http import HttpRequest, QueryDict


def fake_request(
    *,
    hostname: Optional[str] = None,
    https: bool = True,
    port: Optional[int] = None,
) -> HttpRequest:
    """
    Build just enough of a request object to call `build_absolute_uri()`.

    Note that we have to use the site's canonical domain as we can't determine
    where and how it might be running.

    Useful to calculate full URLs when sending HTML emails in cron jobs where
    a proper request object is not available.

    Args:
        https:
            Use HTTPS for the URL's scheme.
        port:
            Override port number. Defaults to default value for `https` setting.
        server_name:
            Override server name. Use ``SITE_DOMAIN`` setting if not given.

    Returns:
        Bare-bones request object.
    """
    if hostname is None:
        hostname = settings.SITE_DOMAIN                     # type: ignore[misc]
    if port is None:
        port = 443 if https else 80
    assert isinstance(hostname, str)

    request = HttpRequest()
    if https:
        request._get_scheme = lambda: 'https'               # type: ignore[attr-defined]
    request.META['SERVER_NAME'] = hostname
    request.META['SERVER_PORT'] = port
    return request


def get_referrer(
    request: HttpRequest,
    drop_query: bool = True,
    drop_fragment: bool = False,
    default: str = '/'
) -> str:
    """
    Return last url visited by user, or the default if not found.

    For security, drop scheme and host from url and just the absolute path,
    and optionally the query and fragment.

    Args:
        request:
            Django Request object.
        drop_query (bool):
            Delete any query string from URL.
        drop_fragment (bool):
            Delete fragment from URL.
        default:
            URL to use if 'HTTP_REFERER' not found in request.

    Returns:
        The absolute path to the referring URL.
    """
    url = request.META.get('HTTP_REFERER')
    if url:
        parts = urlsplit(url)
        path = parts.path
        query = parts.query if not drop_query else ''
        fragment = parts.fragment if not drop_fragment else ''
        url = urlunsplit(('', '', path, query, fragment))
    else:
        url = default
    return str(url)


def querydict_from_dict(data: Dict[str, str], mutable: bool = False) -> QueryDict:
    """
    Return a new QueryDict with keys (may be repeated) from an iterable and
    values from value.
    """
    q = QueryDict('', mutable=True)

    for key in data:
        q.appendlist(key, data[key])

    if not mutable:
        q._mutable = False

    return q
