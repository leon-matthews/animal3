
import os
from pathlib import Path
import tempfile
import time
from unittest import mock, TestCase
import zipfile

from django.core.exceptions import SuspiciousFileOperation

from animal3.utils.testing import DocTestLoader

from .. import files
from ..files import (
    allowed_path,
    change_filename,
    clean_filename,
    count_files,
    delete_empty_subfolders,
    delete_old_files,
    extract_name,
    line_random,
    make_prefixed_zipfile,
    match_stem,
    TemporaryFolder,
    unique_filename,
    ZipFile,
    _folder_check,
)
from ..testing import assert_deprecated

from . import DATA_FOLDER


class DocTests(TestCase, metaclass=DocTestLoader, test_module=files):
    pass


class AllowedPathTest(TestCase):
    def test_empty(self) -> None:
        error = r"Empty path given"
        with self.assertRaisesRegex(ValueError, error):
            allowed_path('')

    def test_valid_path(self) -> None:
        cleaned = allowed_path(__file__)
        self.assertIsInstance(cleaned, Path)
        self.assertTrue(str(cleaned).endswith('animal3/utils/tests/test_files.py'))

    def test_illegal_path(self) -> None:
        message = r"^Path is not under ALLOWED_ROOTS: '/etc/passwd'$"
        with self.assertRaisesRegex(SuspiciousFileOperation, message):
            allowed_path('/etc/passwd')


class ChangeFilenameTest(TestCase):
    def test_preserve_path(self) -> None:
        current = 'screen/shot/2017/02/27/3.55.14PM.png'
        self.assertEqual(
            change_filename(current, 'chair'),
            'screen/shot/2017/02/27/chair.png'
        )

    def test_preserve_suffix(self) -> None:
        current = 'Screen Shot 2017-02-27 at 3.55.14 PM.png'
        self.assertEqual(
            change_filename(current, 'chair'),
            'chair.png',
        )

    def test_change_suffix(self) -> None:
        self.assertEqual(
            change_filename('/tmp/apple.txt', 'banana.odt'),
            '/tmp/banana.odt',
        )

    def test_pathlib_path(self) -> None:
        self.assertEqual(
            change_filename(Path('/tmp/apple.txt'), 'banana.odt'),
            '/tmp/banana.odt',
        )


class CleanFileNameTest(TestCase):
    def test_clean(self) -> None:
        """
        Ensure function behaves as expected.
        """
        self.assertEqual(clean_filename('abc'), 'abc')
        self.assertEqual(clean_filename('data.txt'), 'data.txt')
        self.assertEqual(clean_filename('DATA.TXT'), 'data.txt')
        self.assertEqual(clean_filename(' the data.txt '), 'the-data.txt')

    def test_empty_error(self) -> None:
        """
        Should raise ValueError on empty input.
        """
        error = r"Empty filename given"
        with self.assertRaisesRegex(ValueError, error):
            clean_filename('')

    def test_path_error(self) -> None:
        """
        Should raise ValueError on empty input.
        """
        error = r"Attempt to pass path to clean_filename\(\): '/etc/password'"
        with self.assertRaisesRegex(SuspiciousFileOperation, error):
            clean_filename('/etc/password')


class CountFilesTest(TestCase):
    def test_count_files(self) -> None:
        count = count_files(DATA_FOLDER)
        self.assertEqual(count, 13)

    def test_not_found(self) -> None:
        error = r"Folder not found: /no/such/folder"
        with self.assertRaisesRegex(FileNotFoundError, error):
            count_files('/no/such/folder/')

    def test_check_folder_call(self) -> None:
        """
        Ensure that `_check_function()` is called once.
        """
        folder = DATA_FOLDER
        with mock.patch('animal3.utils.files._folder_check') as folder_check:
            count_files(DATA_FOLDER)
            folder_check.assert_called_once()
            folder_check.assert_called_with(folder)


class DeleteEmptySubfoldersTest(TestCase):
    def test_check_folder_call(self) -> None:
        """
        Ensure that `_check_function()` is called once with 'allow_subfolders=False'.
        """
        folder = DATA_FOLDER
        with mock.patch('animal3.utils.files._folder_check') as folder_check:
            delete_empty_subfolders(folder, dry_run=True)
            folder_check.assert_called_once()
            folder_check.assert_called_with(folder)

    def test_delete_empty_subfolders(self) -> None:
        with tempfile.TemporaryDirectory(prefix='test_cache_folder_aged') as folder_str:
            # Create some folders
            folder = Path(folder_str)
            (folder / 'empty').mkdir()
            not_empty = folder / 'not_empty'
            not_empty.mkdir()
            (not_empty / '.hidden').touch()

            # Folder before deletion
            before_deletion = [f.name for f in folder.iterdir()]
            before_deletion.sort()
            self.assertEqual(before_deletion, ['empty', 'not_empty'])

            # Delete empty sub-folders
            deleted = delete_empty_subfolders(folder)

            # Check deleted
            self.assertEqual(len(deleted), 1)
            deleted_file = deleted[0]
            self.assertEqual(deleted_file.name, 'empty')

            # Folder after deletion
            after_deletion = [f.name for f in folder.iterdir()]
            self.assertEqual(after_deletion, ['not_empty'])


class DeleteOldFilesTest(TestCase):
    def test_check_folder_call(self) -> None:
        """
        Ensure that `_check_function()` is called once with 'allow_subfolders=False'.
        """
        folder = DATA_FOLDER
        with mock.patch('animal3.utils.files._folder_check') as folder_check:
            delete_old_files(folder, dry_run=True)
            folder_check.assert_called_once()
            folder_check.assert_called_with(folder, allow_subfolders=False)

    def test_delete_old_files(self) -> None:
        with tempfile.TemporaryDirectory(prefix='test_cache_folder_aged') as folder_str:
            # Create files
            folder = Path(folder_str)
            now = int(time.time())
            mtime = now
            one_day = 86_400
            for i in range(0, 10):
                name = f"{i}_days_old"
                path = folder / name
                path.touch(exist_ok=False)
                os.utime(path, (mtime, mtime))
                mtime -= one_day

            # Folder before deletion
            before_deletion = sorted([f.name for f in folder.iterdir()])
            expected = [
                '0_days_old',
                '1_days_old',
                '2_days_old',
                '3_days_old',
                '4_days_old',
                '5_days_old',
                '6_days_old',
                '7_days_old',
                '8_days_old',
                '9_days_old',
            ]
            self.assertEqual(before_deletion, expected)

            # Delete old files
            deleted = delete_old_files(folder)

            # Check deleted
            deleted_names = sorted([f.name for f in deleted])
            expected = ['7_days_old', '8_days_old', '9_days_old']
            self.assertEqual(deleted_names, expected)

            # After deletion
            after_deletion = sorted([f.name for f in folder.iterdir()])
            expected = [
                '0_days_old',
                '1_days_old',
                '2_days_old',
                '3_days_old',
                '4_days_old',
                '5_days_old',
                '6_days_old',
            ]
            self.assertEqual(after_deletion, expected)


class ExtractNameTest(TestCase):
    def test_relative_path(self) -> None:
        relpath = 'samples/files/2023/06/13/happy-times.pdf'
        name = extract_name(relpath)
        self.assertEqual(name, 'Happy Times')


class LineRandomTest(TestCase):
    def test_line_random(self) -> None:
        path = DATA_FOLDER / 'haiku.txt'
        for _ in range(100):
            line = line_random(path)
            self.assertFalse(line.endswith('\n'))
            self.assertGreater(len(line), 0)
            self.assertNotIn('#', line)


class MakePrefixedZipFileDeprecatedTest(TestCase):
    def test_deprecated(self) -> None:
        message = 'make_prefixed_zipfile() moved to animal3.utils.zip module()'
        with assert_deprecated(message):
            with tempfile.TemporaryDirectory(prefix='test_cache_folder_aged') as folder_str:
                output = Path(folder_str) / 'out.zip'
                make_prefixed_zipfile([], output)


class MatchStemTest(TestCase):
    def test_defaults(self) -> None:
        found = match_stem(DATA_FOLDER, 'BEAN')
        self.assertEqual(len(found), 3)
        expected = ['BEAN.rst', 'bean.txt', 'bean.zip']
        names = sorted(f.name for f in found)
        self.assertEqual(names, expected)

    def test_case_sensitive(self) -> None:
        found = match_stem(DATA_FOLDER, 'Bean', case_sensitive=True)
        self.assertEqual(len(found), 0)


class TemporaryFolderDeprecatedTest(TestCase):
    def test_temporary_folder_deprecated(self) -> None:
        with assert_deprecated():
            with TemporaryFolder():
                pass


class UniqueFilenameTest(TestCase):
    def test_already_unique(self) -> None:
        filename = unique_filename(DATA_FOLDER, 'invisible.png')
        self.assertEqual(filename, 'invisible.png')

    def test_in_sequence(self) -> None:
        filename = unique_filename(DATA_FOLDER, 'bean3.jpg')
        self.assertEqual(filename, 'bean6.jpg')

    def test_find_unique(self) -> None:
        filename = unique_filename(DATA_FOLDER, 'bean.doc')
        self.assertEqual(filename, 'bean6.doc')

    def test_existing_suffix(self) -> None:
        filename = unique_filename(DATA_FOLDER, 'bean2.doc')
        self.assertEqual(filename, 'bean6.doc')

    def test_check_folder_call(self) -> None:
        """
        Ensure that `_check_function()` is called once.
        """
        folder = DATA_FOLDER
        with mock.patch('animal3.utils.files._folder_check') as folder_check:
            unique_filename(DATA_FOLDER, 'example.txt')
            folder_check.assert_called_once()
            folder_check.assert_called_with(folder)


class ZipFileDeprecatedTest(TestCase):
    def test_zip_file_deprecated(self) -> None:
        with assert_deprecated():
            with tempfile.NamedTemporaryFile() as f:
                with zipfile.ZipFile(f.name, 'w'):
                    pass
                ZipFile(f.name)


class _CheckFolderTest(TestCase):
    def test_check_folder_good(self) -> None:
        _folder_check(DATA_FOLDER)

    def test_folder_not_found(self) -> None:
        folder = Path('/not/a/real/folder')
        message = "Folder not found: /not/a/real/folder"
        with self.assertRaisesRegex(FileNotFoundError, message):
            _folder_check(folder)

    def test_folder_not_folder(self) -> None:
        folder = DATA_FOLDER
        path = sorted(folder.iterdir())[1]

        with self.assertRaises(NotADirectoryError) as cm:
            _folder_check(path)

        error = str(cm.exception)
        self.assertTrue(error.startswith('Path is not a folder:'))
        self.assertIn('animal3/utils/tests/data/bean.txt', error)

    def test_subfolders_not_allowed(self) -> None:
        path = DATA_FOLDER.parent
        with self.assertRaises(IsADirectoryError) as cm:
            _folder_check(path, allow_subfolders=False)
        error = str(cm.exception)
        self.assertTrue(error.startswith('Subfolders are not allowed, but'))
        self.assertIn('animal3/utils/tests', error)
