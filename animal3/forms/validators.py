"""
Django validators.

See also country validators in ``animal3.utils.iso_3166``
"""

import re
from typing import Any, Optional, Type

from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.core.validators import URLValidator as DjangoURLValidator
from django.utils.deconstruct import deconstructible

from animal3.utils.urls import is_path_only


@deconstructible
class JSONDictValidator:
    """
    Ensure JSON value is a dictionary.

        >>> validator = JSONDictValidator()
        >>> data = {'a': 1, 'b': 2, 'c': 3}
        >>> validator(data)

    Optionally, restrict keys to a given type:

        >>> validator = JSONDictValidator(key_type=str)
        >>> validator(data)

    Also optionally, restrict the type of the values:

        >>> validator = JSONDictValidator(key_type=str, value_type=int)
        >>> validator(data)

    """
    def __init__(
        self,
        key_type: Optional[Type] = None,
        value_type: Optional[Type] = None
    ):
        """
        Initialiser.

        Args:
            require_type:
                Optionally provide a type to check types against.
        """
        self.key_type = key_type
        self.value_type = value_type

    def __call__(self, container: object) -> None:
        """
        Run validation against given value.

        Raises:
            ValidationError:
                If container type is not a list, or if values inside the
                container do not match `require_type` (if not None).

        Returns:
            None
        """
        # Check container
        if not isinstance(container, dict):
            raise ValidationError(
                f"Container must be a dict, found: {type(container).__name__!r}"
            )

        # Finished?
        if self.key_type is None and self.value_type is None:
            return

        # Check container
        for key, value in container.items():

            # Check key?
            if self.key_type is not None:
                if not isinstance(key, self.key_type):
                    raise ValidationError(
                        f"Keys must all be {self.key_type.__name__!r}, "
                        f"but key {key!r} is {type(value).__name__!r}"
                    )

            # Check value?
            if self.value_type is not None:
                if not isinstance(value, self.value_type):
                    raise ValidationError(
                        f"Values must all be {self.value_type.__name__!r}, "
                        f"but container[{key!r}] is {type(value).__name__!r}"
                    )


@deconstructible
class JSONListValidator:
    """
    Ensure JSON value is a list.

        >>> validator = JSONListValidator()
        >>> validator([1, '2', 3.0])

    Optionally, restrict values inside list to a particular type.

        >>> validator = JSONListValidator(value_type=int)
        >>> validator([1, 2, 3])

    """
    def __init__(self, value_type: Optional[Type] = None):
        """
        Initialiser.

        Args:
            require_type:
                Optionally provide a type to check types against.
        """
        self.value_type = value_type

    def __call__(self, container: Any) -> None:
        """
        Run validation against given value.

        Raises:
            ValidationError:
                If container type is not a list, or if values inside the
                container do not match `require_type` (if not None).

        Returns:
            None
        """
        # Check container
        if not isinstance(container, list):
            raise ValidationError(
                f"Container must be a list, found: {type(container).__name__!r}"
            )

        # Finished?
        if self.value_type is None:
            return

        # Check values
        for index, value in enumerate(container):
            if not isinstance(value, self.value_type):
                raise ValidationError(
                    f"Values must all be {self.value_type.__name__!r}, "
                    f"but container[{index}] is {type(value).__name__!r}"
                )


@deconstructible
class NumericRange:
    """
    Number must be within the (inclusive) range given.

        >>> d6 = NumericRange(1, 6)
        >>> d6(1)
        >>> d6(4)

    """
    def __init__(self, bottom: float, top: float):
        if bottom >= top:
            raise ImproperlyConfigured("Bottom should be less than top")
        self.bottom = bottom
        self.top = top

    def __call__(self, number: float) -> None:
        """
        Run validation against given value.

        Raises:
            ValidationError:
                If container type is outside range.

        Returns:
            None
        """
        try:
            if number < self.bottom or number > self.top:
                if number < self.bottom:
                    message = "Too small."
                else:
                    message = "Too large."
                message += " Enter a number from {} to {}."
                raise ValidationError(message.format(self.bottom, self.top))
        except (TypeError, ValueError):
            raise ValidationError('Enter a valid number.')

    def __eq__(self, other: Any) -> bool:
        return bool(
            (self.bottom == other.bottom)
            and (self.top == other.top)
        )


@deconstructible
class URLValidator:
    """
    Extend Django's URLValidator to allow paths to local site.

    Without arguments its behaviour is the same as Django's built-in:

        >>> validator = URLValidator()
        >>> validator('https://example.com/as/are/full/urls')

    Use the new 'allow_paths` argument to relax rules for local URLs.

        >>> validator = URLValidator(allow_paths=True)
        >>> validator('/absolute/paths/are/okay')

    """
    def __init__(self, *, allow_full: bool = True, allow_paths: bool = False):
        """
        Initialiser.

        Args:
            allow_full:
                Allow full URLs, eg. 'https://example.com/some/url.png'
            allow_paths:
                Absolute paths are allowed, eg. '/some/url.png'

        """
        self.allow_full = allow_full
        self.allow_paths = allow_paths

        # Check for stupid
        if not (self.allow_full or self.allow_paths):
            raise ImproperlyConfigured("At least one type of URL must be allowed.")

    def __call__(self, url: str) -> None:
        """
        Run validation against given value.

        Raises:
            ValidationError:
                If URL does not validate against current rules.

        Returns:
            None
        """
        # Ignore empty values
        if not url:
            return

        # Path given
        if is_path_only(url, allow_relative=True):
            # No paths allowed
            if not self.allow_paths:
                raise ValidationError("Enter a full URL.")

            # Not absolute
            if not url.startswith('/'):
                raise ValidationError("Path must start with a forward-slash")

            # Check format
            match = re.match(r"^(?:[/?#][^\s]*)$", url)
            if not match:
                raise ValidationError("Not a valid path.")

            # It's a good 'un!
            return

        # Disallow full URLs
        if not self.allow_full:
            raise ValidationError("Enter an absolute path, not full URL.")

        # Check format of full URL
        message = "Enter a valid URL."
        if self.allow_paths:
            message = "Enter a valid URL or path."
        url_validator = DjangoURLValidator(message=message)
        url_validator(url)
