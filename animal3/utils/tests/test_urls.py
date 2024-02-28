
from typing import Any, Mapping
from unittest import TestCase

from django.conf import settings

from animal3.utils.testing import DocTestLoader, multiline

from .. import urls
from ..urls import (
    extract_base,
    extract_hostname,
    extract_path,
    find_urls,
    hostname_link,
    is_current_site,
    is_path_only,
    join_url,
    query_string,
)


class DocTests(TestCase, metaclass=DocTestLoader, test_module=urls):
    pass


class ExtractBaseTest(TestCase):
    def test_extract_base(self) -> None:
        """
        Various valid schemes
        """
        self.assertEqual(
            extract_base("https://example.com/some/path/here.jpg"),
            'https://example.com'
        )

        self.assertEqual(
            extract_base("http://example.com/some/path/"),
            'http://example.com'
        )

        self.assertEqual(
            extract_base("//example.com"),
            '//example.com'
        )

    def test_missing_scheme_error(self) -> None:
        message = "Given URL missing scheme: 'example.com/some/path/here.jpg'"
        with self.assertRaisesRegex(ValueError, message):
            extract_base("example.com/some/path/here.jpg")


class ExtractHostnameTest(TestCase):
    def test_extract_hostname(self) -> None:
        self.assertEqual(
            extract_hostname("https://example.com/some/path.png"),
            'example.com')

    def test_drop_port_number(self) -> None:
        self.assertEqual(
            extract_hostname("https://localhost:8000/"),
            'localhost')


class ExtractAbsolutePathTest(TestCase):
    def test_extract_path(self) -> None:
        self.assertEqual(
            extract_path("https://example.com/some/path/here.jpg"),
            '/some/path/here.jpg')
        self.assertEqual(
            extract_path("http://example.com/some/path/"),
            '/some/path/')

    def test_bare_path(self) -> None:
        self.assertEqual(
            extract_path("/some/path.png"),
            '/some/path.png')

    def test_keep_fragment(self) -> None:
        """
        Drop schema, hostname, and query - but keep fragment by default.
        """
        url = 'https://localhost/papers/refs.html?active=1#hot'
        self.assertEqual(
            extract_path(url), '/papers/refs.html#hot')

    def test_ignore_port_number(self) -> None:
        url = 'https://localhost:8000/papers/refs.html'
        self.assertEqual(
            extract_path(url), '/papers/refs.html')

    def test_path_options(self) -> None:
        """
        Use options to keep or drop query and fragments.
        """
        url = 'https://localhost/papers/refs.html?active=1#hot'
        self.assertEqual(
            extract_path(url, drop_query=True, drop_fragment=True),
            '/papers/refs.html')
        self.assertEqual(
            extract_path(url, drop_query=True, drop_fragment=False),
            '/papers/refs.html#hot')
        self.assertEqual(
            extract_path(url, drop_query=False, drop_fragment=True),
            '/papers/refs.html?active=1')
        self.assertEqual(
            extract_path(url, drop_query=False, drop_fragment=False),
            '/papers/refs.html?active=1#hot')


class FindURLsTest(TestCase):
    def test_find_urls_empty(self) -> None:
        urls = find_urls("")
        self.assertEqual(urls, [])

    def test_find_urls_html(self) -> None:
        string = multiline("""
            <p>
            For example, if our input said that
            <a href="https://example.com/docs/" title="Documentation">docs</a>,
            was where we kept the documentation, we probably <em>didn't</em>
            intend that the trailing comma be included.
            </p>
        """)
        urls = find_urls(string)
        self.assertEqual(urls, ['https://example.com/docs/'])

    def test_find_urls_paragraph(self) -> None:
        string = multiline("""
            For example, if our input said that https://example.com/docs/, was where
            we kept the documentation, we probably didn't intend that the trailing
            comma be included
        """)
        urls = find_urls(string)
        self.assertEqual(urls, ['https://example.com/docs/'])

    def test_find_urls_multiple(self) -> None:
        string = multiline("""
            Then again we might use multiple URLs for our documentation.
            Say, https://example.com/current/docs/, http://example.com/v1/docs/,
            and http://example.com/v2/docs/.
        """)
        urls = find_urls(string)
        expected = [
            'https://example.com/current/docs/',
            'http://example.com/v1/docs/',
            'http://example.com/v2/docs/',
        ]
        self.assertEqual(urls, expected)


class HostnameLinkTest(TestCase):
    def test_hostname_link_attributes(self) -> None:
        """
        Add custom attributes to anchor tag.
        """
        self.assertEqual(
            hostname_link('example.com', target='_blank'),
            '<a href="http://example.com" target="_blank">example.com</a>')

        # Note that 'class' is a Python reserved keyword, so must be passed as below.
        attrs = {'class': 'button', 'target': '_blank'}
        self.assertEqual(
            hostname_link('example.com', **attrs),
            '<a href="http://example.com" class="button" target="_blank">example.com</a>')

    def test_hostname_link_case_sensitive(self) -> None:
        """
        Preserve case in link, but always show hostname as lower-case.
        """
        self.assertEqual(
            hostname_link('HTTP://EXAMPLE.COM'),
            '<a href="http://EXAMPLE.COM">example.com</a>')

    def test_hostname_link_path_fragments_query(self) -> None:
        """
        The path and other parts should be preserved, but not shown in anchor text.
        """
        self.assertEqual(
            hostname_link('example.com/some/long/path.jpg'),
            '<a href="http://example.com/some/long/path.jpg">example.com</a>')
        self.assertEqual(
            hostname_link('example.com/some/path.html#anchor?var=one&var2=two'),
            ('<a href="http://example.com/some/path.html#anchor?'
             'var=one&var2=two">example.com</a>'),
        )

    def test_hostname_link_schema(self) -> None:
        """
        Try various values for the input schema.
        """
        self.assertEqual(
            hostname_link('example.com'),
            '<a href="http://example.com">example.com</a>')
        self.assertEqual(
            hostname_link('http://example.com'),
            '<a href="http://example.com">example.com</a>')
        self.assertEqual(
            hostname_link('https://example.com'),
            '<a href="https://example.com">example.com</a>')

    def test_hostname_link_www(self) -> None:
        """
        Drop the 'www' prefix from just the anchor text, if present.
        """
        self.assertEqual(
            hostname_link('https://www.example.com/index.html'),
            '<a href="https://www.example.com/index.html">example.com</a>')
        self.assertEqual(
            hostname_link('https://WWW.example.com/index.html'),
            '<a href="https://WWW.example.com/index.html">example.com</a>')


class IsCurrentSiteTest(TestCase):
    def test_is_current_site(self) -> None:
        self.assertTrue(is_current_site('localhost'))
        self.assertTrue(is_current_site('testserver'))

    def test_is_site_domain(self) -> None:
        self.assertTrue(is_current_site(settings.SITE_DOMAIN))

    def test_is_not_current_site(self) -> None:
        self.assertFalse(is_current_site('example.com'))

    def test_port_not_allowed(self) -> None:
        message = r"^Unexpected character found in hostname: 'localhost:8000'$"
        with self.assertRaisesRegex(ValueError, message):
            is_current_site('localhost:8000')

    def test_path_not_allowed(self) -> None:
        message = r"^Unexpected character found in hostname: 'example.com/'$"
        with self.assertRaisesRegex(ValueError, message):
            is_current_site('example.com/')


class IsPathOnlyTest(TestCase):
    def test_absolute_paths(self) -> None:
        self.assertTrue(is_path_only('/'))
        self.assertTrue(is_path_only('/index.html'))

    def test_relative_paths(self) -> None:
        self.assertFalse(is_path_only('relative/path.png'))
        self.assertTrue(is_path_only('relative/path.png', allow_relative=True))

    def test_full_urls(self) -> None:
        self.assertFalse(is_path_only('https://example.com/'))
        self.assertFalse(is_path_only('//example.com/'))


class JoinUrlTest(TestCase):
    def test_join_url_simple(self) -> None:
        self.assertEqual(
            join_url('example.com', ''),
            'http://example.com')

        self.assertEqual(
            join_url('example.com', 'index.html'),
            'http://example.com/index.html')

        self.assertEqual(
            join_url('http://example.com', 'index.html'),
            'http://example.com/index.html')

    def test_join_url_slashes(self) -> None:
        """
        Ensure that paths are handled nicely.
        """
        self.assertEqual(
            join_url('http://example.com/', '/search.html?q=corvid-19'),
            'http://example.com/search.html?q=corvid-19')


class QueryStringTest(TestCase):
    def test_empty(self) -> None:
        params: Mapping[str, Any] = {}
        expected = ''
        self.assertEqual(query_string(params), expected)

    def test_single(self) -> None:
        params = {'q': 'swordfish'}
        expected = '?q=swordfish'
        self.assertEqual(query_string(params), expected)

    def test_several_quoted(self) -> None:
        params = {'page': 1, 'q': 'AMD Ryzen 9 3950X', 'order_by': 'price'}
        expected = '?order_by=price&page=1&q=AMD+Ryzen+9+3950X'
        self.assertEqual(query_string(params), expected)

    def test_skip_none(self) -> None:
        params = {'d': None, 'g': None, 'e': None, 'c': 3, 'f': None, 'b': 2, 'a': 1}
        expected = '?a=1&b=2&c=3'
        self.assertEqual(query_string(params), expected)

    def test_sorted(self) -> None:
        params = {'d': 4, 'g': 7, 'e': 5, 'c': 3, 'f': 6, 'b': 2, 'a': 1}
        expected = '?a=1&b=2&c=3&d=4&e=5&f=6&g=7'
        self.assertEqual(query_string(params), expected)

    def test_quoting(self) -> None:
        params = {'url': 'https://example.com/images/wot.png'}
        expected = '?url=https%3A%2F%2Fexample.com%2Fimages%2Fwot.png'
        self.assertEqual(query_string(params), expected)
