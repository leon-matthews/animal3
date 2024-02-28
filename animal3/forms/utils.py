
import collections
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Set, Union

from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import models
from django.forms import Form, ModelForm

from animal3.utils.files import allowed_path, clean_filename
from animal3.utils.mimetype import guess_mimetype
from animal3.utils.text import shorten


def cleaned_data_to_dict(form: Form) -> Dict[str, Any]:
    """
    Serialise form cleaned data to a dictionary, suitable for use in session.

    Drops values that are empty strings or `None`.
    """
    serialised = {}
    for key, value in form.cleaned_data.items():
        if value is None:
            continue

        if value == '':
            continue

        key = str(key)

        # Use primary-key for a model
        if isinstance(value, models.Model):
            value = value.pk

        serialised[key] = value
    return serialised


def collapse_errors(errors: Dict[str, List[str]]) -> List[str]:
    """
    Collapse a dictionary of similar form errors into a flat list.

    Some editing of the messages also takes place for clarity.

    For example:

        >>> collapse_errors({'name': ['This field is required.'],
        ... 'slug': ['This field is required.']})
        ['Required fields missing: name, slug']

    Args:
        errors:
            A dictionary of Django form errors from, eg. 'form.errors'

    Returns:
        A flat list of error strings.
    """
    # Message replacements
    replacements = {
        'This field is required': 'Required fields missing',
    }

    # Invert the error dictionary
    inverted = collections.defaultdict(set)
    for field, messages in errors.items():
        for message in messages:
            inverted[message].add(field)

    # Build output messages
    def pset(keys: Set[str]) -> str:
        return ", ".join(sorted(keys))

    output = []
    for message, fields in inverted.items():
        message = message.strip('.')
        message = replacements.get(message, message)
        output.append(f"{message}: {pset(fields)}")
    return sorted(output)


def create_upload(path: Path, name: Optional[str] = None) -> SimpleUploadedFile:
    """
    Create a Django `SimpleUploadedFile` instance from path.

    Can then be passed on to a form's FILES argument, ie.

        data = {...}
        files = {'attachment': create_upload(path_to_file)}
        form = SampleForm(data, files)

    Args:
        path:
            Path to existing file.
        name:
            Optionally provide a new name for file. Will still be run
            through `clean_filename()`.

    Returns:
        A `SimpleUploadedFile` instance, or None if relpath empty.
    """
    legal_path = allowed_path(path)
    if not legal_path.is_file():
        message = f"Upload not found: '{legal_path}'"
        raise FileNotFoundError(message)

    if name is None:
        name = legal_path.name

    name = clean_filename(name)
    mimetype = guess_mimetype(legal_path.name)
    return SimpleUploadedFile(name, legal_path.read_bytes(), content_type=mimetype)


def errors_to_string(form: Union[Form, ModelForm], indent: str = '    ') -> str:
    """
    Format a form's errors to a string suitible for logging.

    Args:
        form (Form):
            Instance of a form.
        indent (str):
            Indent to use for multi-line errors.

    Returns (str):
        Error as multi-line string, or empty string if no errors.
    """
    errors = form.errors.items()
    if not errors:
        return ''

    lines = ['']
    for name, messages in errors:
        parts = [f"{indent}{form.__class__.__name__}.{name}:"]
        for message in messages:
            parts.append(message)
        lines.append(' '.join(parts))
    return '\n'.join(lines)


def form_values_line(
    data: Mapping[str, Any],
    maxlen: Optional[int] = 80,
    skip_csrf: bool = True,
) -> str:
    """
    Produce short string of form data for logging purposes.

    eg. "Chris, Farley, chrisf@example.com, Lorem ipsum..."

    Args:
        data:
            Pass in either `form.data` or 'form.cleaned_data`.
        maxlen:
            Truncate string to fit this many characters. Set to None to disable.
        skip_csrf:
            Do not bother printing value of CSRF token (raw data only).

        csrfmiddlewaretoken

    Raises:
        ValueError:
            If form is accidentally passed instead of its data or cleaned_data.

    Returns:
        The data values as a single-line string.
    """
    if issubclass(data.__class__, (Form, ModelForm)):       # type: ignore[unreachable]
        raise ValueError(
            "Unexpected form instance. Pass `form.data` or "
            "`form.cleaned_data` instead."
        )

    parts = []
    for key in data:
        if key == 'csrfmiddlewaretoken' and skip_csrf:
            continue
        value = str(data[key])
        parts.append(value)
    string = ', '.join(parts)

    if maxlen is not None:
        string = shorten(string, maxlen)

    return string
