"""
Investigate edge behaviour of Django model forms.

Specifically, data fields with `auto_now` and `auto_now_add` attributes make
bulk loading of data into the database tricky.
"""

import datetime

from django.forms import ModelForm
from django.test import TestCase

from animal3.django.utils import model_to_dict
from animal3.tests.models import DatedModel


class DatedModelForm(ModelForm):
    class Meta:
        exclude = ()
        model = DatedModel


class DatedModelTest(TestCase):
    """
    Create model instances directly, not via model form.
    """
    auto_now_fields = ('ctime', 'mtime')

    def test_model_field_is_editable(self) -> None:
        """
        Both types of automatic date fields have `editable` set false.
        """
        obj = DatedModel(name="Unsaved")
        is_editable = {}
        for field in obj._meta.get_fields():
            is_editable[field.name] = field.editable

        expected = {
            'id': True,
            'name': True,
            'date': True,
            'ctime': False,
            'mtime': False,
        }
        self.assertEqual(is_editable, expected)

    def test_form_field_not_created(self) -> None:
        """
        Model form doesn't even create fields for non-editable model fields.
        """
        form = DatedModelForm()
        self.assertEqual(form.fields.keys(), set(['date', 'name']))

    def test_not_saved(self) -> None:
        """
        Automatic date fields start as None.
        """
        obj = DatedModel(name="Unsaved")
        data = model_to_dict(obj)

        self.assertEqual(data['id'], None)
        self.assertEqual(data['name'], 'Unsaved')
        for date_field in self.auto_now_fields:
            self.assertIsNone(data[date_field])

        field_names = sorted(data.keys())
        expected = ['ctime', 'date', 'id', 'mtime', 'name']
        self.assertEqual(field_names, expected)

    def test_create(self) -> None:
        """
        Manager's `create()` method causes datetimes to be created.
        """
        obj = DatedModel.objects.create(name="Create")
        data = model_to_dict(obj)

        self.assertEqual(data['id'], 1)
        self.assertEqual(data['name'], 'Create')
        for date_field in self.auto_now_fields:
            self.assertIsInstance(data[date_field], datetime.datetime)

    def test_model_form_valid(self) -> None:
        """
        No date fields in cleaned data, only in created model.
        """
        data = {'name': 'Name Only'}
        form = DatedModelForm(data=data)
        self.assertTrue(form.is_valid())
        expected = {
            'date': None,
            'name': 'Name Only',
        }
        self.assertEqual(form.cleaned_data, expected)

        obj = form.save()
        data = model_to_dict(obj)
        self.assertEqual(data['id'], 1)
        self.assertEqual(data['name'], 'Name Only')
        for date_field in self.auto_now_fields:
            self.assertIsInstance(data[date_field], datetime.datetime)

    def test_not_editable_fields(self) -> None:
        """
        ModelForm knows how to convert string dates into models fields.
        """
        data = {
            'name': 'Give Dates',
            'date': '2023-05-18',
        }
        form = DatedModelForm(data=data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data.keys(), set(['date', 'name']))
        self.assertEqual(form.cleaned_data['name'], 'Give Dates')

        # Timezone-aware datetime object with current timezone
        self.assertIsInstance(form.cleaned_data['date'], datetime.datetime)

    def test_automatic_dates_ignored(self) -> None:
        """
        Model form just ignores attempts to pass dates manually.
        """
        data = {
            'name': 'Give ALL Dates',
            'date': '2023-05-18',
            'ctime': '2023-05-18',
            'mtime': '2023-05-18',
        }
        form = DatedModelForm(data=data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data.keys(), set(('date', 'name')))
