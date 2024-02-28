
from typing import Any, IO, Optional

from django.core.files.storage import FileSystemStorage

from animal3.utils.files import delete_old_files


class AutoDeletingStorage(FileSystemStorage):
    """
    Delete old files within the given folder.

    Use as the `file_storage` attribute for a form wizard view, in order to
    handle file uploads in incomplete forms; the file wizard only cleans up
    uploaded files when the final form is successfully.

    Note that the `delete_old_files()` function used will deliberately
    raise an exception if the location used has any subfolders.

    See:
        https://django-formtools.readthedocs.io/en/latest/
    """
    def save(
        self,
        name: Optional[str],
        content: IO[Any],
        max_length: Optional[int] = None
    ) -> str:
        """
        Check for, and delete, files older than a week before saving new.
        """
        saved = super().save(name, content, max_length)
        delete_old_files(self.location)
        return saved
