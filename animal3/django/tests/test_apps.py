
from django.test import RequestFactory, SimpleTestCase

from ..apps import get_current_app


class TestGetCurrentApp(SimpleTestCase):
    def test_no_current_app(self) -> None:
        request = RequestFactory().get('/')
        current = get_current_app(request)
        self.assertIs(current, None)
