
from django.test import override_settings, SimpleTestCase

from animal3.utils.testing import DocTestLoader

from .. import algorithms
from ..algorithms import (
    compare_digests,
    create_digest,
    find_before_after,
    flatten,
    lstrip_iterable,
    merge_data,
    rstrip_iterable,
    strip_iterable,
)


PRIMES = (
    2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47,
    53, 59, 61, 67, 71, 73, 79, 83, 89, 97,
)


class DocTests(SimpleTestCase, metaclass=DocTestLoader, test_module=algorithms):
    pass


@override_settings(SECRET_KEY='5w0rdf1sh')
class CompareDigestTest(SimpleTestCase):
    def test_same_input_same_output(self) -> None:
        message = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        digest1 = create_digest(message)
        digest2 = create_digest(message)
        self.assertTrue(compare_digests(digest1, digest2))

    def test_odd_numbered_lengths(self) -> None:
        digest = '1234567'
        self.assertEqual(len(digest), 7)
        self.assertTrue(compare_digests(digest, digest))


@override_settings(SECRET_KEY='Sw0rdfi5h')
class CreateDigestTest(SimpleTestCase):
    def test_create_digest(self) -> None:
        digest = create_digest('abcdefghijklmnopqrstuvwxyz')
        self.assertEqual(len(digest), 128)
        expected = (
            'd41cc7db57278d35fe9d973c945ed2bdcd8efbcc62bb31279ea990a97d362b3e'
            '30d79a54788f9393a452584b771cfb3d0c20434bb5592d0de88eadc7ffd6db11'
        )
        self.assertEqual(digest, expected)

    def test_max_length(self) -> None:
        digest = create_digest('abcdefghijklmnopqrstuvwxyz', 16)
        self.assertEqual(len(digest), 16)
        self.assertEqual(digest, 'd41cc7db57278d35')


class FindBeforeAfterTest(SimpleTestCase):
    def test_empty(self) -> None:
        before, after = find_before_after([], None)
        self.assertIs(before, None)
        self.assertIs(after, None)

    def test_duplicates(self) -> None:
        """
        The first match is used (and lets mix up the types too).
        """
        fibbonacci = ['zero', 'one', 'one', 'two', 'three', 'four']
        before, after = find_before_after(fibbonacci, 'one')
        self.assertEqual(before, 'zero')
        self.assertEqual(after, 'one')

    def test_found(self) -> None:
        before, after = find_before_after(PRIMES, 47)
        self.assertEqual(before, 43)
        self.assertEqual(after, 53)

    def test_found_first(self) -> None:
        before, after = find_before_after(PRIMES, 2)
        self.assertIs(before, None)
        self.assertEqual(after, 3)

    def test_found_first_wrap(self) -> None:
        before, after = find_before_after(PRIMES, 2, wrap=True)
        self.assertIs(before, 97)
        self.assertEqual(after, 3)

    def test_found_last(self) -> None:
        before, after = find_before_after(PRIMES, 97)
        self.assertEqual(before, 89)
        self.assertIs(after, None)

    def test_found_last_wrap(self) -> None:
        before, after = find_before_after(PRIMES, 97, wrap=True)
        self.assertEqual(before, 89)
        self.assertIs(after, 2)

    def test_not_found(self) -> None:
        before, after = find_before_after(PRIMES, 20)
        self.assertIs(before, None)
        self.assertIs(after, None)


class FlattenTest(SimpleTestCase):
    def test_plain_list(self) -> None:
        iterable = range(1, 5)
        self.assertEqual(
            list(flatten(iterable)),
            [1, 2, 3, 4],
        )

    def test_leave_strings_alone(self) -> None:
        """
        Don't iterate over each of the characters in a string.
        """
        iterable = ['Leon', 'Matthews']
        self.assertEqual(
            list(flatten(iterable)),
            ['Leon', 'Matthews'],
        )

    def test_nested(self) -> None:
        iterable = [
            [1, 2, 3],
            [4, 5, 6],
            [7],
            [8, 9]
        ]
        self.assertEqual(
            list(flatten(iterable)),
            [1, 2, 3, 4, 5, 6, 7, 8, 9],
        )

    def test_nested_more(self) -> None:
        iterable = [
            1,
            2,
            [3, 4, [5], ['hi']],
            [6, [
                [[7, 'hello']]]],
        ]
        self.assertEqual(
            list(flatten(iterable)),
            [1, 2, 3, 4, 5, 'hi', 6, 7, 'hello']
        )


class TestMergeData(SimpleTestCase):
    def test_small(self) -> None:
        """
        Override single existing key.
        """
        first = {'a': 1, 'b': 2, 'c': 3}
        second = {'b': 10}
        merged = merge_data(first, second)
        expected = {'a': 1, 'b': 10, 'c': 3}
        self.assertEqual(merged, expected)

    def test_small_new_key(self) -> None:
        """
        Adding new keys is allowed.
        """
        first = {'a': 1, 'b': 2, 'c': 3}
        second = {'b': 10, 'd': 4}
        merged = merge_data(first, second)
        expected = {'a': 1, 'b': 10, 'c': 3, 'd': 4}
        self.assertEqual(merged, expected)

    def test_merge_two_lists(self) -> None:
        first = {'a': [1, 2, 3]}
        second = {'a': [2, 3, 4]}
        merged = merge_data(first, second)
        self.assertEqual(merged, {'a': [1, 2, 3, 4]})

    def test_merge_three(self) -> None:
        first = {'a': 1, 'b': 2, 'c': 3}
        second = {'a': 100, 'd': 4}
        third = {'a': 10, 'b': 20}
        merged = merge_data(first, second, third)
        expected = {'a': 10, 'b': 20, 'c': 3, 'd': 4}
        self.assertEqual(merged, expected)

    def test_one_nested(self) -> None:
        """
        Nested dict in first must be merged into second.
        """
        first = {
            'name': 'First',
            'details': {
                'age': 43,
                'sex': 'M',
            },
        }
        second = {
            'name': 'Second',
        }

        merged = merge_data(first, second)
        expected = {
            'name': 'Second',
            'details': {
                'age': 43,
                'sex': 'M',
            },
        }
        self.assertEqual(merged, expected)

    def test_both_nested(self) -> None:
        """
        Override existing key in nested.
        """
        first = {
            'name': 'First',
            'details': {
                'age': 43,
                'sex': 'M',
            },
        }
        second = {
            'name': 'Second',
            'details': {
                'age': 11,
            },
        }

        merged = merge_data(first, second)
        expected = {
            'details': {
                'age': 11,
                'sex': 'M'
            },
            'name': 'Second',
        }
        self.assertEqual(merged, expected)


class StripIterable(SimpleTestCase):
    def test_lstrip_iterable(self) -> None:
        iterable = (None, None, 1, None, 2, None)
        expected = [1, None, 2, None]
        self.assertEqual(lstrip_iterable(iterable), expected)

    def test_rstrip_iterable(self) -> None:
        iterable = (None, 1, None, 2, None, None)
        expected = [None, 1, None, 2]
        self.assertEqual(rstrip_iterable(iterable), expected)

    def test_strip_iterable(self) -> None:
        iterable = (None, None, 1, None, 2, None, None)
        expected = [1, None, 2]
        self.assertEqual(strip_iterable(iterable), expected)
