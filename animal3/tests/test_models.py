
import datetime
from decimal import Decimal
import logging

from django.test import TestCase
from django.utils import timezone

from animal3.utils.logging import CaptureLogs

from .models import SingletonSample, SlugOnly, TestModel


class SingletonTest(TestCase):
    def test_singleton_lifecycle(self) -> None:
        # 0) No models in database
        self.assertEqual(SingletonSample.objects.count(), 0)

        # 1) First call to ``load()`` creates instance, using default value.
        obj = SingletonSample.load()
        self.assertEqual(SingletonSample.objects.count(), 1)
        self.assertIsInstance(obj, SingletonSample)
        self.assertEqual(str(obj), '$9.99')

        # 2) Second call does nothing but returns cached value
        obj2 = SingletonSample.load()
        self.assertEqual(SingletonSample.objects.count(), 1)
        self.assertIsInstance(obj2, SingletonSample)
        self.assertEqual(str(obj2), '$9.99')
        self.assertTrue(obj is obj2)

        # 3) Change value then save changes
        obj3 = SingletonSample.load()
        assert isinstance(obj3, SingletonSample)
        obj3.price = Decimal('10.00')
        obj3.save()
        self.assertEqual(str(obj3), '$10.00')
        self.assertEqual(SingletonSample.objects.count(), 1)

        # 4) Call to ``load()`` after save should return updated model
        obj4 = SingletonSample.load()
        self.assertEqual(str(obj4), '$10.00')
        self.assertEqual(str(SingletonSample.objects.get(pk=1)), '$10.00')


class TestModelTest(TestCase):
    obj: TestModel

    @classmethod
    def setUpTestData(cls) -> None:
        cls.obj = TestModel.objects.create(name="Annie Wittenmyer")

    def test_model_fields(self) -> None:
        self.assertEqual(self.obj.id, 1)
        self.assertEqual(self.obj.pk, 1)
        self.assertEqual(self.obj.name, 'Annie Wittenmyer')
        self.assertEqual(self.obj.slug, 'annie-wittenmyer')
        self.assertIs(self.obj.price, None)
        self.assertEqual(self.obj.description, '')

    def test_inherited_fields(self) -> None:
        # Ordering
        self.assertEqual(self.obj.ordering, 1)

        # Timestamps
        now = timezone.now()
        created = self.obj.created
        updated = self.obj.updated
        self.assertIsInstance(created, datetime.datetime)
        self.assertIsInstance(updated, datetime.datetime)
        self.assertLess((now - created), datetime.timedelta(seconds=1))
        self.assertLess((now - updated), datetime.timedelta(seconds=1))

    def test_type(self) -> None:
        self.assertEqual(self.obj.type(), 'animal3_tests_test_model')

    def test_signal_handler_run_delete_files(self) -> None:
        """
        Signal handler ran AND delete_files() method run on instance.
        """
        obj = TestModel.objects.create(name="Gonna Biteit")
        with CaptureLogs('animal3.signals', logging.DEBUG) as logs:
            obj.delete()
        messages = [record.message for record in logs.records]
        expected = [
            'Running delete_files() signal handler',
            'Running TestModel.delete_files()',
        ]
        self.assertEqual(messages, expected)

    def test_signal_handler_no_delete_files(self) -> None:
        """
        Signal handler ran, but delete_files() method NOT run on instance.
        """
        obj = SlugOnly.objects.create(slug="soon-be-dead")
        with CaptureLogs('animal3.signals', logging.DEBUG) as logs:
            obj.delete()
        messages = [record.message for record in logs.records]
        expected = [
            'Running delete_files() signal handler',
        ]
        self.assertEqual(messages, expected)

    def test_ordering(self) -> None:
        obj2 = TestModel.objects.create(name="Frances Willard")
        self.assertEqual(obj2.ordering, 2)
