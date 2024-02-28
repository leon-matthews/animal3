
from typing import Dict

from django import forms
from django.core.exceptions import ImproperlyConfigured, SuspiciousOperation
from django.http import QueryDict
from django.test import SimpleTestCase

from animal3.utils.text import split_name

from ..mixins import (
    AddPlaceholders, AsDictMixin, PrecleanMixin, SpamHoneypot,
)


class AddPlaceholdersTest(SimpleTestCase):
    class SampleForm(AddPlaceholders, forms.Form):
        name = forms.CharField()
        nickname = forms.CharField(label='Preferred name')
        email = forms.EmailField()

        class Meta:
            placeholders = {
                'email': 'john@example.com',
            }

    def test_placeholders(self) -> None:
        form = self.SampleForm()
        placeholders = self.extract_placeholders(form)
        expected = {
            'email': 'john@example.com',        # From form's Meta class's 'placeholder'
            'name': 'Name',                     # From field's name
            'nickname': 'Preferred name',       # From field's 'label'
        }
        self.assertEqual(placeholders, expected)

    def extract_placeholders(self, form: forms.Form) -> Dict[str, str]:
        placeholders = {}
        for name, field in form.fields.items():
            placeholder = field.widget.attrs.get('placeholder', '')
            placeholders[name] = placeholder
        return placeholders


class AsDictMixinTest(SimpleTestCase):
    DATA = {
        'email': 'johns@example.com',
        'name': 'John Smith',
        'nickname': 'JJ',
        'phone': '021 555-1234',
    }

    class SampleForm(AsDictMixin, forms.Form):
        name = forms.CharField()
        nickname = forms.CharField(required=False)
        email = forms.EmailField()
        phone = forms.CharField(required=False)

    def test_ordering(self) -> None:
        form = self.SampleForm(data=self.DATA)
        self.assertTrue(form.is_valid())

        ordering = ('name', 'nickname', 'email', 'phone')
        data = form.asdict()
        for name, expected in zip(data.keys(), ordering):
            self.assertEqual(name, expected)

    def test_no_cleaned_data(self) -> None:
        """
        RuntimeError raised if form bound, but clean() hasn't run yet.
        """
        form = self.SampleForm(data=self.DATA)
        message = r"Form has not run clean\(\) yet. Call `form.is_valid\(\)`"
        with self.assertRaisesRegex(RuntimeError, message):
            form.asdict()

    def test_not_bound(self) -> None:
        """
        RuntimeError raised if form not bound.
        """
        form = self.SampleForm()
        message = r"Cannot call asdict\(\) on a non-bound form"
        with self.assertRaisesRegex(RuntimeError, message):
            form.asdict()

    def test_partial(self) -> None:
        """
        Skip some not-required fields.
        """
        data = self.DATA.copy()
        del data['nickname']
        del data['phone']
        form = self.SampleForm(data=data)
        self.assertTrue(form.is_valid())
        expected = {
            'name': 'John Smith',
            'email': 'johns@example.com',
        }
        self.assertEqual(form.asdict(), expected)

    def test_valid(self) -> None:
        """
        Full set of data.
        """
        form = self.SampleForm(data=self.DATA)
        self.assertTrue(form.is_valid())
        expected = {
            'name': 'John Smith',
            'nickname': 'JJ',
            'email': 'johns@example.com',
            'phone': '021 555-1234',
        }
        self.assertEqual(form.asdict(), expected)


class PrecleanMixinTest(SimpleTestCase):
    """
    Test PrecleanMixin using several example form classes.
    """
    class MissingPrecleanMethodForm(PrecleanMixin, forms.Form):
        """
        The required preclean() method has not been provided.
        """
        name = forms.CharField()
        email = forms.EmailField()

    class SplitNameForm(PrecleanMixin, forms.Form):
        """
        Full name in first_name field? Not a problem!
        """
        first_name = forms.CharField()
        last_name = forms.CharField()

        def preclean(self, data: QueryDict) -> QueryDict:
            # Full name in first_name field?
            first_name = data.get('first_name', '')
            if ' ' in first_name and not data.get('last_name', '').strip():
                data['first_name'], data['last_name'] = split_name(first_name)
            return data

    def test_error_message(self) -> None:
        """
        Nice error message from MissingPrecleanMethodForm.
        """
        message = (
            r"PrecleanMixin requires that a preclean\(\) method be "
            r"defined in MissingPrecleanMethodForm"
        )
        with self.assertRaisesRegex(NotImplementedError, message):
            self.MissingPrecleanMethodForm(data={})         # type: ignore[arg-type]

    def test_preclean(self) -> None:
        """
        Test functionality from SplitNameForm.
        """
        data = {
            'first_name': 'John Smith',
            'last_name': ' ',
        }
        form = self.SplitNameForm(data=data)                # type: ignore[arg-type]
        self.assertIsInstance(form.data, QueryDict)
        expected = {
            'first_name': ['John'],
            'last_name': ['Smith'],
        }
        self.assertEqual(dict(form.data), expected)

    def test_preclean_not_needed(self) -> None:
        data = {
            'first_name': 'John',
            'last_name': 'Smith',
        }
        form = self.SplitNameForm(data=data)                # type: ignore[arg-type]
        self.assertIsInstance(form.data, QueryDict)
        expected = {
            'first_name': ['John'],
            'last_name': ['Smith'],
        }
        self.assertEqual(dict(form.data), expected)

    def test_querydict(self) -> None:
        """
        Data from request.GET or request.POST are read-only QueryDict instances.
        """
        data = QueryDict('first_name=John+Smith')
        form = self.SplitNameForm(data=data)
        self.assertIsInstance(form.data, QueryDict)
        expected = {
            'first_name': ['John'],
            'last_name': ['Smith'],
        }
        self.assertEqual(dict(form.data), expected)

    def test_returns_read_only_queryset(self) -> None:
        """
        Data QuerySet remains read-only after preclean() runs.
        """
        immutable_message = "This QueryDict instance is immutable"

        data = QueryDict('first_name=John+Smith')

        # Starts read-only
        with self.assertRaisesRegex(AttributeError, immutable_message):
            data['last_name'] = 'Hammersly'                 # type: ignore[misc]

        # Should stay read-only!
        form = self.SplitNameForm(data=data)
        with self.assertRaisesRegex(AttributeError, immutable_message):
            form.data['last_name'] = 'Hammersly'            # type: ignore[index]


HONEYPOT_DATA = {
    'first_name': 'Chadwick',
    'last_name': 'Boseman',
    'email': 'chadwick.b@example.com',
    'email2': '',
}


class HoneypotForm(SpamHoneypot, forms.Form):
    """
    Form for testing.
    """
    first_name = forms.CharField()
    last_name = forms.CharField()
    email = forms.EmailField()


class SpamHoneypotTest(SimpleTestCase):
    def test_valid(self) -> None:
        """
        Everything is well.
        """
        form = HoneypotForm(data=HONEYPOT_DATA)
        self.assertTrue(form.is_valid())

    def test_spammer_detected(self) -> None:
        """
        Some spammer filled-in the 'email2' field.

        (Or we forgot to hide the field from the user...).
        """
        data = HONEYPOT_DATA.copy()
        data['email2'] = 'chadwick.b@example.com'
        form = HoneypotForm(data=data)

        message = (
            "^Value found in 'email2' honeypot field: "
            "animal3.forms.tests.test_mixins.HoneypotForm: 'chadwick.b@example.com'$"
        )
        with self.assertRaisesRegex(SuspiciousOperation, message):
            form.is_valid()

    def test_form_class_no_email2(self) -> None:
        """
        Ensure correct error message if form has no honeypot field somehow.
        """
        form = HoneypotForm(data=HONEYPOT_DATA)
        del form.fields['email2']
        message = "^No 'email2' field defined on form class$"
        with self.assertRaisesRegex(ImproperlyConfigured, message):
            form.is_valid()

    def test_template_no_email2(self) -> None:
        """
        Detect common error of forgetting to add invisible 'email2' input.
        """
        data = HONEYPOT_DATA.copy()
        del data['email2']
        form = HoneypotForm(data=data)
        message = "^No 'email2' key found in POST data. Check template.$"
        with self.assertRaisesRegex(ImproperlyConfigured, message):
            form.is_valid()


HONEYPOT_CUSTOM_NAME_DATA = {
    'company': "Three's",
    'account_email': 'john.ritter@example.com',
    'account_email2': '',
}


class HoneypotCustomNameForm(SpamHoneypot, forms.Form):
    """
    Custom honeypot field names.
    """
    # Fields
    company = forms.CharField()
    account_email = forms.CharField()

    # Options
    honeypot_field_name = 'account_email2'


class SpamHoneypotCustomName(SimpleTestCase):
    def test_valid(self) -> None:
        """
        Everything is well.
        """
        form = HoneypotCustomNameForm(data=HONEYPOT_CUSTOM_NAME_DATA)
        self.assertTrue(form.is_valid())

    def test_spammer_detected(self) -> None:
        """
        Some spammer filled-in the 'account_email2' field.

        (Or we forgot to hide the field from the user...).
        """
        data = HONEYPOT_CUSTOM_NAME_DATA.copy()
        data['account_email2'] = 'john.ritter@example.com'
        form = HoneypotCustomNameForm(data=data)

        message = (
            "^Value found in 'account_email2' honeypot field: "
            "animal3.forms.tests.test_mixins.HoneypotCustomNameForm: "
            "'john.ritter@example.com'$"
        )
        with self.assertRaisesRegex(SuspiciousOperation, message):
            form.is_valid()

    def test_form_class_no_honeypot(self) -> None:
        """
        Ensure correct error message if form has no honeypot field somehow.
        """
        form = HoneypotCustomNameForm(data=HONEYPOT_CUSTOM_NAME_DATA)
        del form.fields['account_email2']
        message = "^No 'account_email2' field defined on form class$"
        with self.assertRaisesRegex(ImproperlyConfigured, message):
            form.is_valid()

    def test_template_no_honeypot(self) -> None:
        """
        Detect common error of forgetting to add invisible 'email2' input.
        """
        data = HONEYPOT_CUSTOM_NAME_DATA.copy()
        del data['account_email2']
        form = HoneypotCustomNameForm(data=data)
        message = "^No 'account_email2' key found in POST data. Check template.$"
        with self.assertRaisesRegex(ImproperlyConfigured, message):
            form.is_valid()
