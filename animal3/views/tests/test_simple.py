
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpRequest
from django.test import RequestFactory, SimpleTestCase
from django.urls import reverse

from ..simple import redirect, RedirectPrefixView


class RedirectTest(SimpleTestCase):
    expected_url = reverse('index')

    def test_redirect(self) -> None:
        view = redirect('index')
        self.assertTrue(callable(view))

        # Can't use GET() here, as_view() already called
        request = RequestFactory().get('/')
        response = view(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, self.expected_url)

    def test_redirect_permanent(self) -> None:
        view = redirect('index', permanent=True)
        response = view(RequestFactory().get('/'))
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response.url, self.expected_url)


class RedirectPrefixViewTest(SimpleTestCase):
    request: HttpRequest

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.request = RequestFactory().get('/')

    def test_missing_prefix(self) -> None:
        """
        Require that ``as_view()`` gets a 'prefix' argument.
        """
        message = r"^Missing required 'prefix' argument$"
        with self.assertRaisesRegex(ImproperlyConfigured, message):
            RedirectPrefixView.as_view()

    def test_missing_path(self) -> None:
        """
        No path capture/converter argument in URL.
        """
        view = RedirectPrefixView.as_view(prefix='/news/')
        message = r"^No 'path' found in URL for RedirectPrefixView$"
        with self.assertRaisesRegex(ImproperlyConfigured, message):
            view(self.request)

    def test_rename_app(self) -> None:
        """
        Rename 'blog' to 'news'
        """
        view = RedirectPrefixView.as_view(prefix='/news/')
        response = view(self.request, path='/1995/first-post/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/news/1995/first-post/')

    def test_leading_slashes(self) -> None:
        """
        Rename 'blog' to 'news', but without leading slashes.
        """
        view = RedirectPrefixView.as_view(prefix='news/')
        response = view(self.request, path='1995/first-post/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/news/1995/first-post/')

    def test_permanent(self) -> None:
        view = RedirectPrefixView.as_view(prefix='/news/', permanent=True)
        response = view(self.request, path='/1995/first-post/')
        self.assertEqual(response.status_code, 301)

    def test_temporary_or_permanent(self) -> None:
        view = RedirectPrefixView.as_view(prefix='/news/')
        response = view(self.request, path='/1995/first-post/')
        self.assertEqual(response.status_code, 302)
