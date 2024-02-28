
from unittest import TestCase

from django.db import models

from animal3 import fake


class ChoiceTest(TestCase):
    """
    Traditional tuple of tuples.
    """
    JANUARY = 1
    FEBRUARY = 2
    MARCH = 3
    APRIL = 4
    MAY = 5
    JUNE = 6
    JULY = 7
    AUGUST = 8
    SEPTEMBER = 9
    OCTOBER = 10
    NOVEMBER = 11
    DECEMBER = 12
    MONTH_CHOICES = (
        (JANUARY, "January"),
        (FEBRUARY, "February"),
        (MARCH, "March"),
        (APRIL, "April"),
        (MAY, 'May'),
        (JUNE, 'June'),
        (JULY, 'July'),
        (AUGUST, 'August'),
        (SEPTEMBER, 'September'),
        (OCTOBER, 'October'),
        (NOVEMBER, 'November'),
        (DECEMBER, 'December'),
    )

    def test_fake_choice(self) -> None:
        for _ in range(100):
            choice = fake.choice(self.MONTH_CHOICES)
            assert isinstance(choice, int)                # For mypy
            self.assertTrue(choice >= 1)
            self.assertTrue(choice <= 12)

    def test_fake_multichoice(self) -> None:
        for _ in range(100):
            choices = fake.multichoice(self.MONTH_CHOICES)
            self.assertIsInstance(choices, list)
            self.assertTrue(len(choices) >= 2)
            self.assertTrue(len(choices) <= 12)

    def test_fake_multichoice_uniform(self) -> None:
        for _ in range(100):
            choices = fake.multichoice(self.MONTH_CHOICES, uniform=True)
            self.assertIsInstance(choices, list)
            self.assertTrue(len(choices) >= 2)
            self.assertTrue(len(choices) <= 12)

    def test_fake_multichoice_too_few(self) -> None:
        JANUARY = 1
        MONTH_CHOICES = (
            (JANUARY, "January"),
        )
        message = "Too few choices given to choose multiple values"
        with self.assertRaisesRegex(ValueError, message):
            fake.multichoice(MONTH_CHOICES)


class ChoiceEnumTest(TestCase):
    """
    Test the Enum choices introduced in Django 3.0
    """
    class KeyboardLayouts(models.TextChoices):
        AZERTY = 'a', 'AZERTY'
        COLEMAK = 'c', 'Colemak'
        DVORAK = 'd', 'Dvorak'
        QUERTY = 'q', 'QUERTY'

    class StatusChoices(models.IntegerChoices):
        PENDING = (1, 'Payment pending')
        ACCEPTED = (2, 'Accepted')
        COMPLETE = (3, 'Complete')
        CANCELLED = (4, 'Cancelled')
        DECLINED = (5, 'Payment Declined')

    def test_enum_fake_choice(self) -> None:
        """
        Use new Enum support in Django 3.0
        """
        choices = self.StatusChoices.choices
        for _ in range(100):
            choice = fake.choice(choices)
            assert isinstance(choice, int)
            self.assertGreater(choice, 0)
            self.assertLess(choice, 6)

    def test_enum_fake_choice_error(self) -> None:
        """
        As above, but forgetting to use the `choices` attribute.
        """
        message = r"Bare Enum class given, use 'StatusChoices.choices'"
        with self.assertRaisesRegex(ValueError, message):
            fake.choice(self.StatusChoices)                 # type: ignore[arg-type]

    def test_enum_fake_multichoice(self) -> None:
        for _ in range(100):
            choices = fake.multichoice(self.KeyboardLayouts.choices)
            self.assertIsInstance(choices, list)
            self.assertTrue(len(choices) >= 2)
            self.assertTrue(len(choices) <= len(self.KeyboardLayouts))

    def test_enum_fake_multichoice_error(self) -> None:
        """
        As above, but forgetting to use the `choices` attribute.
        """
        message = r"Bare Enum class given, use 'KeyboardLayouts.choices'"
        with self.assertRaisesRegex(ValueError, message):
            fake.multichoice(self.KeyboardLayouts)          # type: ignore[arg-type]
