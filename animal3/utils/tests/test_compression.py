
from django.test import TestCase

from .. import compression


class TestCompression(TestCase):
    def test_gzip(self) -> None:
        data = ("The quick brown fox jumped over the lazy dog." * 100).encode('utf-8')
        self.assertEqual(len(data), 4500)

        compressed = compression.compress(data, 'gzip')
        self.assertEqual(len(compressed), 80)

        uncompressed = compression.decompress(compressed, 'gzip')
        self.assertEqual(len(uncompressed), 4500)
        self.assertEqual(uncompressed, data)

    def test_bzip2(self) -> None:
        data = ("The quick brown fox jumped over the lazy dog." * 100).encode('utf-8')
        self.assertEqual(len(data), 4500)

        compressed = compression.compress(data, 'bzip2')
        self.assertEqual(len(compressed), 141)

        uncompressed = compression.decompress(compressed, 'bzip2')
        self.assertEqual(len(uncompressed), 4500)
        self.assertEqual(uncompressed, data)

    def test_xz(self) -> None:
        data = ("The quick brown fox jumped over the lazy dog." * 100).encode('utf-8')
        self.assertEqual(len(data), 4500)

        compressed = compression.compress(data, 'xz')
        self.assertEqual(len(compressed), 140)

        uncompressed = compression.decompress(compressed, 'xz')
        self.assertEqual(len(uncompressed), 4500)
        self.assertEqual(uncompressed, data)

    def test_unknown_compress_method(self) -> None:
        with self.assertRaises(KeyError):
            compression.compress(b'', 'super')
