
import io
from typing import Type

from django.test import TestCase
from django.utils import timezone

from ...tests.models import TestModel

from ..serialisers import (
    CSVSerialiserBase, JSONSerialiserBase, QuerysetSerialiser,
)
from ..testing import multiline
from ..text import currency


# Utils ####################################################

def make_string(serialiser_class: Type[QuerysetSerialiser]) -> str:
    """
    Utility function to serialise to multi-line string.
    """
    try:
        output = io.StringIO()
        serialiser = serialiser_class()
        serialiser.write(output)
        string = output.getvalue()
    finally:
        output.close()
    return string


class SerialiserTestCase(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.create_test_models()

    @staticmethod
    def create_test_models() -> None:
        TestModel.objects.bulk_create([
            TestModel(name='Apples', slug='apples', price='34.34'),
            TestModel(name='Bananas', slug='bananas', price=4.50),
            TestModel(name='Carrots', slug='carrots', price=12.25),
        ])


# Serialisers ##############################################

class JSONSerialiser(JSONSerialiserBase):
    converters = {
        'price': float,
    }
    exclude = ('created', 'ordering', 'updated')
    model = TestModel


class CSVSerialiserBasic(CSVSerialiserBase):
    """
    Minimal CSV serialiser, using default values for all options.

    (Except for 'exclude', 'cause who wants to deal with all those datetimes.)
    """
    exclude = ['created', 'ordering', 'updated']
    model = TestModel


class CSVSerialiserFull(CSVSerialiserBase):
    """
    A more user-friendly serialiser.

    Formats the prices and gives nicer column names.
    """
    converters = {
        'price': currency,
    }
    exclude = ['created', 'updated', 'ordering']
    field_names_verbose = {
        'id': 'ID',
        'price': 'Recommended Retail',
    }
    model = TestModel


# Test cases ###############################################

class CSVSerialiserBasicTest(SerialiserTestCase):
    """
    Test minimal CSV serialiser
    """
    def test_default_filename(self) -> None:
        serialiser = CSVSerialiserBasic()
        output = serialiser.get_filename()
        date = timezone.localtime().strftime('%Y-%m-%d')
        expected = f"test-models-{date}.csv"
        self.assertEqual(output, expected)

    def test_default_output(self) -> None:
        output = make_string(CSVSerialiserBasic)
        expected = (
            "ID,Name,Slug,Price,Description\r\n"
            "1,Apples,apples,34.34,\r\n"
            "2,Bananas,bananas,4.50,\r\n"
            "3,Carrots,carrots,12.25,\r\n"
        )
        self.assertEqual(output, expected)


class CSVSerialiserFullTest(SerialiserTestCase):
    """
    Test more fully-featured serialiser.
    """
    def test_default_output(self) -> None:
        output = make_string(CSVSerialiserFull)
        expected = (
            "ID,Name,Slug,Recommended Retail,Description\r\n"
            "1,Apples,apples,$34.34,\r\n"
            "2,Bananas,bananas,$4.50,\r\n"
            "3,Carrots,carrots,$12.25,\r\n"
        )
        self.assertEqual(output, expected)


class JSONSerialiserTest(SerialiserTestCase):
    maxDiff = None

    def test_get_file_name(self) -> None:
        serialiser = JSONSerialiser()
        output = serialiser.get_filename()
        date = timezone.localtime().strftime('%Y-%m-%d')
        expected = f"test-models-{date}.json"
        self.assertEqual(output, expected)

    def test_default_output(self) -> None:
        output = make_string(JSONSerialiser)
        expected = multiline("""
            [
                {
                    "id": 1,
                    "name": "Apples",
                    "slug": "apples",
                    "price": 34.34,
                    "description": ""
                },
                {
                    "id": 2,
                    "name": "Bananas",
                    "slug": "bananas",
                    "price": 4.5,
                    "description": ""
                },
                {
                    "id": 3,
                    "name": "Carrots",
                    "slug": "carrots",
                    "price": 12.25,
                    "description": ""
                }
            ]
        """)
        self.assertEqual(output, expected)
