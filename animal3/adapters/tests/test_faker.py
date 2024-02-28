
from django.test import SimpleTestCase

from animal3.utils.testing import assert_deprecated

from ..faker import (
    fake_choice,
    fake_code,
    fake_datetime_between,
    fake_html_paragraphs,
    fake_price,
    get_faker,
)


class FakeChoiceTest(SimpleTestCase):
    def test_fake_choice_deprecated(self) -> None:
        message = 'fake_choice() moved to animal3.fake.choice()'
        with assert_deprecated(message):
            fake_choice([(0, 'Unknown')])


class FakeCodeTest(SimpleTestCase):
    def test_fake_code_deprecated(self) -> None:
        message = 'fake_code() moved to animal3.fake.numeric_string()'
        with assert_deprecated(message):
            fake_code()


class FakePriceTest(SimpleTestCase):
    def test_fake_price_deprecated(self) -> None:
        message = 'fake_price() moved to animal3.fake.price()'
        with assert_deprecated(message):
            fake_price()


class FakeDatetimeBetweenTest(SimpleTestCase):
    def test_datetime_between(self) -> None:
        message = (
            "fake_datetime_between() moved to animal3.fake.datetime_between()"
        )
        with assert_deprecated(message):
            fake_datetime_between('-30y', 'now')


class FakeHtmlParagraphsTest(SimpleTestCase):
    def test_html_paragraphs(self) -> None:
        message = (
            "fake_html_paragraphs() moved to animal3.fake.paragraphs_html()"
        )
        with assert_deprecated(message):
            fake_html_paragraphs(3)


class GetFakerTest(SimpleTestCase):
    def test_get_faker(self) -> None:
        message = r"The 3rd-party 'faker' package has been replaced with 'animal3.fake'"
        with self.assertRaisesRegex(ImportError, message):
            with assert_deprecated(message):
                get_faker()
