
from unittest import TestCase

from ..html import AttributesParser, find_csrftoken, html2text
from ..testing import multiline

from . import DATA_FOLDER


def read_file(name: str) -> str:
    path = DATA_FOLDER / name
    with open(path, 'rt', encoding='utf-8') as textio:
        contents = textio.read()
    return contents


class AttributesParserTest(TestCase):
    message: str

    @classmethod
    def setUpClass(cls) -> None:
        cls.message = read_file('message.html')

    def test_found(self) -> None:
        parser = AttributesParser('a')
        parser.feed(self.message)
        attrs = parser.get_attributes()
        expected = [
            {'href': 'http://localhost:8000/'},
            {'href': '/local/link/ignored.html'},
        ]
        self.assertEqual(attrs, expected)

    def test_no_attributes(self) -> None:
        """
        Tags found have no attributes.
        """
        # There are three <tr> tags...
        parser = AttributesParser('tr')
        parser.feed(self.message)
        # ...none of which have any attributes.
        self.assertEqual(parser.get_attributes(), [{}, {}, {}])

    def test_not_found(self) -> None:
        """
        No 'banana' tag defined in HTML yet?
        """
        parser = AttributesParser('banana')
        parser.feed(self.message)
        attrs = parser.get_attributes()
        self.assertEqual(attrs, [])

    def test_sans_value(self) -> None:
        """
        It is legal to have HTML attributes without a value.
        """
        parser = AttributesParser('div')
        parser.feed(self.message)
        attrs = parser.get_attributes()
        expected = [{'data-target': None}]
        self.assertEqual(attrs, expected)


class FindCSRFTokenTest(TestCase):
    def test_find_csrftoken(self) -> None:
        html = read_file('login.html')
        csrf_token = find_csrftoken(html)
        self.assertEqual(
            csrf_token,
            'Wb9lQzbuQ3hMqGZ1CWl1Lpg70p447wnSRYmb91C7RvfSpTWX33vm4u4x2sLkTddd',
        )

    def test_not_find_csrftoken(self) -> None:
        html = read_file('simple.html')
        csrf_token = find_csrftoken(html)
        self.assertEqual(csrf_token, None)


class Html2TextSimpleTest(TestCase):
    """
    Translate very simple HTML document.
    """
    def test_html2text(self) -> None:
        html = read_file('simple.html')
        text = html2text(html)
        expected = multiline("""
            Hello world!
        """)
        self.assertEqual(text, expected)

    def test_html2text_allow_head(self) -> None:
        html = read_file('simple.html')
        text = html2text(html, skip_head=False)
        expected = multiline("""
            This is a title

            Hello world!
        """)
        self.assertEqual(text, expected)


class Html2TextMessageTest(TestCase):
    def test_html2text_simple(self) -> None:
        html = read_file('message.html')
        text = html2text(html, maxlen=77)
        expected = multiline("""
            http://localhost:8000/

            Name:  John Smith
            Email: johns@example.com
            Phone: 021 555 1234

            Message: If you are using a custom AdminSite, it is common to import all of
            the ModelAdmin subclasses into your code and register them to the custom
            AdminSite. In that case, in order to disable auto-discovery, you should put
            'django.contrib.admin.apps.SimpleAdminConfig' instead of
            'django.contrib.admin' in your INSTALLED_APPS setting.

            Mailing list: True
        """)
        self.assertEqual(text, expected)
