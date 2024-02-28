
import mimetypes
from typing import Iterable, Optional, Tuple
from unittest import TestCase

from ..mimetype import guess_file_icon, guess_mimetype, guess_mimetype_icon, Icon


class GuessFileIconTest(TestCase):
    def test_empty(self) -> None:
        expected = Icon.DEFAULT.value
        self.assertEqual(expected, 'file-empty')
        self.assertEqual(guess_file_icon(''), expected)

    def test_icon_audio(self) -> None:
        """
        File extensions that should have the audio icon.
        """
        file_names = (
            'mpeg-audio-stream-layer-3.mp3',
            'ogg/opus-audio-file.opus',
            'vorbis-audio-in-the-ogg-container-format.ogg',
            'microsoft-windows-riff.wav',
            'windows-media-audio.wma',
        )
        expected = Icon.AUDIO.value
        self.assertEqual(expected, 'file-music')
        self._check_icons(file_names, expected)

    def test_icon_compressed(self) -> None:
        """
        File extensions that should have the compressed icon.
        """
        file_names = (
            'burrows–wheeler-transform.bz2',
            'gnu-zip.gz',
            'lempel–ziv–markov-chain-algorithm.xz',
            'pwware.zip',
            'zstandard.zstd',
            'tape-archive.tar',
            'tape-archive.tar.gz',
            'tape-archive.tar.bz2',
            'tape-archive.tar.xz',
            'tape-archive.tar.zstd',
        )
        expected = Icon.COMPRESSED.value
        self.assertEqual(expected, 'file-zip')
        self._check_icons(file_names, expected)

    def test_icon_default(self) -> None:
        """
        File extensions where we expect just the default icon.
        """
        file_names = (
            'microsoft-excel.xls',
            'microsoft-excel-2007.xlsx',
            'open-document-spreadsheet.ods',
        )
        expected = Icon.DEFAULT.value
        self.assertEqual(expected, 'file-empty')
        self._check_icons(file_names, expected)

    def test_icon_image(self) -> None:
        """
        File extensions that should have the image icon.
        """
        file_names = (
            'av1-image-file-format.avif',
            'graphics-interchange-format.gif'
            'high-efficiency-image-file-format.heif',
            'joint-photographic-experts-group.jpeg',
            'joint-photographic-experts-group.jpg',
            'microsoft-powerpoint.ppt',
            'microsoft-powerpoint-2007.pptx',
            'openoffice-presentation.odp',
            'portable-network-graphics.png',
            'web-picture.webp',
        )
        expected = Icon.IMAGE.value
        self.assertEqual(expected, 'file-picture')
        self._check_icons(file_names, expected)

    def test_icon_text(self) -> None:
        """
        File extensions that should have the text icon.
        """
        file_names = (
            # Office
            'text.txt',
            'microsoft-word.doc',
            'microsoft-word-2007.docx',
            'hypertext.html',
            'openoffice-document.odt',
            'portable-document-format.pdf',

            # Programming
            'python.py',
        )
        expected = Icon.TEXT.value
        self.assertEqual(expected, 'file-text2')
        self._check_icons(file_names, expected)

    def test_icon_video(self) -> None:
        """
        File extensions that should have the image icon.
        """
        file_names = (
            'audio-video-interleave.avi',
            'matroska-video-container.mkv',
            'quick-time-video.mov',
            'multimedia-container-format-mpeg-4-part-14.mp4',
        )
        expected = Icon.VIDEO.value
        self.assertEqual(expected, 'file-video')
        self._check_icons(file_names, expected)

    def _check_icons(self, file_names: Iterable[str], expected: str) -> None:
        for file_name in file_names:
            icon = guess_file_icon(file_name)
            mimetype, encoding = mimetypes.guess_type(file_name, strict=True)
            if mimetype is None:
                mimetype = 'application/octet-stream'

            if encoding:
                mimetype = f"{mimetype} as {encoding}"

            self.assertEqual(
                icon,
                expected,
                f"Expected {expected!r} for {file_name!r} ({mimetype}) but got {icon!r}"
            )


class GuessMimetype(TestCase):
    def test_guess_mimetype(self) -> None:
        self.assertEqual(guess_mimetype('ai.py'), 'text/x-python')
        self.assertEqual(guess_mimetype('manifesto.txt'), 'text/plain')
        self.assertEqual(guess_mimetype('mixtape.mp3'), 'audio/mpeg')
        self.assertEqual(guess_mimetype('unknown'), 'application/octet-stream')


class GuessMimetypeIconTest(TestCase):
    def test_empty(self) -> None:
        error = r"^Unknown MIME type: ''$"
        with self.assertRaisesRegex(ValueError, error):
            guess_mimetype_icon('')

    def test_unknown(self) -> None:
        error = r"^Unknown MIME type: 'banana'$"
        with self.assertRaisesRegex(ValueError, error):
            guess_mimetype_icon('banana')

    def test_icon_audio(self) -> None:
        cases = (
            ('audio/mpeg', None),
            ('audio/ogg', None),
            ('audio/x-wav', None),
            ('audio/x-ms-wma', None),

        )
        self._check_icons(cases, 'file-music')

    def test_icon_compressed(self) -> None:
        cases = (
            ('application/octet-stream', 'bzip2'),
            ('application/octet-stream', 'gzip'),
            ('application/octet-stream', 'xz'),
            ('application/zip', None),
            ('application/zstd', None),
            ('application/x-tar', None),
            ('application/x-tar', 'gzip'),
            ('application/x-tar', 'bzip2'),
            ('application/x-tar', 'xz'),
            ('application/zstd', None),
        )
        self._check_icons(cases, 'file-zip')

    def test_icon_image(self) -> None:
        cases = (
            ('image/avif', None),
            ('image/heif', None),
            ('image/jpeg', None),
            ('image/jpeg', None),
            ('application/vnd.ms-powerpoint', None),
            ('application/vnd.openxmlformats-officedocument.presentationml.presentation', None),
            ('application/vnd.oasis.opendocument.presentation', None),
            ('image/png', None),
            ('image/webp', None),
        )
        self._check_icons(cases, 'file-picture')

    def test_icon_text(self) -> None:
        cases = (
            ('text/plain', None),
            ('application/msword', None),
            ('application/vnd.openxmlformats-officedocument.wordprocessingml.document', None),
            ('text/html', None),
            ('application/vnd.oasis.opendocument.text', None),
            ('application/pdf', None),
            ('text/x-python', None),
        )
        self._check_icons(cases, 'file-text2')

    def test_icon_video(self) -> None:
        cases = (
            ('video/x-msvideo', None),
            ('video/x-matroska', None),
            ('video/quicktime', None),
            ('video/mp4', None),
        )
        self._check_icons(cases, 'file-video')

    def _check_icons(
        self,
        cases: Iterable[Tuple[str, Optional[str]]],
        expected: str,
    ) -> None:
        for mime_type, encoding in cases:
            icon = guess_mimetype_icon(mime_type, encoding)
            self.assertEqual(
                icon,
                expected,
                f"Expected {expected!r} for {mime_type!r} ({encoding}) but got {icon!r}"
            )
