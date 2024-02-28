
import logging
import os.path
from pathlib import Path
from typing import List, Union
import zipfile


logger = logging.getLogger(__name__)


def make_prefixed_zipfile(paths_in: List[Path], path_out: Path) -> Path:
    """
    Create simple zip file with simple extracted structure; a single sub-folder
    that matches the zipfile's name.

    File names will be used as-is.  Having two files with the same name is
    a bad idea, but isn't explicitly checked for.

    Args:
        path_out:
            Full path to output file to create.

        paths_in:
            Iterable of paths to input files. Names are retained, paths are dropped.

    Raises:
        FileExistsError:
            If output path already exists.

    Returns:
        Path to newly-created zip file.
    """
    if path_out.exists():
        raise FileExistsError(f"Output path already exists: {path_out}")

    with zipfile.ZipFile(path_out, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for path_in in paths_in:
            with open(path_in, 'rb') as fp:
                zipf.writestr(os.path.join(path_out.stem, path_in.name), fp.read())

    return path_out


class ZipFile:
    """
    Make reading existing zip file easier.
    """
    names: List[str]
    zip: zipfile.ZipFile

    def __init__(self, path: Union[Path, str]):
        self.path = Path(path)
        self._open(self.path)

    def read(self, file_name: str) -> bytes:
        """
        Read contents of file within zip file.

        Args:
            file_name (str):
                file_name of file (inside zip) to read (see `find_file_name()`).

        Raises:
            FileNotFoundError:
                If `file_name` is not present within the zip file.

        Return (bytes):
            Contents of file found. Zero-length if no file found.
        """
        try:
            info = self.zip.getinfo(file_name)
        except KeyError as e:
            raise FileNotFoundError(str(e)) from None

        logger.debug(
            f"Reading CSV data from zip entry ({info.file_size:,} bytes, "
            f"{info.compress_size:,} compressed): {file_name}")
        return self.zip.read(file_name)

    def _open(self, path: Path) -> None:
        """
        Attempt to open zip file and read contents.
        """
        try:
            self.zip = zipfile.ZipFile(path)
        except zipfile.BadZipFile as e:
            # Improve default error message
            message = f"{e}: {path.name}"
            raise zipfile.BadZipFile(message) from None
        logger.info(f"Opened zip archive: {os.path.relpath(path)}")
        self.names = self.zip.namelist()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.path.name!r})"
