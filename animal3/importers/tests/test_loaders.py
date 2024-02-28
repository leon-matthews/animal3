
from animal3.tests.models import TestModel
from typing import Any, Dict, Iterable

from django.core.exceptions import ImproperlyConfigured
from django.forms import ModelForm
from django.test import SimpleTestCase

from ..extractors import Extractor
from ..loaders import Loader


class EmptyExtractor(Extractor):
    def fields(self, model_tag: str) -> Iterable[Dict[str, Any]]:
        yield from ()                                       # pragma: no cover


class EmptyLoader(Loader):
    pass


class MinimalLoader(Loader):
    model = TestModel


class CustomForm(ModelForm):
    class Meta:
        model = TestModel
        exclude = ()


class CustomFormLoader(Loader):
    model = TestModel
    form_class = CustomForm


class LoaderTest(SimpleTestCase):
    extractor: Extractor

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.extractor = EmptyExtractor()

    def test_get_model_name(self) -> None:
        loader = MinimalLoader(self.extractor)
        self.assertEqual(loader.get_model_name(), 'TestModel')

    def test_get_form_class_custom(self) -> None:
        """
        Use custom form provided in loader's form_class attribute.
        """
        loader = CustomFormLoader(self.extractor)
        form_class = loader.get_form_class()
        self.assertEqual(form_class.__name__, 'CustomForm')
        self.assertTrue(issubclass(form_class, ModelForm))

    def test_get_form_class_default(self) -> None:
        """
        Create default ModelForm automatically from model.
        """
        loader = MinimalLoader(self.extractor)
        form_class = loader.get_form_class()
        self.assertEqual(form_class.__name__, 'TestModelForm')
        self.assertTrue(issubclass(form_class, ModelForm))

        form = form_class()
        self.assertIsInstance(form, ModelForm)
        expected = {'ordering', 'name', 'slug', 'price', 'description'}
        self.assertEqual(form.fields.keys(), expected)

    def test_form_class_not_found_error(self) -> None:
        message = r"^No model found on loader class$"
        with self.assertRaisesRegex(ImproperlyConfigured, message):
            EmptyLoader(self.extractor)
