
from collections import OrderedDict
import re
from typing import Any, List, Mapping
from urllib.parse import urlencode, urljoin, urlsplit, urlunsplit

from django.conf import settings

from .text import html_attributes


def extract_base(url: str) -> str:
    """
    Extract (and join) just the schema and hostname from the given URL.

        >>> extract_base('https://example.com/some/path/here.jpg')
        'https://example.com'

    Args:
        Full URL.

    Raises:
        ValueError:
            If url is not valid.

    Returns:
        Base url.
    """
    parts = urlsplit(url)
    if not parts.scheme and not parts.netloc:
        raise ValueError(f"Given URL missing scheme: {url!r}")

    base = urlunsplit((parts.scheme, parts.netloc, '', '', ''))
    return base


def extract_hostname(url: str) -> str:
    """
    Extract just the hostname from the given URL.

        >>> extract_hostname("https://example.com/some/path.png")
        'example.com'

    Args:
        Full URL.

    Returns:
        Bare hostname.
    """
    parts = urlsplit(url)
    hostname = parts.netloc.partition(':')[0]               # Drop port number
    return hostname


def extract_path(
    url: str,
    *,
    drop_query: bool = True,
    drop_fragment: bool = False,
) -> str:
    """
    Extract just the absolute path from the given URL.

    Used to convert internal links pasted by users into their own website. Will
    raise an exception if link not for current site.

    Args:
        url:
            Full URL, eg. 'https://example.com/information/faq/'
        drop_query (bool):
            Delete any query string from URL.
        drop_fragment (bool):
            Delete fragment from URL.

    Raises:
        ValueError:
            If given URL does not appear to be for the current website.

    Returns:
        Absolute path, eg. '/information/faq/' or None if not local URL.
    """
    parts = urlsplit(url)
    path = parts.path
    query = parts.query if not drop_query else ''
    fragment = parts.fragment if not drop_fragment else ''
    url = urlunsplit(('', '', path, query, fragment))
    return url


def find_urls(string: str) -> List[str]:
    """
    Find absolute URLs embedded within a string.

    Slightly stricter semantics than a full URL validation, to avoid
    picking up parts of an english sentence as parts of the URL.

    For example, if our input said that https://example.com/docs/, was where
    we kept the documentation, we probably didn't intend that the trailing comma
    be included - nor the 'space-was-space-where' that followed it - even though
    both commas and spaces are allowed in URLs.

    Args:
        string:
            String to search in.

    Returns:
        List of absolute URLs found, possibly empty.
    """
    regex = (
        r"https?://"                    # Schema
        r"[-a-z0-9+&@#/%=~_|$!:,.;]*"   # Hostname and path
        r"[a-z0-9+&@#/%=~_|$]"          # Last character
    )
    matches = re.findall(regex, string, re.IGNORECASE)
    return matches


def hostname_link(url: str, **attributes: Any) -> str:
    """
    Shorten link text by using just the hostname as the link text.

        >>> hostname_link('https://example.com/find/me/a/river.html')
        '<a href="https://example.com/find/me/a/river.html">example.com</a>'

    Args:
        url:
            Full URL to resource
        attributes:
            All keyword arguments are treated as attributes to add to the
            anchor tag. Because 'class' is a reserved keyword in Python you
            should use the dictionary syntax, ie. **{'class': 'button'}.

    Returns:
        String.
    """
    # Parse URL
    if '://' not in url:
        url = f'http://{url}'
    parts = urlsplit(url)
    cleaned = urlunsplit(parts)

    # Build attributes
    attrs = ''
    if attributes:
        attrs = f' {html_attributes(attributes)}'

    # Hostname
    hostname = parts.netloc.lower()
    www = 'www.'
    if hostname.startswith(www):
        hostname = hostname[len(www):]

    # Put it all together
    anchor = f'<a href="{cleaned}"{attrs}>{hostname}</a>'
    return anchor


def is_current_site(hostname: str) -> bool:
    """
    Does the given hostname refer to the current site?

    Args:
        hostname:
            Hostname to check against, eg. 'example.com'

    Returns:
        True if the hostname matches currently running site.
    """
    if '/' in hostname or ':' in hostname:
        raise ValueError(f"Unexpected character found in hostname: {hostname!r}")
    hostname = hostname.lower()

    if hostname == settings.SITE_DOMAIN:
        return True

    for allowed in settings.ALLOWED_HOSTS:
        if hostname.endswith(allowed):
            return True

    return False


def is_path_only(url: str, allow_relative: bool = False) -> bool:
    """
    Is the given URL just a path, ie. without host or schema?

        >>> is_path_only('/some/url/here.jpg')
        True
        >>> is_path_only('//example.com/some/url/here.png')
        False

    Args:
        url:
            URL to check.
        allow_relative:
            Set True to allow relative paths as well as absolute.

    Returns:
        True if no hostname or schema attached.
    """
    parts = urlsplit(url)

    if parts.scheme or parts.netloc:
        return False

    if not allow_relative and not parts.path.startswith('/'):
        return False

    return True


def join_url(base: str, path: str) -> str:
    """
    Join a domain and path parts of a URL together.

    Similar to `urllib.parse.urljoin()`, but adds in a default schema
    if one not provided.

        # Relative paths joined
        >>> join_url('https://example.com', 'products/index.html')
        'https://example.com/products/index.html'

        # Schema added automatically
        >>> join_url('example.com/about/', 'henry.html')
        'http://example.com/about/henry.html'

        # Absolute paths change things up
        >>> join_url('example.com/about/', '/henry.html')
        'http://example.com/henry.html'

    Args:
        base:
            Base URL. May contain a schema and an existing path.
        path:
            File name or full path.

    Returns:
        Full URL.
    """
    if '//' not in base:
        base = 'http://' + base
    return urljoin(base, path)


def query_string(params: Mapping[str, Any]) -> str:
    """
    Combine a base URL with a mapping of parameter values.

        >>> query_string({})
        ''
        >>> query_string({'q': 'the holy grail', 'id': 3})
        '?id=3&q=the+holy+grail'

    Parameter keys are sorted. Parameters with a value of `None` are skipped
    entirely. Note also that the initial '?' is present, if required.
    """
    keys = params.keys()
    mapping = OrderedDict()
    for key in sorted(keys):
        value = params[key]
        if value is not None:
            mapping[key] = value
    query_string = urlencode(mapping)
    if query_string:
        query_string = '?' + query_string
    return query_string
