
import datetime
from decimal import Decimal
import io
from unittest import SkipTest

from animal3.tests.models import TestModel
from animal3.utils.tests.test_serialisers import SerialiserTestCase

try:
    from ..serialiser import ExcelSerialiserBase
except ImportError:                                         # pragma: no cover
    raise SkipTest('OpenPyXL not installed')


class ExampleSerialiser(ExcelSerialiserBase):
    converters = {
        'price': float,
    }
    exclude = ('created', 'ordering', 'updated')
    model = TestModel


class ExcelSerialiserTest(SerialiserTestCase):
    def setUp(self):
        self.serialiser = ExampleSerialiser()

    def test_excel_value(self) -> None:
        """
        Check type conversion.
        """
        naive_date = datetime.datetime(2023, 10, 20, 10, 15, 00)
        utc_date = naive_date.astimezone(datetime.timezone.utc)
        value = self.serialiser.excel_value

        self.assertEqual(value(None), '')
        self.assertEqual(value(False), '')
        self.assertEqual(value(True), 'Yes')
        self.assertEqual(value(3), 3)
        self.assertEqual(value(3.0), 3.0)
        self.assertEqual(value(Decimal(3)), 3.0)
        self.assertEqual(value(naive_date), '2023-10-20T10:15:00')
        self.assertEqual(value(utc_date), '2023-10-19T21:15:00+00:00')

    def test_get_header(self) -> None:
        header = self.serialiser.get_header()
        expected = ['ID', 'Name', 'Slug', 'Price', 'Description']
        self.assertEqual(header, expected)

    def test_get_rows(self) -> None:
        """
        Convert `get_rows()` generator into list, and compare. Note types.
        """
        rows = list(self.serialiser.get_rows())
        expected = [
            [1, 'Apples', 'apples', 34.34, ''],
            [2, 'Bananas', 'bananas', 4.5, ''],
            [3, 'Carrots', 'carrots', 12.25, ''],
        ]
        self.assertEqual(rows, expected)

    def test_write_bytes(self) -> None:
        output = io.BytesIO()
        xl = ExampleSerialiser()
        xl.write(output)
        length = len(output.getvalue())
        self.assertGreater(length, 4096)
