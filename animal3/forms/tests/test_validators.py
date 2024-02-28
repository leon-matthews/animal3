
from unittest import TestCase

from django.core.exceptions import ImproperlyConfigured, ValidationError

from animal3.utils.testing import DocTestLoader

from .. import validators
from ..validators import (
    JSONDictValidator, JSONListValidator, NumericRange, URLValidator,
)


class DocTests(TestCase, metaclass=DocTestLoader, test_module=validators):
    pass


class JSONDictValidatorTest(TestCase):
    """
    Validate JSON dictionary values.
    """
    def test_invalid_container(self) -> None:
        validate = JSONDictValidator()
        message = r"Container must be a dict, found: 'list'"
        with self.assertRaisesRegex(ValidationError, message):
            validate([1, 2, 3])

    def test_invalid_key(self) -> None:
        validate = JSONDictValidator(key_type=int, value_type=int)
        message = r"Keys must all be 'int', but key 'fruit' is 'str'"
        with self.assertRaisesRegex(ValidationError, message):
            validate({'fruit': 'banana'})

    def test_invalid_value(self) -> None:
        validate = JSONDictValidator(value_type=int)
        message = r"Values must all be 'int', but container\['fruit'\] is 'str'"
        with self.assertRaisesRegex(ValidationError, message):
            validate({'fruit': 'banana'})

    def test_valid(self) -> None:
        validate = JSONDictValidator(key_type=str, value_type=int)
        data = {
            'a': 10,
            'b': 11,
            'c': 12,
            'd': 13,
            'e': 14,
            'f': 15,
        }
        validate(data)


class JSONListValidatorTest(TestCase):
    """
    Validate JSON list values.
    """
    def test_invalid_container(self) -> None:
        validate = JSONListValidator()
        message = r"Container must be a list, found: 'dict'"
        with self.assertRaisesRegex(ValidationError, message):
            validate({'a': 1})

    def test_invalid_value(self) -> None:
        validate = JSONListValidator(value_type=int)
        message = r"Values must all be 'int', but container\[3\] is 'str'"
        with self.assertRaisesRegex(ValidationError, message):
            validate([1, 2, 4, '8', 16])

    def test_valid(self) -> None:
        validate = JSONListValidator(value_type=int)
        validate([2, 3, 5, 7, 11, 13, 17, 19, 23, 29])


class NumericRangeTest(TestCase):
    def test_improperly_configured(self) -> None:
        message = 'Bottom should be less than top'
        with self.assertRaisesRegex(ImproperlyConfigured, message):
            NumericRange(1, 1)

    def test_range_valid(self) -> None:
        validate = NumericRange(10, 20)
        validate(10)
        validate(15)
        validate(20)

    def test_equal(self) -> None:
        v1 = NumericRange(10, 20)
        v2 = NumericRange(10, 20)
        self.assertEqual(v1, v2)

    def test_not_equal(self) -> None:
        v1 = NumericRange(10, 20)
        v2 = NumericRange(10, 30)
        self.assertNotEqual(v1, v2)

    def test_value_too_small(self) -> None:
        validate = NumericRange(10, 20)
        message = r'Too small. Enter a number from 10 to 20.'
        with self.assertRaisesRegex(ValidationError, message):
            validate(9)

    def test_value_too_large(self) -> None:
        validate = NumericRange(10, 20)
        message = r'Too large. Enter a number from 10 to 20.'
        with self.assertRaisesRegex(ValidationError, message):
            validate(21)

    def test_value_invalid(self) -> None:
        validate = NumericRange(10, 20)
        message = r'Enter a valid number.'
        with self.assertRaisesRegex(ValidationError, message):
            validate('banana')                              # type: ignore[arg-type]


class URLValidatorDefaultTest(TestCase):
    """
    Default behaviour of URLValidator matches that of Django's own.
    """
    def setUp(self) -> None:
        self.validator = URLValidator()

    def test_absolute_paths(self) -> None:
        """
        The default is to disallow paths, just like Django's URLValidator.
        """
        message = 'Enter a full URL.'
        with self.assertRaisesRegex(ValidationError, message):
            self.validator('/')

        with self.assertRaisesRegex(ValidationError, message):
            self.validator('/absolute/paths/are/not/always/okay')

    def test_bad_url(self) -> None:
        message = "Enter a valid URL."
        with self.assertRaisesRegex(ValidationError, message):
            self.validator('http://example')

    def test_relative_paths(self) -> None:
        message = 'Enter a full URL.'
        with self.assertRaisesRegex(ValidationError, message):
            self.validator('relative/paths/not/okay.img')

    def test_full_urls(self) -> None:
        self.validator('https://example.com')
        self.validator('https://example.com/')
        self.validator('https://example.com/index.html')

    def test_empty(self) -> None:
        """
        Leave empty values for `blank=False` to deal with.
        """
        self.validator('')

    def test_improperly_configured(self) -> None:
        """
        At least one type of URL must be allowed.
        """
        message = "At least one type of URL must be allowed"
        with self.assertRaisesRegex(ImproperlyConfigured, message):
            URLValidator(allow_full=False, allow_paths=False)


class URLValidatorAllowPathsTest(TestCase):
    """
    Setting 'allow_paths' to true allows absolute paths to local site.
    """
    def setUp(self) -> None:
        self.validator = URLValidator(allow_paths=True)

    def test_absolute_paths(self) -> None:
        """
        No exceptions thrown for absolute paths, if 'allow_paths' is true.
        """
        self.validator('/')
        self.validator('/absolute/paths/are/okay')

    def test_bad_path(self) -> None:
        message = 'Not a valid path.'
        with self.assertRaisesRegex(ValidationError, message):
            self.validator('/this is not a good path')

    def test_bad_url(self) -> None:
        message = "Enter a valid URL or path."
        with self.assertRaisesRegex(ValidationError, message):
            self.validator('http://example')

    def test_relative_paths(self) -> None:
        """
        Relative paths are still verboten.
        """
        validator = URLValidator(allow_paths=True)
        message = 'Path must start with a forward-slash'
        with self.assertRaisesRegex(ValidationError, message):
            validator('relative/paths/not/okay.img')

    def test_full_urls(self) -> None:
        self.validator('https://example.com')
        self.validator('https://example.com/')
        self.validator('https://example.com/index.html')

    def test_empty(self) -> None:
        """
        Leave empty values for `blank=False` to deal with.
        """
        self.validator('')


class URLValidatorNoFullTest(TestCase):
    """
    Setting 'allow_full' to false disallows links to external sites.
    """
    def setUp(self) -> None:
        self.validator = URLValidator(allow_full=False, allow_paths=True)

    def test_absolute_paths(self) -> None:
        """
        No exceptions thrown for absolute paths, if 'allow_paths' is true.
        """
        self.validator('/')
        self.validator('/absolute/paths/are/okay')

    def test_relative_paths(self) -> None:
        """
        Relative paths are still verboten.
        """
        validator = URLValidator(allow_paths=True)
        message = 'Path must start with a forward-slash'
        with self.assertRaisesRegex(ValidationError, message):
            validator('relative/paths/not/okay.img')

    def test_bad_path(self) -> None:
        message = 'Not a valid path.'
        with self.assertRaisesRegex(ValidationError, message):
            self.validator('/this is not a good path')

    def test_bad_url(self) -> None:
        message = "Enter an absolute path, not full URL."
        with self.assertRaisesRegex(ValidationError, message):
            self.validator('http://example')

    def test_full_urls(self) -> None:
        """
        Do not allow full URLs.
        """
        message = 'Enter an absolute path, not full URL'
        with self.assertRaisesRegex(ValidationError, message):
            self.validator('https://example.com/')

    def test_empty(self) -> None:
        """
        Leave empty values for `blank=False` to deal with.
        """
        self.validator('')
