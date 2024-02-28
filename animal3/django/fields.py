
from hashlib import md5
from typing import Callable, List, Optional

from django.db.models import Model
from django.utils import timezone
from django.utils.crypto import salted_hmac

from ..utils.files import clean_filename
from ..utils.text import camelcase_to_underscore


def upload_to(instance: Model, filename: str) -> str:
    """
    Clean file name, then adds subfolders for both the model's app and name.

    See the `UploadTo` class for even more details.
    """
    upload_to = UploadTo()
    return upload_to(instance, filename)


def upload_to_dated(instance: Model, filename: str) -> str:
    """
    As per `upload_to()` but add subfolders for (UTC) year, month, & day.

    Attempts to use the `created` attribute of the instance. If not found
    uses the current date.
    """
    def subfolders(instance: Model, filename: str) -> List[str]:
        date = getattr(instance, 'created', None)
        if date is None:
            date = timezone.now()
        date_string = str(date.strftime("%Y/%m/%d"))
        parts = date_string.split('/')
        return parts

    upload_to = UploadTo(subfolders)
    return upload_to(instance, filename)


def upload_to_hashed(instance: Model, filename: str) -> str:
    """
    As per `upload_to()` but spreads files into one of 256 'random' subfolders.

    Uses the first two hex-characters of the md5-hash of the file's name.
    """
    def subfolders(instance: Model, filename: str) -> List[str]:
        babyhash = md5(filename.encode('utf-8')).hexdigest()[:2]
        return [babyhash]

    upload_to = UploadTo(subfolders)
    return upload_to(instance, filename)


def upload_to_obsfucated(instance: Model, filename: str) -> str:
    """
    As per `upload_to_hashed()` but adds hard-to-guess folder name.

    Note that we're using the value of the site's secret key
    to generate the secret hash value. The path is saved into the model,
    so will not break if secret key ever changes.
    """
    def subfolders(instance: Model, filename: str) -> List[str]:
        hash_ = salted_hmac(filename, filename).hexdigest()
        return [hash_[:2], hash_[:16]]

    upload_to = UploadTo(subfolders)
    return upload_to(instance, filename)


class UploadTo:
    """
    Generic implementation of a `FieldField.upload_to` callable.

    Creates paths with the following sensible site-wide policy, where we
    have subfolders per app, per model, and (optionally) per field, eg.:

        '{app}/{model}/{field}/{file}'

    Because of limitations of the Django migrations system, support for field
    names has been dropped. You must also use the plain-function interface
    provided below.
    """
    def __init__(self, subfolders: Optional[Callable] = None):
        """
        Initialise object with optional subfolders callable.
        """
        self._install_subfolders(subfolders)

    def __call__(self, instance: Model, filename: str) -> str:
        filename = clean_filename(filename)
        path = self._metadata(instance, filename)
        path.extend(self.subfolders(instance, filename))
        path.append(filename)
        return '/'.join(path)

    def _install_subfolders(self, subfolders: Optional[Callable]) -> None:
        """
        Add callable that can provide additional subfolders to use.

        Args:
            subfolders:
                Function that returns a list of folders to add to the default set.
        """
        # Use default
        def default_subfolders(instance: Model, filename: str) -> List[str]:
            return []

        if subfolders is None:
            self.subfolders = default_subfolders
        else:
            self.subfolders = subfolders

    def _metadata(self, instance: Model, filename: str) -> List[str]:
        """
        Return list containing instance's app and model name.

        The model name is also transformed from CamelCase into underscores.
        """
        app_name, model_name = instance._meta.label.split('.')
        model_name = camelcase_to_underscore(model_name)
        metadata = [app_name, model_name]
        return metadata
