
from pathlib import Path
import tempfile

from django.conf import settings
from django.core.exceptions import SuspiciousOperation
from django.test import SimpleTestCase

from ..commands import clean_path, CommandError, run
from ..logging import logger_hush


class TestCleanPath(SimpleTestCase):
    site_root: Path

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.site_root = Path(settings.SITE_ROOT)

    def test_bad_paths(self) -> None:
        bad_paths = (
            '/etc/',
            '~',
            settings.SITE_ROOT,
            Path(settings.SITE_ROOT) / 'settings.ini',
            settings.SOURCE_ROOT,
            Path(settings.SOURCE_ROOT) / 'common/settings/settings.py',
        )

        for bad_path in bad_paths:
            with self.assertRaises(SuspiciousOperation):
                clean_path(bad_path)                        # type: ignore[arg-type]

    def test_good_paths(self) -> None:
        good_paths = (
            tempfile.gettempdir(),
            Path(tempfile.gettempdir()) / 'euue/aoeu.log',
            settings.MEDIA_ROOT,
            Path(settings.MEDIA_ROOT) / 'blog' / 'thumbnails' / 'headshot.jpg',
            settings.STATIC_ROOT,
            Path(settings.STATIC_ROOT) / 'blog' / 'missing.jpg',
        )

        for good_path in good_paths:
            cleaned = clean_path(good_path)                 # type: ignore[arg-type]
            self.assertEqual(str(good_path), str(cleaned))


class TestRun(SimpleTestCase):
    def test_success(self) -> None:
        command = ['true']
        run(command)

    def test_failure(self) -> None:
        command = ['false']
        message = "Command failed: 'false'"
        with logger_hush(), self.assertRaisesRegex(CommandError, message):
            run(command)

    def test_timeout(self) -> None:
        command = ['sleep', '1']
        message = r"^Command timed-out: 'sleep 1'$"
        with logger_hush(), self.assertRaisesRegex(CommandError, message):
            run(command, timeout=0.01)
