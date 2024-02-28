
from typing import Any, Iterator, Optional, Union

from django.core.exceptions import ImproperlyConfigured
from django.http import HttpRequest


class SessionList:
    """
    Present a list-like collection that saves itself in a Django store.

    The list `self.values` is always available, defaulting to an empty list.
    If you modify it manually, you must take care to call the `self.save()`,
    as the supplied methods do.

    Subclass and ensure that you provide at least a `session_key` string::

        class FavouriteFruits(SessionList):
            session_key = 'favourite_fruits'

    The `session_key` must be unique across all uses of the Django session
    store for this project.
    """
    session_key: Optional[str] = None

    def __init__(self, request: HttpRequest):
        self.request = request
        if self.session_key is None:
            message = "Expected a valid 'session_key' class attribute"
            raise ImproperlyConfigured(message)
        self.values = self.request.session.get(self.session_key, [])

    def append(self, value: str) -> None:
        """
        Append a value a single value to the session.
        """
        self.values.append(value)
        self.save()

    def clear(self) -> None:
        """
        Remove all values.
        """
        self.values = []
        self.save()

    def index(self, value: Any) -> int:
        """
        Return first index of value.

        Raises ValueError if the value is not present
        """
        return int(self.values.index(value))

    def purge(self, value: Any) -> None:
        """
        Delete ALL occurrences of value entirely from the list.

        No exceptions are raised, even if `value` is not present
        in `self.values`.
        """
        try:
            while True:
                self.remove(value)
        except ValueError:
            pass
        self.save()

    def remove(self, value: Any) -> None:
        """
        Remove first occurrence of value.

        Raises ValueError if the value is not present.
        """
        self.values.remove(value)
        self.save()

    def save(self) -> None:
        """
        Save changes to `self.values` back to session.
        """
        assert self.session_key is not None
        self.request.session[self.session_key] = self.values
        self.request.session.modified = True

    def __contains__(self, value: Any) -> bool:
        return value in self.values

    def __delitem__(self, index: Union[slice, int]) -> None:
        del self.values[index]
        self.save()

    def __getitem__(self, index: Union[slice, int]) -> Any:
        return self.values[index]

    def __iter__(self) -> Iterator:
        return iter(self.values)

    def __len__(self) -> int:
        return len(self.values)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({repr(self.values)})"

    def __setitem__(self, index: int, value: Any) -> None:
        self.values[index] = value
        self.save()
