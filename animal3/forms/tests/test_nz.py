
from django.test import SimpleTestCase

from ..nz import Regions


class RegionsTest(SimpleTestCase):
    def test_string_keys(self) -> None:
        for x in Regions:
            self.assertIsInstance(x, Regions)
            self.assertIsInstance(x.label, str)
            self.assertIsInstance(x.value, str)
