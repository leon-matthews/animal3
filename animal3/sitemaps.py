
import datetime
from typing import Any, Callable, Dict, List, Optional, Type, Union

from django.apps import apps
from django.contrib.sitemaps import Sitemap
from django.core.exceptions import ImproperlyConfigured

from animal3.utils.text import make_slug

from .models import BaseModel


def build_sitemaps() -> Dict:
    """
    Build a site-wide 'sitemaps' dictionary from installed app configs.

    Runs the `get_sitemaps()` method, if defined, on each app config. Also
    prepends the app's label to the key.

    Returns: dict
    """
    sitemaps = {}
    for config in apps.get_app_configs():
        get_sitemaps = getattr(config, 'get_sitemaps', None)
        if get_sitemaps is not None:
            key = make_slug(str(config.verbose_name))
            sitemaps[key] = SitemapWrapper(*get_sitemaps())
    return sitemaps


class AgingMixin:
    """
    Provides a `priority()` method that decreases object's priority as they age.

    Requires that a `lastmod()` method is provided that returns a
    `datetime.datetime` instance.

    Priority starts at 1.0 for a new entry then decreases to hit a minimum
    value of 0.1 after YEARS have elapsed.

    Attributes:
        YEARS (int):
            How many years before our priority hits 0.1

    """
    lastmod: Callable
    YEARS = 4

    def __init__(self) -> None:
        super().__init__()
        self.max_age = self.YEARS * 365.2425
        self.today = datetime.date.today()

    def priority(self, obj: BaseModel) -> float:
        """
        Calculate priority of object given its age in days.

        If age is equal or greater than YEARS its priority is always 0.1

        Returns:
            Value between 1.0 and 0.1, rounded to two decimal places.
        """
        # Age in days
        try:
            lastmod = self.lastmod(obj)
            age = (self.today - lastmod.date()).days
        except AttributeError:
            message = (
                "Sitemap must provide a lastmod() method that returns a datetime."
            )
            raise ImproperlyConfigured(message) from None

        # Calculate priority
        priority = float(max(0.1, 1.0 - (age / self.max_age)))
        return round(priority, 2)


class SitemapWrapper(Sitemap):
    """
    Combines various Sitemap classes together.
    """
    def __init__(self, *sitemaps: Type[Sitemap]):
        self.sitemaps = sitemaps

    def get_urls(
        self,
        page: Union[int, str] = 1,
        site: Optional[Any] = None,
        protocol: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Instantiate all of the Sitemap classes and combine their data.
        """
        urls = []
        for cls in self.sitemaps:
            sitemap = cls()
            urls.extend(sitemap.get_urls(page, site, protocol))
        return urls
