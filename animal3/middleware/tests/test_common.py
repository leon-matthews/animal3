
from django.core.exceptions import ImproperlyConfigured
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseRedirect,
)
from django.test import TestCase

from ..common import append_slash


class TestAppendSlashMiddleware(TestCase):
    def setUp(self) -> None:
        self.request = HttpRequest()
        self.request.META['SERVER_NAME'] = 'localhost'
        self.request.META['SERVER_PORT'] = 80
        self.request.method = 'GET'
        self.request.path = '/about'

        self.response = HttpResponse()
        self.response.status_code = 404
        self.response['QUERY_STRING'] = ''

        self.middleware = append_slash(lambda request: self.response)

    def test_do_nothing_if_404(self) -> None:
        """
        No action required if response not a 404.
        """
        self.response.status_code = 200
        response = self.middleware(self.request)
        self.assertIs(response, self.response)

    def test_do_nothing_if_post(self) -> None:
        self.request.method = 'POST'
        response = self.middleware(self.request)
        self.assertIs(response, self.response)

    def test_do_nothing_if_slashed(self) -> None:
        self.request.path += '/'
        response = self.middleware(self.request)
        self.assertIs(response, self.response)

    def test_improperly_configured(self) -> None:
        """
        Middleware should be disabled if unusable.
        """
        with self.settings(APPEND_SLASH=False):
            with self.assertRaises(ImproperlyConfigured):
                # Any callable will do as an argument...
                append_slash(str)

    def test_redirect(self) -> None:
        """
        Actually perform redirect.
        """
        response = self.middleware(self.request)
        self.assertIsInstance(response, HttpResponseRedirect)
        self.assertFalse(self.request.path.endswith('/'))
        self.assertTrue(response.url.endswith('/'))

    def test_preserve_querystring(self) -> None:
        self.request.META['QUERY_STRING'] = 'q=apple&order_by=colour'
        response = self.middleware(self.request)
        self.assertEqual(
            response.url,
            'http://localhost/about/?q=apple&order_by=colour')
