
from datetime import datetime

from django.utils import timezone
from django.test import SimpleTestCase

from . import ExampleModel


class UploadToTest(SimpleTestCase):
    def test_upload_to(self) -> None:
        """
        With no field name given path is: '{app}/{model}/{file}'
        """
        example = ExampleModel()
        func = example.file_plain.field.upload_to
        self.assertEqual(
            func(example, 'example1.png'),
            'animal3/example_model/example1.png')

    def test_upload_to_clean_filename(self) -> None:
        example = ExampleModel()
        func = example.file_plain.field.upload_to
        self.assertEqual(
            func(example, 'Good    Photo! .jpg'),
            'animal3/example_model/good-photo.jpg')


class UploadToDatedTest(SimpleTestCase):
    def test_upload_to_dated(self) -> None:
        """
        Use UTC-date folders to spread fields files around.
        """
        example = ExampleModel()
        example.created = timezone.make_aware(datetime(2021, 6, 17))
        func = example.file_dated.field.upload_to
        path = func(example, 'Example 1.png')
        self.assertEqual(path, 'animal3/example_model/2021/06/17/example-1.png')

    def test_model_no_created_field(self) -> None:
        """
        As above, but uses todays date because created is empty.
        """
        example = ExampleModel()
        example.created = None
        func = example.file_dated.field.upload_to
        path = func(example, 'Example 2.png')
        # Check date using regex, eg. '.../2021/06/17/...'
        pattern = r'animal3/example_model/20\d\d/\d\d/\d\d/example-2.png'
        self.assertRegex(path, pattern)


class UploadToHashedTest(SimpleTestCase):
    def test_upload_to_hashed(self) -> None:
        """
        Use 2-character hex hash to spread files across 256 folders.
        """
        example = ExampleModel()
        func = example.file_hashed.field.upload_to
        self.assertEqual(
            func(example, 'Example 3.png'),
            'animal3/example_model/50/example-3.png',
        )


class UploadToObsfucatedTest(SimpleTestCase):
    def test_upload_to_obsfucated(self) -> None:
        example = ExampleModel()
        func = example.file_obsfucated.field.upload_to

        with self.settings(SECRET_KEY='abcdefghijklmnopqrstuvwxyz'):
            relpath = func(example, 'Example 4.png')

        self.assertEqual(
            relpath,
            'animal3/example_model/ec/ec804c800c8e988f/example-4.png',
        )
