
import configparser
from decimal import Decimal

from django.db import models
from django.test import override_settings, SimpleTestCase, TestCase

from animal3.tests.models import SlugOnly, TestModel

from ..utils import (
    get_settings_ini, model_to_dict, unique_slug,
)


SETTINGS_INI = """
[keys]
bool = False
float = 455.95
integer = 42
multiline =
    Twas brillig, and the slithy toves
    Did gyre and gimble in the wabe:
    All mimsy were the borogoves,
    And the mome raths outgrabe
multiword = Leon Matthews
word = Leon
"""
config = configparser.ConfigParser()
config.read_string(SETTINGS_INI)


@override_settings(SETTINGS_INI=config)
class GetSettingsKeyTest(SimpleTestCase):
    def test_strings(self) -> None:
        """
        Everything is a string by default.
        """
        self.assertEqual(get_settings_ini('keys', 'bool'), 'False')
        self.assertEqual(get_settings_ini('keys', 'float'), '455.95')
        self.assertEqual(get_settings_ini('keys', 'word'), 'Leon')
        self.assertEqual(get_settings_ini('keys', 'multiword'), 'Leon Matthews')

        # Note the position of the newlines
        multiline = (
            'Twas brillig, and the slithy toves\n'
            'Did gyre and gimble in the wabe:\n'
            'All mimsy were the borogoves,\n'
            'And the mome raths outgrabe'
        )
        self.assertEqual(get_settings_ini('keys', 'multiline'), multiline)

    def test_to_bool(self) -> None:
        self.assertEqual(get_settings_ini('keys', 'bool', to_bool=True), False)
        self.assertEqual(get_settings_ini('keys', 'integer', to_bool=True), True)

    def test_to_float(self) -> None:
        self.assertEqual(get_settings_ini('keys', 'float', to_float=True), 455.95)

    def test_to_int(self) -> None:
        self.assertEqual(get_settings_ini('keys', 'integer', to_int=True), 42)
        self.assertEqual(get_settings_ini('keys', 'float', to_int=True), 456)

    def test_too_many_conversions(self) -> None:
        message = r"Only one type conversion at a time, please."
        with self.assertRaisesRegex(ValueError, message):
            get_settings_ini('key', 'word', to_bool=True, to_float=True)

        # Catch 'thruthy' values as well boolean.
        # Previous version of check used ``tuple.count(True)``, but that was not as robust.
        with self.assertRaisesRegex(ValueError, message):
            get_settings_ini('key', 'word', to_bool='apple', to_float=3)  # type: ignore[arg-type]

    def test_section_not_found(self) -> None:
        message = r"Missing key 'agent' under 'secret' section in settings.ini"
        with self.assertRaisesRegex(KeyError, message):
            get_settings_ini('secret', 'agent')

    def test_name_not_found(self) -> None:
        message = r"Missing key 'nosuchname' under 'keys' section in settings.ini"
        with self.assertRaisesRegex(KeyError, message):
            get_settings_ini('keys', 'nosuchname')


class ModelToDictTest(SimpleTestCase):
    def test_model_to_dict(self) -> None:
        instance = TestModel(
            name='John Q. Public',
            slug='john-q-public',
            price=Decimal('199.95'),
            description="Not a man",
        )
        dictionary = model_to_dict(instance)
        expected = {
            'created': None,
            'description': 'Not a man',
            'id': None,
            'name': 'John Q. Public',
            'ordering': 0,
            'price': Decimal('199.95'),
            'slug': 'john-q-public',
            'updated': None,
        }
        self.assertEqual(dictionary, expected)


class UniqueSlugTest(TestCase):
    queryset: models.QuerySet

    @classmethod
    def setUpTestData(cls) -> None:
        SlugOnly.objects.bulk_create([
            SlugOnly(slug='bean'),
            SlugOnly(slug='bean2'),
            SlugOnly(slug='bean5'),
        ])
        cls.queryset = SlugOnly.objects.all()

    def test_unique(self) -> None:
        self.assertEqual(self.queryset.count(), 3)
        slug = unique_slug(self.queryset, 'bean')
        self.assertEqual(slug, 'bean6')

    def test_existing_suffix(self) -> None:
        slug = unique_slug(self.queryset, 'bean2')
        self.assertEqual(slug, 'bean6')

    def test_not_in_sequence(self) -> None:
        slug = unique_slug(self.queryset, 'bean3')
        self.assertEqual(slug, 'bean6')
