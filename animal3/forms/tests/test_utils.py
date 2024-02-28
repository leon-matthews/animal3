
from pathlib import Path
from typing import Any, Dict

from django import forms
from django.core.exceptions import SuspiciousFileOperation
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TestCase

from animal3.utils.testing import DocTestLoader

from ...tests.models import TestModel

from .. import utils
from ..utils import (
    cleaned_data_to_dict,
    collapse_errors,
    create_upload,
    errors_to_string,
    form_values_line,
)


class DocTests(TestCase, metaclass=DocTestLoader, test_module=utils):
    pass


class SampleForm(forms.Form):
    name = forms.CharField()
    nickname = forms.CharField(required=False)
    email = forms.EmailField()
    phone = forms.CharField(required=False)
    year_joined = forms.IntegerField(required=False)
    model = forms.ModelChoiceField(queryset=TestModel.objects.all(), required=False)


DATA: Dict[str, Any] = {
    'email': 'johnj@example.com',
    'name': 'John Jones',
    'nickname': 'JJ',
    'phone': '021 555-1234',
    'year_joined': '2018',
}


class CleanedDataToDictTest(TestCase):
    maxDiff = None

    def test_valid_full(self) -> None:
        data = DATA.copy()
        form = SampleForm(data=data)
        self.assertTrue(form.is_valid())
        expected = {
            'email': 'johnj@example.com',
            'name': 'John Jones',
            'nickname': 'JJ',
            'phone': '021 555-1234',
            'year_joined': 2018,
        }
        self.assertEqual(cleaned_data_to_dict(form), expected)

    def test_valid_partial(self) -> None:
        # Remove non-required fields
        data = DATA.copy()
        del data['nickname']
        del data['phone']
        del data['year_joined']
        form = SampleForm(data=data)
        self.assertTrue(form.is_valid())
        expected = {
            'email': 'johnj@example.com',
            'name': 'John Jones',
        }
        self.assertEqual(cleaned_data_to_dict(form), expected)

    def test_with_model(self) -> None:
        model = TestModel(name='Silly', slug='silly', pk=3)
        model.save()

        data = DATA.copy()
        data['model'] = model
        form = SampleForm(data=data)
        self.assertTrue(form.is_valid())
        expected = {
            'email': 'johnj@example.com',
            'model': 3,
            'name': 'John Jones',
            'nickname': 'JJ',
            'phone': '021 555-1234',
            'year_joined': 2018,
        }
        self.assertEqual(cleaned_data_to_dict(form), expected)


class CreateUploadTest(SimpleTestCase):
    def test_create_upload(self) -> None:
        path = Path(__file__)
        upload = create_upload(path)
        self.assertIsInstance(upload, SimpleUploadedFile)
        self.assertEqual(upload.name, 'test-utils.py')      # Note hyphen
        self.assertEqual(upload.content_type, 'text/x-python')

    def test_custom_name_cleaned(self) -> None:
        path = Path(__file__)
        upload = create_upload(path, 'Gud Code!')
        self.assertEqual(upload.name, 'gud-code')
        self.assertEqual(upload.content_type, 'text/x-python')

    def test_not_found(self) -> None:
        path = Path('no/such/file')
        message = r"^Upload not found:...*/no/such/file'$"
        with self.assertRaisesRegex(FileNotFoundError, message):
            create_upload(path)

    def test_catch_dangerous(self) -> None:
        path = Path('/etc/passwd')
        message = r"^Path is not under ALLOWED_ROOTS: PosixPath\('/etc/passwd'\)$"
        with self.assertRaisesRegex(SuspiciousFileOperation, message):
            create_upload(path)

    def test_catch_sneaky(self) -> None:
        path = Path('/srv/websites/example.com/../../../etc/passwd')
        message = (
            r"^Path is not under ALLOWED_ROOTS: "
            r"PosixPath\('/srv/websites/example.com/../../../etc/passwd'\)$"
        )
        with self.assertRaisesRegex(SuspiciousFileOperation, message):
            create_upload(path)


class ErrorsToStringTest(SimpleTestCase):
    maxDiff = None

    def test_errors_to_string(self) -> None:
        form = SampleForm(data={})
        self.assertFalse(form.is_valid())
        errors = errors_to_string(form)
        expected = (
            "\n"
            "    SampleForm.name: This field is required.\n"
            "    SampleForm.email: This field is required."
        )
        self.assertEqual(errors, expected)

    def test_no_errors(self) -> None:
        form = SampleForm(data=DATA)
        self.assertTrue(form.is_valid())
        errors = errors_to_string(form)
        self.assertEqual(errors, '')


class FormValuesListTest(SimpleTestCase):
    form: SampleForm

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        data = DATA.copy()
        data['csrfmiddlewaretoken'] = 'KcyqgLKXXoyw4SIzw8gpn7j9s4Pms9YFwWxkm'
        cls.form = SampleForm(data=data)
        cls.form.is_valid()

    def test_form_values_line_cleaned_data(self) -> None:
        self.assertTrue(self.form.is_valid())
        line = form_values_line(self.form.cleaned_data)
        expected = "John Jones, JJ, johnj@example.com, 021 555-1234, 2018, None"
        self.assertEqual(line, expected)

    def test_form_values_line_data(self) -> None:
        line = form_values_line(self.form.data)
        expected = "johnj@example.com, John Jones, JJ, 021 555-1234, 2018"
        self.assertEqual(line, expected)

    def test_form_values_line_maxlen(self) -> None:
        line = form_values_line(self.form.data, maxlen=31)
        self.assertEqual(len(line), 31)

    def test_form_values_line_allow_csrf(self) -> None:
        line = form_values_line(self.form.data, maxlen=None, skip_csrf=False)
        expected = (
            "johnj@example.com, John Jones, JJ, 021 555-1234, "
            "2018, KcyqgLKXXoyw4SIzw8gpn7j9s4Pms9YFwWxkm"
        )
        self.assertEqual(line, expected)

    def test_form_values_line_form_error(self) -> None:
        """
        Passing the form instead of the form's data should raise ValueError
        """
        message = (
            "Unexpected form instance. Pass `form.data` or "
            "`form.cleaned_data` instead."
        )
        with self.assertRaisesRegex(ValueError, message):
            form_values_line(self.form)                     # type: ignore[arg-type]


class CollapseErrorsTest(SimpleTestCase):
    def test_collapse_errors(self) -> None:
        errors = {
            'ordering': ['This field is required.'],
            'name': ['This field is required.'],
            'slug': ['This field is required.'],
        }
        output = collapse_errors(errors)
        expected = ['Required fields missing: name, ordering, slug']
        self.assertEqual(output, expected)

    def test_collapse_errors_different(self) -> None:
        errors = {
            'sender': ['Enter a valid email address.'],
            'subject': ['This field is required.'],
        }
        output = collapse_errors(errors)
        expected = [
            'Enter a valid email address: sender',
            'Required fields missing: subject',
        ]
        self.assertEqual(output, expected)
