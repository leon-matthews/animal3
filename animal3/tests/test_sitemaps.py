
import datetime
from typing import List

from django.contrib.sitemaps import Sitemap
from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase

from animal3.utils.testing import sitemap_get_urls

from ..sitemaps import AgingMixin, SitemapWrapper


class AgingSitemap(AgingMixin, Sitemap):
    protocol = 'http'
    YEARS = 2

    def __init__(self) -> None:
        # Override self.data so that our tests don't break tomorrow
        super().__init__()
        self.today = datetime.date(2022, 10, 7)

    def items(self) -> List[datetime.datetime]:
        now = datetime.datetime(2022, 10, 7)
        datetimes = []
        for _ in range(10):
            datetimes.append(now)
            now -= datetime.timedelta(days=100)
        return datetimes

    def lastmod(self, date: datetime.datetime) -> datetime.datetime:
        return date

    def location(self, date: datetime.datetime) -> str:
        return f"/{date.strftime('%Y-%m-%d')}/"


class AgingSitemapError(AgingSitemap):
    def lastmod(self, date: datetime.datetime) -> datetime.datetime:
        return None                                         # type: ignore[return-value]


class TinyAlphabetSitemap(Sitemap):
    protocol = 'http'

    def items(self) -> List[str]:
        return list("abc")

    def location(self, obj: str) -> str:
        return f"/{obj}/"


class TinyNumbersSitemap(Sitemap):
    protocol = 'http'

    def items(self) -> List[int]:
        return list(range(1, 4))

    def location(self, obj: int) -> str:
        return f"/{obj}/"


class AgingMixinTest(SimpleTestCase):
    def test_priorities(self) -> None:
        urls = sitemap_get_urls(AgingSitemap())
        priorities = [(url['location'], url['priority']) for url in urls]
        expected = [
            ('http://testserver/2022-10-07/', '1.0'),
            ('http://testserver/2022-06-29/', '0.86'),
            ('http://testserver/2022-03-21/', '0.73'),
            ('http://testserver/2021-12-11/', '0.59'),
            ('http://testserver/2021-09-02/', '0.45'),
            ('http://testserver/2021-05-25/', '0.32'),
            ('http://testserver/2021-02-14/', '0.18'),
            ('http://testserver/2020-11-06/', '0.1'),
            ('http://testserver/2020-07-29/', '0.1'),
            ('http://testserver/2020-04-20/', '0.1')
        ]
        self.assertEqual(priorities, expected)

    def test_no_lastmod_method(self) -> None:
        message = r"^Sitemap must provide a lastmod\(\) method that returns a datetime.$"
        with self.assertRaisesRegex(ImproperlyConfigured, message):
            sitemap_get_urls(AgingSitemapError())


class SitemapWrapperTest(SimpleTestCase):
    def test_sitemap_wrapper(self) -> None:
        wrapper = SitemapWrapper(TinyAlphabetSitemap, TinyNumbersSitemap)
        urls = sitemap_get_urls(wrapper)
        locations = [url['location'] for url in urls]
        expected = [
            'http://testserver/a/',
            'http://testserver/b/',
            'http://testserver/c/',
            'http://testserver/1/',
            'http://testserver/2/',
            'http://testserver/3/',
        ]
        self.assertEqual(locations, expected)
