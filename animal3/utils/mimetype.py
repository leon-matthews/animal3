
from enum import Enum
from typing import Optional
import mimetypes


# Add to system defaults
# Required as of Ubuntu 21.10
mimetypes.add_type('application/zstd', '.zstd', strict=True)
mimetypes.add_type('image/avif', '.avif', strict=True)
mimetypes.add_type('image/webp', '.webp', strict=True)


class Icon(Enum):
    """
    Uses the icon names found in 'static/animal3/icons/'
    """
    DEFAULT = 'file-empty'
    AUDIO = 'file-music'
    COMPRESSED = 'file-zip'
    IMAGE = 'file-picture'
    TEXT = 'file-text2'
    VIDEO = 'file-video'


def guess_file_icon(filename: str) -> str:
    """
    Return an icon class name appropriate for the given file's extension.

        >>> guess_icon_name('banana-cake.txt')
        'file-text2'

    Args:
        filename:
            File name, path, or URL.

    Returns:
        CSS class name for icon.
    """
    mimetype, encoding = mimetypes.guess_type(filename, strict=True)
    if mimetype is None:
        mimetype = 'application/octet-stream'

    return guess_mimetype_icon(mimetype, encoding)


def guess_mimetype(filename: str) -> str:
    """
    Guess a file's mimetype just from its extension.

    Args:
        filename:
            File's name.

    Returns:
        A valid mimetype, though it might just be 'application/octet-stream'.
    """
    mimetype, encoding = mimetypes.guess_type(filename, strict=True)
    if mimetype is None:
        mimetype = 'application/octet-stream'
    return mimetype


def guess_mimetype_icon(mimetype: str, encoding: Optional[str] = None) -> str:
    """
    Return an icon class name appropriate for the given mimetype.

        >>> guess_icon_name('image/jpeg')
        'file-picture'

    Args:
        mimetype:
            Media type to use
        encoding:
            Optional Content-Encoding header value, eg. 'gzip'

    Raises:
        ValueError:
            If invalid mimetype given.

    Returns:
        CSS class name for icon.
    """

    # Compress
    if encoding:
        return Icon.COMPRESSED.value

    # Easy types
    type_, _, subtype = mimetype.partition('/')
    mapping = {
        'audio': Icon.AUDIO,
        'image': Icon.IMAGE,
        'text': Icon.TEXT,
        'video': Icon.VIDEO,
    }
    icon = mapping[type_] if type_ in mapping else None

    # Application
    if type_ == 'application':
        if 'word' in subtype or 'text' in subtype:
            icon = Icon.TEXT
        elif subtype == 'pdf':
            icon = Icon.TEXT
        elif 'powerpoint' in subtype or 'presentation' in subtype:
            icon = Icon.IMAGE
        elif subtype in ('bzip2', 'x-tar', 'zip', 'zstd'):
            icon = Icon.COMPRESSED
        else:
            icon = Icon.DEFAULT

    # No matches?
    if icon is None:
        raise ValueError(f"Unknown MIME type: {mimetype!r}")

    return icon.value
