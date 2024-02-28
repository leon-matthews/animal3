
from typing import Any, Dict

from django.forms import ModelForm
from django.test import SimpleTestCase

from animal3.tests.models import SimpleModel, TestModel

from ..transformers import Transformer


DATA = {
    'name': 'Peanut Slabs (6-Pack)',
    'slug': 'peanut-slabs-6-pack',
    'price': 9.99,
    'description': 'Need more than one, fatty? Here you go!'
}


class Copy(Transformer):
    """
    Return copy of field data unchanged. No files.
    """
    model_label = 'copy'


class CopyTest(SimpleTestCase):
    """
    Minimal transformer returns POST data unchanged.
    """
    transformer: Transformer

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.transformer = Copy()

    def test_get_form_data(self) -> None:
        data = self.transformer.get_form_data(DATA.copy())
        self.assertEqual(data, DATA)

    def test_get_file_data(self) -> None:
        files = self.transformer.get_form_files(DATA.copy())
        self.assertEqual(files, {})


class Modify(Transformer):
    """
    Modify data. No files.
    """
    def get_form_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        data['price'] += 1
        data['title'] = data.pop('name')
        del data['description']
        return data


class ModifyTest(SimpleTestCase):
    """
    POST data is changed before passing to form.
    """
    transformer: Transformer

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.transformer = Modify()

    def test_get_form_data(self) -> None:
        data = self.transformer.get_form_data(DATA.copy())

        # Check that original has not been modified
        self.assertEqual(DATA['price'], 9.99)

        # Transformed?
        expected = {
            'slug': 'peanut-slabs-6-pack',
            'price': 10.99,
            'title': 'Peanut Slabs (6-Pack)',
        }
        self.assertEqual(data, expected)


class SimpleModelForm(ModelForm):
    class Meta:
        exclude = ()
        model = SimpleModel


class TestModelForm(ModelForm):
    class Meta:
        exclude = ()
        model = TestModel


class CheckTest(SimpleTestCase):
    """
    Verify that the check() method returns the expected errors.
    """
    def test_no_errors(self) -> None:
        transformer = Copy()
        data = {
            'title': 'Required',
            'description': '',
        }
        errors = transformer.check(data, SimpleModelForm)
        self.assertEqual(errors, [])

    def test_form_not_valid(self) -> None:
        """
        Right number of fields, but form still invalid.
        """
        transformer = Copy()
        data = {
            'title': '',
            'description': '',
        }
        errors = transformer.check(data, SimpleModelForm)
        self.assertEqual(errors, ['Form error. Required fields missing: title'])

    def test_too_few_fields(self) -> None:
        """
        Form valid, but too few fields passed to form.
        """
        transformer = Copy()
        data = {
            'title': "Form alone doesn't need a description",
        }
        errors = transformer.check(data, SimpleModelForm)
        self.assertEqual(errors, ['Transformer is missing fields: description'])

    def test_too_few_fields_not_strict(self) -> None:
        """
        Form valid, but too few fields passed to form.
        """
        transformer = Copy()
        data = {
            'title': "Form alone doesn't need a description",
        }
        errors = transformer.check(data, SimpleModelForm, strict=False)
        self.assertEqual(errors, [])

    def test_extra_fields(self) -> None:
        """
        Form valid, but too many fields passed to form.
        """
        transformer = Copy()
        data = {
            'title': "Form alone doesn't need a description",
            'description': '',
            'opinion': "Let my give you my two cents",
        }
        errors = transformer.check(data, SimpleModelForm)
        expected = [
            "Transformer provided extra fields: opinion",
        ]
        self.assertEqual(errors, expected)

    def test_extra_fields_not_strict(self) -> None:
        """
        Form valid, but too many fields passed to form.
        """
        transformer = Copy()
        data = {
            'title': "Form alone doesn't need a description",
            'description': '',
            'opinion': "Let my give you my two cents",
        }
        errors = transformer.check(data, SimpleModelForm, strict=False)
        self.assertEqual(errors, [])

    def test_form_errors_collect(self) -> None:
        """
        Collect similar errors from form validation together into one line.
        """
        transformer = Copy()
        errors = transformer.check({}, TestModelForm)
        expected = [
            'Form error. Required fields missing: name, ordering, slug',
            'Transformer is missing fields: description, name, ordering, price, slug',
        ]
        self.assertEqual(errors, expected)
