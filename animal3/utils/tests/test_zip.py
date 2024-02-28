
import os.path
from pathlib import Path
import tempfile
from unittest import TestCase
import zipfile

from ..zip import make_prefixed_zipfile, ZipFile

from . import DATA_FOLDER


class ZipFileTest(TestCase):
    path: str
    zip: ZipFile

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.path = os.path.join(DATA_FOLDER, 'bean.zip')
        cls.zip = ZipFile(cls.path)

    def test_file_list(self) -> None:
        self.assertEqual(
            sorted(self.zip.names),
            ['bean.txt', 'bean2.rst', 'bean5.rtf'],
        )

    def test_read_file(self) -> None:
        self.assertEqual(self.zip.read('bean.txt'), b"Lima bean\n")
        self.assertEqual(self.zip.read('bean2.rst'), b"Red bean\n")
        self.assertEqual(self.zip.read('bean5.rtf'), b"Mung bean\n")

    def test_error_file_not_found(self) -> None:
        message = "There is no item named 'no-such-file.txt' in the archive"
        with self.assertRaisesRegex(FileNotFoundError, message):
            self.zip.read('no-such-file.txt')

    def test_error_not_zip(self) -> None:
        path = Path(DATA_FOLDER) / 'haiku.txt'
        message = "File is not a zip file: haiku.txt"
        with self.assertRaisesRegex(zipfile.BadZipfile, message):
            ZipFile(str(path))

    def test_repr(self) -> None:
        self.assertEqual(repr(self.zip), "ZipFile('bean.zip')")

    def test_str(self) -> None:
        self.assertEqual(str(self.zip), "ZipFile('bean.zip')")


class MakePrefixedZipfileTest(TestCase):
    input_folder: Path
    output_folder: tempfile.TemporaryDirectory

    @classmethod
    def setUpClass(cls) -> None:
        cls.input_folder = DATA_FOLDER
        cls.output_folder = tempfile.TemporaryDirectory(prefix='test_prefixed_zip_file')

    @classmethod
    def tearDownClass(cls) -> None:
        cls.output_folder.cleanup()

    def test_make_prefixed_zip_file(self) -> None:
        # Prepare arguments
        files = sorted(self.input_folder.glob('bean*'))
        output = Path(self.output_folder.name) / 'bean.zip'

        # Create
        self.assertFalse(output.is_file())
        created = make_prefixed_zipfile(files, output)
        self.assertIsInstance(created, Path)
        self.assertEqual(created.name, 'bean.zip')

        # Check
        self.assertTrue(output.is_file())
        self.assertTrue(zipfile.is_zipfile(output))
        z = ZipFile(output)
        names = sorted(z.names)
        expected = [
            'bean/bean.txt',
            'bean/bean.zip',
            'bean/bean2.rst',
            'bean/bean5.rtf',
        ]
        self.assertEqual(names, expected)

    def test_already_exists(self) -> None:
        # Create empty file
        output = Path(self.output_folder.name) / 'exists.zip'
        self.assertFalse(output.is_file())
        output.touch()
        self.assertTrue(output.is_file())

        # Exception should be thrown
        message = r"Output path already exists: /.*/exists.zip"
        with self.assertRaisesRegex(FileExistsError, message):
            make_prefixed_zipfile([], output)
