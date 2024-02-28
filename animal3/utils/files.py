
from __future__ import annotations

import os
from pathlib import Path
import random
import tempfile
import time
from typing import Any, List, Optional, Union

from django.conf import settings
from django.core.exceptions import SuspiciousFileOperation

from .text import make_slug, _unique_suffix
from .zip import ZipFile as ZipFileNew


# Wrap in string to avoid run-time crash under Python 3.8
PathLike = Union[str, 'os.PathLike[str]']


def allowed_path(path: PathLike) -> Path:
    """
    Ensure given path is under folders in ALLOWED_ROOTS.

    Args:
        path:
            Path to check.

    Raises:
        SuspiciousFileOperation:
            If path not found under allowed directory.

    Returns:
        Cleaned path to some place we're allowed to be.
    """
    if not path:
        raise ValueError('Empty path given')

    cleaned = Path(path)
    cleaned = cleaned.expanduser()
    cleaned = cleaned.resolve()
    relative: Optional[PathLike] = None
    for root in settings.ALLOWED_ROOTS:
        try:
            relative = cleaned.relative_to(root)
        except ValueError:
            pass

    if relative is None:
        raise SuspiciousFileOperation(f"Path is not under ALLOWED_ROOTS: {path!r}")

    return cleaned


def change_filename(old: PathLike, new: str) -> str:
    """
    Change filename while preserving path and suffix.

        >>> change_filename('Screen Shot.png', 'chair')
        'chair.png'

    Args:
        old:
            Previous filename or path.
        new:
            New filename. If it has no suffix the suffix from the old
            filename will be preserved.

    Returns:
        Output filename or path as a string.
    """
    old_path, _ = os.path.split(old)
    old_name, old_extension = os.path.splitext(old)
    new_name, new_extension = os.path.splitext(new)
    extension = new_extension if new_extension else old_extension
    filename = f"{new_name}{extension}"
    if old_path:
        filename = os.path.join(old_path, filename)
    return filename


def clean_filename(filename: str) -> str:
    """
    Pass given filename through `slugify`, but preserving extension.

        >>> clean_filename('Important Document.odt')
        'important-document.odt'

    Args:
        filename:
            Name of file including extension only. Paths are not allowed.

    Raises:
        ValueError:
            If input is empty, or contains a path separator.
        SuspiciousFileOperation:
            If a path is

    Returns:
        Cleaned filename.
    """
    # Empty?
    if not filename:
        raise ValueError('Empty filename given')

    # No paths!
    path, name = os.path.split(filename)
    if path:
        raise SuspiciousFileOperation(
            f"Attempt to pass path to clean_filename(): {filename!r}"
        )

    # Clean, keeping the extension
    name, extension = os.path.splitext(name)
    name = make_slug(name)
    extension = make_slug(extension)
    name = f"{name}.{extension}" if extension else name
    return name


def count_files(root: PathLike) -> int:
    """
    Recursively count the number of files underneath the given root.

    Args:
        root:
            Path to look under.

    Raises:
        FileNotFoundError:
            If given path doesn't exist
        NotADirectoryError
            if given path does not refer to a folder.

    Returns:
        The number of files found.
    """
    root = Path(root)
    _folder_check(root)
    num_files = 0
    for _, _, files in os.walk(root):
        num_files += len(files)
    return num_files


def delete_empty_subfolders(
    folder: PathLike,
    *,
    dry_run: bool = False
) -> List[Path]:
    """
    Remove empty folders under the given one.

    Search is NOT recursive; only direct subfolders are checked.

    Args:
        folder:
            Folder to delete subfolders from.
        dry_run:
            When set to True no folders will actually be deleted.

    Raises:
        FileNotFoundError:
            If folder doesn't exist
        NotADirectoryError:
            Given folder is not a folder.

    Returns:
        A list of the deleted folders' paths.
    """
    folder = Path(folder)
    _folder_check(folder)

    # Find
    deadpool = []
    for path in folder.iterdir():
        if path.is_dir():
            num_files = len(list(path.iterdir()))
            if num_files == 0:
                deadpool.append(path)

    # Delete?
    if not dry_run:
        for path in deadpool:
            path.rmdir()

    return deadpool


def delete_old_files(
    folder: PathLike,
    *,
    max_age: int = 604800,
    dry_run: bool = False,
) -> List[Path]:
    """
    Delete files in the given folder whose *mtime* is older than the given `max_age`.

    To help avoid accidents, sub-folders are not allowed under the folder.

    Args:
        folder:
            Folder to delete files from.
        max_age:
            How old, in seconds, files can be before getting deleted.
            Defaults to one week.
        dry_run:
            When set to True no folders will actually be deleted.

    Raises:
        RuntimeError:
            If folder vaidation fails: it doesn't exist, isn't a folder, or
            has sub-folders.

    Returns:
        A  list of the deleted files' paths.
    """
    folder = Path(folder)
    _folder_check(folder, allow_subfolders=False)

    # Find
    now = time.time()
    deadpool = []
    for path in folder.iterdir():
        age = now - os.path.getmtime(path)
        if age > max_age:
            deadpool.append(path)

    # Delete?
    if not dry_run:
        for path in deadpool:
            path.unlink()

    return deadpool


def extract_name(path: PathLike) -> str:
    """
    Extract a name from the given path.

    Args:
        path:
            Path, relative path, or file name.

    Returns:
        Printable name.
    """
    name = os.path.basename(path)
    name, extension = os.path.splitext(name)
    name = name.replace('-', ' ')
    name = name.replace('_', ' ')
    name = name.title()
    return name


def load_lines(path: PathLike, encoding: str = 'utf-8') -> List[str]:
    """
    Load lines from given text file into list.

    Blank lines and lines beginning with '#' are skipped.

    Args:
        path:
            Path to existing files.
        encoding:
            Encoding of text file.

    Returns:
        A list of all of the valid lines in the file.
    """
    lines = []
    path = Path(path)
    with open(path, 'rt', encoding=encoding) as fp:
        for line in fp:
            line = line.strip()
            if not line:
                continue
            if not line.startswith('#'):
                lines.append(line)
    return lines


def line_random(path: PathLike, encoding: str = 'utf-8') -> str:
    """
    Return a single random line from given text file.

    Blank lines and lines beginning with '#' are skipped.

    Args:
        path:
            Path to existing files.
        encoding:
            Encoding of text file.

    Return: Single line of text.
    """
    path = Path(path)
    lines = load_lines(path, encoding)
    return random.choice(lines)


def make_prefixed_zipfile(paths_in: List[Path], path_out: Path) -> Path:
    # 2021-01-02 Moved
    import warnings
    warnings.warn(
        "make_prefixed_zipfile() moved to animal3.utils.zip module()",
        DeprecationWarning,
    )
    from .zip import make_prefixed_zipfile
    return make_prefixed_zipfile(paths_in, path_out)


def match_stem(root: PathLike, stem: str, *, case_sensitive: bool = False) -> List[Path]:
    """
    Find all files in `root` matching given stem.

    Does not search recursively, but does ignore case.

    For example a search for 'readme' might match 'README.txt' and 'ReadMe.pdf'

    Args:
        root:
            Folder to look under.
        stem:
            Filename without extension, eg. 'readme'
        case_sensitive:
            Set to true to limit results to exact matches. By default matches
            ignore case.

    Returns:
        A list (possibly empty) of matched paths.
    """
    root = Path(root)
    found = []

    if not case_sensitive:
        stem = stem.casefold()

    for path in root.iterdir():
        if path.stem == stem:
            found.append(path)
        elif not case_sensitive and path.stem.casefold() == stem:
            found.append(path)

    return found


def TemporaryFolder(**kwargs: Any) -> tempfile.TemporaryDirectory:
    # Deprecated: 2021-01-02
    # Could not use __init_subclass__() method for this stdlib class
    import warnings
    warnings.warn(
        "TemporaryFolder now in stdlib: 'tempfile.TemporaryDirectory'",
        category=DeprecationWarning,
        stacklevel=2)
    return tempfile.TemporaryDirectory(**kwargs)


def unique_filename(folder: PathLike, filename: str) -> str:
    """
    Add a numerical suffix to make a filename unique within the given folder.

    Suffixes are not considered when deciding if a filename is unique. See the
    documentation for the `_unique_suffix()` function from the text module
    for details.

    Args:
        folder:
            Folder to examine.
        filename:
            Desired filename. Will be left unchanged if possible.

    See:
        animal3.utils.text._unique_suffix()

    Returns:
        A plain-string filename.
    """
    folder = Path(folder)
    _folder_check(folder)
    stem, _, suffix = filename.rpartition('.')
    prefix = stem.rstrip('1234567890')
    conflicts = [c.stem for c in folder.glob(f"{prefix}*")]
    stem = _unique_suffix(stem, conflicts)
    return f"{stem}.{suffix}"


def ZipFile(*args: Any, **kwargs: Any) -> ZipFileNew:
    # Deprecated: 2021-01-02
    import warnings
    warnings.warn(
        "ZipFile has been moved to 'animal3.utils.zip'",
        category=DeprecationWarning,
        stacklevel=2)
    return ZipFileNew(*args, **kwargs)


def _folder_check(folder: PathLike, allow_subfolders: bool = True) -> None:
    """
    Helper function for functions that expect an existing folder.

    Args:
        folder:
            Folder to check
        allow_subfolders:
            If False, an exception will be raised if any subfolders are found
            under given folder.  Defaults to True; no check performed.

    Raises:
        Various exceptions under `OSError`.  See source below.

    Returns: None
    """
    folder_path = Path(folder)
    if not folder_path.exists():
        raise FileNotFoundError(f"Folder not found: {folder}")

    if not folder_path.is_dir():
        raise NotADirectoryError(f"Path is not a folder: {folder}")

    if not allow_subfolders:
        for path in folder_path.iterdir():
            if path.is_dir():
                message = f"Subfolders are not allowed, but found one under: {folder}"
                raise IsADirectoryError(message)
