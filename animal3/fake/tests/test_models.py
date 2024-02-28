
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase

from ..models import ModelFaker


class ModelFakerNoModel(ModelFaker):
    """
    We forgot to provide our model!
    """


class ModelFakerTest(TestCase):
    def test_no_model_attribute(self) -> None:
        message = r"^ModelFakerNoModel missing class attribute 'model'$"
        with self.assertRaisesRegex(ImproperlyConfigured, message):
            ModelFakerNoModel()
