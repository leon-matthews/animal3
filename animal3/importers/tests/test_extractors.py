
from unittest import TestCase

from ..extractors import DumpdataJSON, Extractor

from . import DATA_FOLDER


class ExtractorTest(TestCase):
    def test_cannot_instantiate(self) -> None:
        message = r"^Can't instantiate abstract class Extractor.+"
        with self.assertRaisesRegex(TypeError, message):
            Extractor()                                     # type: ignore[abstract]


class DumpdataJSONTest(TestCase):
    extractor: DumpdataJSON

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        path = DATA_FOLDER / 'blog.json'
        cls.extractor = DumpdataJSON(path)

    def test_fields_category(self) -> None:
        """
        Extract ``blog.category`` field data using `fields()` method.
        """
        # Iterate over all data
        expected_keys = {'pk', 'title', 'slug'}
        for count, fields in enumerate(self.extractor.fields('blog.category'), 1):
            self.assertIsInstance(fields, dict)
            self.assertEqual(fields.keys(), expected_keys)

        self.assertEqual(count, 2)

        # Examine last in detail
        expected = {
            'pk': 2,
            'slug': 'product-news',
            'title': 'Product News',
        }
        self.assertEqual(fields, expected)

    def test_fields_entry(self) -> None:
        """
        Extract ``blog.entry`` field data using `fields()` method.
        """
        # Iterate over all data
        expected_keys = {
            'pk',
            'title',
            'slug',
            'cover_image',
            'published',
            'category',
            'featured',
            'status',
            'created',
            'updated',
        }
        for count, fields in enumerate(self.extractor.fields('blog.entry'), 1):
            self.assertIsInstance(fields, dict)
            self.assertEqual(fields.keys(), expected_keys)

        self.assertEqual(count, 3)

        # Examine last in detail
        expected = {
            'pk': 3,
            'title': 'Safe, Reliable Scaffold J-Planks',
            'slug': 'safe-reliable-scaffold-j-planks',
            'cover_image': 'story/image/2013/09/26/IMG_50661.jpg',
            'published': '2013-09-26T02:18:45Z',
            'category': 1,
            'featured': True,
            'status': 1,
            'created': '2013-09-26T02:26:50.533Z',
            'updated': '2013-10-23T01:03:18.910Z',
        }
        self.assertEqual(fields, expected)

    def test_fields_error(self) -> None:
        """
        Giving an invalid model_tag argument causes KeyError to be thrown.
        """
        # Note that messages given to KeyError are wrapped again in another
        # set of quotes. That was annoying to get to the bottom of!
        message = r"^\"No fields found with model_tag 'no.such.model'\"$"
        with self.assertRaisesRegex(KeyError, message):
            list(self.extractor.fields('no.such.model'))

    def test_json_data_error(self) -> None:
        """
        File contains valid JSON data, but not in the expected dumpdata format.
        """
        path = DATA_FOLDER / 'blog-invalid.json'
        message = (
            r"^Error with JSON record 0: Expected mapping with keys "
            r"\['fields', 'model', 'pk'\], but found \['fields', 'model']$"
        )
        with self.assertRaisesRegex(ValueError, message):
            DumpdataJSON(path)
