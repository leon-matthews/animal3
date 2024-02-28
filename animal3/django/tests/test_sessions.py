
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpRequest
from django.test import RequestFactory, SimpleTestCase

from animal3.utils.testing import decorate_request

from ..sessions import SessionList


class MySessionList(SessionList):
    """
    Sub-class of SessionList for testing.
    """
    session_key = 'my_list'


class NoSessionKey(SessionList):
    """
    As per `MySessionList`, but we forget to set a session_key.
    """
    pass


def make_empty(request: HttpRequest) -> MySessionList:
    session_list = MySessionList(request)
    return session_list


def make_full(request: HttpRequest) -> MySessionList:
    session_list = MySessionList(request)
    session_list.append('One')
    session_list.append('Two')
    session_list.append('Two')
    session_list.append('Three')
    session_list.append('Three')
    session_list.append('Three')
    return session_list


class TestSessionList(SimpleTestCase):
    factory = RequestFactory()

    def setUp(self) -> None:
        request = self.factory.get('/')
        self.request = decorate_request(request, {})

    def test_init(self) -> None:
        """
        Catch easy to make errors early.
        """
        store = MySessionList(self.request)
        self.assertEqual(store.values, [])

    def test_init_no_session_key(self) -> None:
        """
        Sub-classes must define a valid 'session_key'.
        """
        message = "Expected a valid 'session_key' class attribute"
        with self.assertRaisesRegex(ImproperlyConfigured, message):
            NoSessionKey(self.request)

    def test_append(self) -> None:
        store = make_empty(self.request)
        self.assertEqual(store.values, [])

        store.append('Single')
        self.assertEqual(store.values, ['Single'])
        store.append('Double')
        self.assertEqual(store.values, ['Single', 'Double'])

    def test_clear(self) -> None:
        store = make_full(self.request)
        self.assertEqual(store.values, ['One', 'Two', 'Two', 'Three', 'Three', 'Three'])
        store.clear()
        self.assertEqual(store.values, [])

    def test_contains(self) -> None:
        store = make_full(self.request)
        self.assertTrue('Two' in store)
        self.assertFalse('Four' in store)

    def test_delitem(self) -> None:
        store = make_full(self.request)
        self.assertEqual(store.values, ['One', 'Two', 'Two', 'Three', 'Three', 'Three'])
        del store[0]
        self.assertEqual(store.values, ['Two', 'Two', 'Three', 'Three', 'Three'])
        del store[-1]
        self.assertEqual(store.values, ['Two', 'Two', 'Three', 'Three'])
        del store[-2:]
        self.assertEqual(store.values, ['Two', 'Two'])

        with self.assertRaises(IndexError):
            del store[97]

    def test_getitem(self) -> None:
        store = make_full(self.request)
        self.assertEqual(store[0], 'One')
        self.assertEqual(store[-1], 'Three')
        self.assertEqual(store[1:3], ['Two', 'Two'])

        with self.assertRaises(IndexError):
            store[13]

    def test_index(self) -> None:
        store = make_full(self.request)
        self.assertEqual(store.index('One'), 0)
        self.assertEqual(store.index('Two'), 1)
        self.assertEqual(store.index('Three'), 3)
        with self.assertRaises(ValueError):
            store.index('Four')

    def test_iter(self) -> None:
        store = make_full(self.request)
        seen = set()
        for number in store:
            seen.add(number)
        self.assertEqual(seen, {'One', 'Two', 'Three'})

    def test_len(self) -> None:
        self.assertEqual(len(make_empty(self.request)), 0)
        self.assertEqual(len(make_full(self.request)), 6)

    def test_purge(self) -> None:
        store = make_full(self.request)
        self.assertEqual(store.values, ['One', 'Two', 'Two', 'Three', 'Three', 'Three'])

        store.purge('Three')
        self.assertEqual(store.values, ['One', 'Two', 'Two'])
        store.purge('Two')
        self.assertEqual(store.values, ['One'])
        store.purge('One')
        self.assertEqual(store.values, [])

        # No exception thrown:
        store.purge('Four')

    def test_remove(self) -> None:
        store = make_full(self.request)
        self.assertEqual(store.values, ['One', 'Two', 'Two', 'Three', 'Three', 'Three'])

        store.remove('Three')
        self.assertEqual(store.values, ['One', 'Two', 'Two', 'Three', 'Three'])
        store.remove('Three')
        self.assertEqual(store.values, ['One', 'Two', 'Two', 'Three'])
        store.remove('Three')
        self.assertEqual(store.values, ['One', 'Two', 'Two'])

        with self.assertRaises(ValueError):
            store.remove('Three')

    def test_repr_and_str(self) -> None:
        """
        Convert object to string.

        (We're making `self.__repr__()` pull double duty and handle str() too)
        """
        empty = make_empty(self.request)
        expected = "MySessionList([])"
        self.assertEqual(repr(empty), expected)
        self.assertEqual(str(empty), expected)

        full = make_full(self.request)
        expected = "MySessionList(['One', 'Two', 'Two', 'Three', 'Three', 'Three'])"
        self.assertEqual(repr(full), expected)
        self.assertEqual(str(full), expected)

    def test_setitem(self) -> None:
        store = make_full(self.request)
        self.assertEqual(store.values, ['One', 'Two', 'Two', 'Three', 'Three', 'Three'])
        store[2] = 'Three'
        store[3] = 'Four'
        store[4] = 'Five'
        store[5] = 'Six'
        self.assertEqual(store.values, ['One', 'Two', 'Three', 'Four', 'Five', 'Six'])

        with self.assertRaises(IndexError):
            store[6] = 'Seven'
