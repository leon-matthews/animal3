
import os.path
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Type

from django.core.exceptions import ImproperlyConfigured
from django.core.files.uploadedfile import SimpleUploadedFile
from django.forms import ModelForm

from animal3.forms import collapse_errors, create_upload


class Transformer:
    """
    Takes raw dictionary of field data and adapts it for current model.

    Produces data for the first and second arguments for a ModelForm:

        transformer = SampleTransformer()
        fields = {...}
        data = transformer.get_form_data(fields.copy())
        files = transformer.get_form_files(fields.copy())
        form = SampleForm(data, files)

    A loader contains at least one, possibly many, transformer classes - one
    for each format of data that it has to deal with.

    Attributes:
        ignore_extra:
            Strict check should ignore these extra fields
        ignore_missing:
            Strict check should ignore these missing fields.
        model_label:
            Label to filter out the field data expected.

    """
    ignore_extra: Optional[Iterable[str]] = None
    ignore_missing: Optional[Iterable[str]] = None
    model_label: str

    def __init__(self, media_root: Optional[Path] = None):
        """
        Initialiser.

        Args:
            media_root:
                Our source of incoming files.
        """
        self.media_root = media_root

    def check(
        self,
        fields: Dict[str, Any],
        form_class: Type[ModelForm],
        *,
        auto_now_fields: Optional[Set[str]] = None,
        strict: bool = True,
    ) -> List[str]:
        """
        Check this transformer against given fields using the form class.

        Used by loader classes to validate which transformer best matches the
        incoming data.

        If strict is set, field names will also be checked for exact matches.
        Django forms silently ignore extra keys, and tolerate missing keys that
        have defaults on the form. In this application that could result in lost
        data, so extra checking is performed.

        Strict checks are influenced by the values of the class attributes
        `ignore_extra` and `ignore_missing`. See class documentation.

        Args:
            fields:
                Field data to transform.
            form_class:
                Model form class to validate against.
            auto_now_fields:
                An optional set of field names of the automatic date fields.
                These are expected to NOT be found in the model form.
            strict:
                If true, field names must be an exact match to each other.

        Returns:
            A list of error messages. An empty list indicates a lack of errors.
        """
        # Transform fields
        if auto_now_fields is None:
            auto_now_fields = set()
        errors: List[str] = []
        form_data = self.get_form_data(fields.copy())
        form_files = self.get_form_files(fields.copy())
        form = form_class(form_data, form_files)            # type: ignore[arg-type]

        # Validate form
        if not form.is_valid():
            errors.extend(form.non_field_errors())
            errors.extend(collapse_errors(form.errors))

        # Prefix error messages
        errors = [f"Form error. {error}" for error in errors]

        # Finished?
        if not strict:
            return sorted(errors)

        # Strict check of field names
        transformed_keys = set(form_data.keys() | form_files.keys())
        form_field_keys = set(form.fields.keys())

        # Pretty-print sets in error messages
        def pset(keys: Set[str]) -> str:
            return ", ".join(sorted(keys))

        # Missing fields that transformer should add
        missing = form_field_keys - transformed_keys
        ignore_missing = set() if self.ignore_missing is None else set(self.ignore_missing)
        missing -= ignore_missing
        if missing:
            message = f"Transformer is missing fields: {pset(missing)}"
            errors.append(message)

        # Extra fields that transformer should remove
        extra = transformed_keys - (form_field_keys | auto_now_fields | set(['pk']))
        if extra:
            message = f"Transformer provided extra fields: {pset(extra)}"
            errors.append(message)

        return sorted(errors)

    def create_upload(
        self,
        relpath: str,
        name: Optional[str] = None,
    ) -> Optional[SimpleUploadedFile]:
        """
        Create a Django `SimpleUploadedFile` instance from path.

        Args:
            relpath:
                Path to existing file, relative to MEDIA_ROOT folder.
            name:
                Optionally provide a new name for file. Will still be run
                through `clean_filename()`.

        Raises:
            ImproperlyConfigured:
                If no media source has been provided.
            ValueError:
                If `relpath` is not a relative path.

        Returns:
            A `SimpleUploadedFile` instance, or None if relpath empty.
        """
        # Can we even?
        if self.media_root is None:
            raise ImproperlyConfigured(
                "Cannot create uploads without a media source. "
                "Use the '--media' argument."
            )

        # Empty?
        if not relpath:
            return None

        # Check path
        relpath = os.path.normpath(relpath)
        if relpath.startswith(('.', '/')):
            raise ValueError(f"Path does not appear to be relative: {relpath!r}")

        # Create upload
        path = self.media_root / relpath
        upload = create_upload(path, name)
        return upload

    def get_form_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform given raw field data into ModelForm ready data.

        Be sure to copy field data before passing it. This method freely
        change values, rename keys, and delete values, for example:

            data['price'] += 1                  # Modify value in place
            data['title'] = data.pop('name')    # Rename key
            del data['description']             # Delete key

        """
        return data

    def get_form_files(self, data: Dict[str, Any]) -> Dict[str, SimpleUploadedFile]:
        """
        Load files for model.

        See:
            `create_upload`:
                To create a SimpleUploadedFile from a relative path.

        Returns:
            A mapping between field name and an uploaded file instance.
        """
        return {}
