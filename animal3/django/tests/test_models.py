
from django.db.models import IntegerChoices, TextChoices
from django.test import SimpleTestCase

from ..models import enum_from_label


# Traditional list-of-tuples for Django < 3.0
FRESHMAN = 'FR'
SOPHOMORE = 'SO'
JUNIOR = 'JR'
SENIOR = 'SR'
GRADUATE = 'GR'
YEAR_IN_SCHOOL_CHOICES = [
    (FRESHMAN, 'Freshman'),
    (SOPHOMORE, 'Sophomore'),
    (JUNIOR, 'Junior'),
    (SENIOR, 'Senior'),
    (GRADUATE, 'Graduate'),
]

YEAR_IN_SCHOOL_CHOICES_TUPLE = (
    (FRESHMAN, 'Freshman'),
    (SOPHOMORE, 'Sophomore'),
    (JUNIOR, 'Junior'),
    (SENIOR, 'Senior'),
    (GRADUATE, 'Graduate'),
)


class KeyboardLayouts(TextChoices):
    AZERTY = 'a', 'AZERTY'
    COLEMAK = 'c', 'Colemak'
    DVORAK = 'd', 'Dvorak'
    QUERTY = 'q', 'QUERTY'


class StatusChoices(IntegerChoices):
    PENDING = (1, 'Payment pending')
    ACCEPTED = (2, 'Accepted')
    COMPLETE = (3, 'Complete')
    CANCELLED = (4, 'Cancelled')
    DECLINED = (5, 'Payment Declined')


class Vehicle(TextChoices):
    """
    Labels build automatically by Django
    """
    CAR = 'C'
    JET_SKI = 'J'
    MOTORBIKE = 'M'
    TRUCK = 'T'


class FindEnumValueTest(SimpleTestCase):
    def test_integer_choice(self) -> None:
        # Note that comparison is not case-sensitive
        value = enum_from_label(StatusChoices, 'complete')
        self.assertIsInstance(value, int)
        self.assertEqual(value, 3)
        self.assertEqual(value, StatusChoices.COMPLETE)

    def test_integer_choice_not_found(self) -> None:
        message = "Invalid label for <enum 'StatusChoices'>: 'Banana'"
        with self.assertRaisesRegex(KeyError, message):
            enum_from_label(StatusChoices, 'Banana')

    def test_text_choice(self) -> None:
        value = enum_from_label(KeyboardLayouts, 'querty')
        self.assertIsInstance(value, str)
        self.assertEqual(value, 'q')
        self.assertEqual(value, KeyboardLayouts.QUERTY)

    def test_text_choice_not_found(self) -> None:
        message = "Invalid label for <enum 'KeyboardLayouts'>: 'KUMQUAT'"
        with self.assertRaisesRegex(KeyError, message):
            enum_from_label(KeyboardLayouts, 'KUMQUAT')

    def test_automatic_labels(self) -> None:
        value = enum_from_label(Vehicle, 'car')
        self.assertIsInstance(value, str)
        self.assertEqual(value, 'C')
        self.assertEqual(value, Vehicle.CAR)

    def test_traditional_choices(self) -> None:
        value = enum_from_label(YEAR_IN_SCHOOL_CHOICES, 'sophomore')
        self.assertEqual(value, 'SO')
        self.assertEqual(value, SOPHOMORE)

    def test_traditional_choices_not_found(self) -> None:
        """
        Should raise `KeyError` if value not found.

        Also ensure that an enclosing tuple rather than a list is handled
        correctly.
        """
        message = r"Invalid label for .*"
        with self.assertRaisesRegex(KeyError, message):
            enum_from_label(YEAR_IN_SCHOOL_CHOICES_TUPLE, 'Form 6')
