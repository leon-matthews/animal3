
from unittest import SkipTest

from django.core.exceptions import ImproperlyConfigured

from animal3.utils.testing import GET, POST

try:
    from ..views import ExcelListView
except ImportError:                                         # pragma: no cover
    raise SkipTest('OpenPyXL not installed')

from .test_serialiser import ExampleSerialiser, SerialiserTestCase


class ExcelListViewTest(SerialiserTestCase):
    class BadView(ExcelListView):
        pass

    class View(ExcelListView):
        excel_serialiser = ExampleSerialiser

    def test_no_serialiser_class_attribute(self) -> None:
        message = r"^An 'excel_serialiser' class must be provided$"
        with self.assertRaisesRegex(ImproperlyConfigured, message):
            GET(self.BadView)

    def test_post_not_allowed(self) -> None:
        """
        HTTP 405 Method Not Allowed.
        """
        response = POST(self.View)
        self.assertEqual(response.status_code, 405)

    def test_get(self) -> None:
        """
        Download attachment.
        """
        response = GET(self.View)
        self.assertEqual(response.status_code, 200)

        # Content
        self.assertIsInstance(response.content, bytes)
        self.assertGreater(len(response.content), 4096)
        self.assertTrue(response.content.startswith(b'PK'))

        # Headers
        self.assertEqual(
            response.headers['Content-Type'],
            'application/octet-stream',
        )
        self.assertRegex(
            response.headers['Content-Disposition'],
            r'attachment; filename="test-models-\d{4}-\d{2}-\d{2}.xlsx"',
        )
