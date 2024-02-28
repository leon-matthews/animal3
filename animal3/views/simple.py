
import os.path
from typing import Any, Callable, Optional

from django.core.exceptions import ImproperlyConfigured
from django.utils.decorators import classonlymethod
from django.views.generic import RedirectView, TemplateView


__all__ = (
    'redirect',
    'RedirectPrefixView',
    'template',
)


def redirect(pattern_name: str, permanent: bool = False) -> Callable:
    """
    Redirect to a named URL.

    For example, in an app's ``urls`` module::

        urlpatterns += [
            path('some/path/', redirect('contacts:index'))
        ]

    Args:
        pattern_name:
            Name of URL pattern to redirect to.
        permanent:
            Set to True to use a 301 redirect, 302 otherwise.

    Returns:
        View function.
    """
    return RedirectView.as_view(pattern_name=pattern_name, permanent=permanent)


class RedirectPrefixView(RedirectView):
    """
    Redirect all paths under given prefix, to ease renaming applications.

    Should be used in the root URL patterns module, as Django truncates
    paths before passing them to patterns imported via the `include()` function.

    In this example, everything to the left of the <path:path> is replaced
    with the given prefix. ie. '/old/url/here/' -> '/new/url/here/':

        path('old/<path:path>', RedirectPrefixView.as_view(prefix='/new')

    You may want to add a plain redirect to catch the root directory too:

        path('old/', RedirectView(url='/new/'))

    Attribute:
        prefix:
            Prefix to add to captured URL. A forward slash is forced to the
            beginning to avoid redirect loops.
    """
    prefix: Optional[str] = None

    @classonlymethod
    def as_view(cls, **initkwargs: Any) -> Callable:
        view = super().as_view(**initkwargs)
        if 'prefix' not in initkwargs or initkwargs['prefix'] is None:
            raise ImproperlyConfigured("Missing required 'prefix' argument")
        return view

    def get_redirect_url(self, *args: Any, **kwargs: Any) -> Optional[str]:
        """
        Figure out
        """
        try:
            path = kwargs['path']
        except KeyError:
            raise ImproperlyConfigured(
                f"No 'path' found in URL for {self.__class__.__name__}"
            )
        if path.startswith('/'):
            path = path[1:]

        assert isinstance(self.prefix, str)
        prefix = self.prefix
        if not prefix.startswith('/'):
            prefix = f"/{prefix}"

        url = os.path.join(prefix, path)
        return url


def template(template_name: str) -> Callable:
    return TemplateView.as_view(template_name=template_name)
