
from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase

from .. import fields


class HtmlFieldTest(SimpleTestCase):
    def test_cannot_instantiate(self) -> None:
        message = (
            r"^Cannot instantiate abstract class. Use ArticleField, "
            r"Article2Field, or RedactorField$"
        )
        with self.assertRaisesRegex(ImproperlyConfigured, message):
            fields.HtmlField()
