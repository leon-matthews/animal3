
import json
from typing import Any, Dict, List

from django.contrib.sitemaps import Sitemap
from django.http import HttpResponse
from django.test import SimpleTestCase

from ..testing import (
    FakeRequestResponse,
    json_unserialise,
    multiline,
    multiline_strip,
    sitemap_get_urls,
)


class FakeRequestResponseTest(SimpleTestCase):
    def test_empty(self) -> None:
        response = FakeRequestResponse()
        self.assertEqual(response.content, b'')
        self.assertEqual(response.json(), {})
        self.assertEqual(response.text, '')

        try:
            response.raise_for_status()
        except Exception:                                   # pragma: no cover
            self.fail('No exception should have been raised')

    def test_binary(self) -> None:
        response = FakeRequestResponse(content=b'ABC')
        self.assertEqual(response.content, b'ABC')

    def test_json(self) -> None:
        veges = ['apple', 'bannaa', 'carrot']
        response = FakeRequestResponse(json=veges)
        self.assertEqual(response.json(), veges)

    def test_text(self) -> None:
        response = FakeRequestResponse(text='ABC')
        self.assertEqual(response.text, 'ABC')


class JsonUnserialiseTest(SimpleTestCase):
    def test_empty(self) -> None:
        response = HttpResponse()
        with self.assertRaises(json.decoder.JSONDecodeError):
            json_unserialise(response)

    def test_html(self) -> None:
        response = HttpResponse(b'<html></html>')
        with self.assertRaises(json.decoder.JSONDecodeError):
            json_unserialise(response)

    def test_unserialise_list(self) -> None:
        response = HttpResponse(b'[true, 3, "pink"]')
        data = json_unserialise(response)
        self.assertEqual(data, [True, 3, 'pink'])

    def test_unserialise_mapping(self) -> None:
        response = HttpResponse(
            b'{"firstName": "John", "lastName": "Smith", "isAlive": true, "age": 87}'
        )
        data = json_unserialise(response)
        expected = {
            'firstName': 'John',
            'lastName': 'Smith',
            'isAlive': True,
            'age': 87,
        }
        self.assertEqual(data, expected)


class MultilineStripTest(SimpleTestCase):
    example = """
        This is an

                indented
            line here.
    """

    def test_multiline_strip(self) -> None:
        string = multiline_strip(self.example)
        expected = (
            "This is an\n"
            "indented\n"
            "line here."
        )
        self.assertEqual(string, expected)

    def test_multiline_strip_keep_blank(self) -> None:
        string = multiline_strip(self.example, keep_blank=True)
        expected = (
            "This is an\n"
            "\n"
            "indented\n"
            "line here."
        )
        self.assertEqual(string, expected)


class MultilineTest(SimpleTestCase):
    def test_multiline(self) -> None:
        string = multiline("""
            This is an indented
            line here.
        """)
        expected = (
            "This is an indented\n"
            "line here."
        )
        self.assertEqual(string, expected)


class MinimalSitemap(Sitemap):
    """
    Could be smaller.

    If your item objects have a `get_absolute_url()` method you can avoid
    having to define `location`.
    """
    protocol = 'http'

    def items(self) -> List[int]:
        return list(range(1, 6))

    def location(self, obj: int) -> str:
        return f"/{obj}/"


class SitemapGetUrlsTest(SimpleTestCase):
    urls: List[Dict[str, Any]]

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.urls = sitemap_get_urls(MinimalSitemap())

    def test_shape(self) -> None:
        self.assertIsInstance(self.urls, list)
        self.assertEqual(len(self.urls), 5)
        for url in self.urls:
            self.assertIsInstance(url, dict)
            self.assertEqual(len(url), 6)

    def test_first(self) -> None:
        expected = {
            'item': 1,
            'location': 'http://testserver/1/',
            'lastmod': None,
            'changefreq': None,
            'priority': '',
            'alternates': [],
        }
        self.assertEqual(self.urls[0], expected)

    def test_items(self) -> None:
        items = [url['item'] for url in self.urls]
        self.assertEqual(items, [1, 2, 3, 4, 5])

    def test_locations(self) -> None:
        locations = [url['location'] for url in self.urls]
        expected = [
            'http://testserver/1/',
            'http://testserver/2/',
            'http://testserver/3/',
            'http://testserver/4/',
            'http://testserver/5/',
        ]
        self.assertEqual(locations, expected)
