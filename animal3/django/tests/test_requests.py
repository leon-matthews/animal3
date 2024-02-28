
from django.conf import settings
from django.http import HttpRequest, QueryDict
from django.template import Context, RequestContext, Template
from django.test import RequestFactory, SimpleTestCase

from ..requests import (
    get_referrer,
    fake_request,
    querydict_from_dict,
)


class FakeRequestTest(SimpleTestCase):
    def test_build_absolute_uri_defaults(self) -> None:
        request = fake_request()
        expected = f"https://{settings.SITE_DOMAIN}"
        self.assertEqual(request.build_absolute_uri(), expected)

    def test_build_absolute_uri_no_ssl(self) -> None:
        request = fake_request(https=False)
        expected = f"http://{settings.SITE_DOMAIN}"
        self.assertEqual(request.build_absolute_uri(), expected)

    def test_build_absolute_uri_localhost(self) -> None:
        request = fake_request(hostname='localhost', https=False, port=8000)
        expected = "http://localhost:8000/feedback/"
        self.assertEqual(request.build_absolute_uri('/feedback/'), expected)

    def test_request_context(self) -> None:
        """
        Ensure we have enough of a request to make useful RequestContext instances.
        """
        request = fake_request(hostname='localhost', https=False, port=8000)
        template = Template("{{ user }} likes {{ fruit }}")
        data = {'fruit': 'bananas'}

        # No request? No context processors will run.
        context = Context(data)
        self.assertEqual(template.render(context), ' likes bananas')

        # A request context enables much more magic
        request_context = RequestContext(request, data)
        self.assertEqual(
            template.render(request_context),
            'AnonymousUser likes bananas',
        )


class GetReferrerTest(SimpleTestCase):
    request: HttpRequest

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.request = RequestFactory().get('/about/')
        referrer = 'https://example.com/papers/refs.html?active=1#hot'
        cls.request.META['HTTP_REFERER'] = referrer

    def test_drop_fragment(self) -> None:
        self.assertEqual(
            get_referrer(self.request, drop_fragment=True),
            '/papers/refs.html'
        )

    def test_keep_query(self) -> None:
        self.assertEqual(
            get_referrer(self.request, drop_query=False),
            '/papers/refs.html?active=1#hot'
        )

    def test_no_referrer(self) -> None:
        """
        Use default value if not referrer.
        """
        request = RequestFactory().get('/about/')
        self.assertEqual(get_referrer(request), '/')
        self.assertEqual(
            get_referrer(request, default='/moved/'), '/moved/')

    def test_defaults(self) -> None:
        """
        Drop everything except the path and fragment.
        """
        self.assertEqual(get_referrer(self.request), '/papers/refs.html#hot')


class QuerydictFromDict(SimpleTestCase):
    def test_defaults(self) -> None:
        data_in = {
            'a': '1',
            'b': '2',
            'c': '3',
        }
        out = querydict_from_dict(data_in)
        self.assertIsInstance(out, QueryDict)
        self.assertEqual(repr(out), "<QueryDict: {'a': ['1'], 'b': ['2'], 'c': ['3']}>")

        message = r"This QueryDict instance is immutable"
        with self.assertRaisesRegex(AttributeError, message):
            out['d'] = 'peach'

    def test_mutable(self) -> None:
        data_in = {
            'a': '1',
            'b': '2',
            'c': '3',
        }
        out = querydict_from_dict(data_in, mutable=True)
        out['d'] = 'nectarine'
        self.assertIsInstance(out, QueryDict)
        self.assertEqual(out.dict(), {'a': '1', 'b': '2', 'c': '3', 'd': 'nectarine'})
