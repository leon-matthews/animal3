"""
Run external commands under Django environment.

Our Django environment in this case means:

    * Don't print to stdout or stderr
    * Do use logging.
    * Restrict file-system operations to the current project and /tmp/

TODO: Delete run(), move and rename clean_path()
"""

import logging
from pathlib import Path
import subprocess
import tempfile
from typing import List, Union

from django.conf import settings
from django.core.exceptions import SuspiciousOperation


logger = logging.getLogger(__name__)


class CommandError(RuntimeError):
    pass


# Restrict operations to these roots
ALLOWED_ROOTS = (
    Path(tempfile.gettempdir()),
    Path(settings.MEDIA_ROOT),
    Path(settings.STATIC_ROOT),
)


def clean_path(path: Union[Path, str]) -> str:
    """
    Cannonicalise path, and check that it is in an expected location.
    """
    cleaned = Path(path)
    cleaned = cleaned.expanduser()
    # ~ cleaned = cleaned.resolve()
    error = ''
    for root in ALLOWED_ROOTS:
        try:
            cleaned.relative_to(root)
        except ValueError as e:
            error += str(e)
        else:
            return str(cleaned)
    raise SuspiciousOperation(error)


def run(command: List[str], timeout: float = 5.0) -> subprocess.CompletedProcess:
    """
    Convenience wrapper around Subprocess class.

    command
        Command to run as list or other iterable, eg. ['ls', '-l']
    """
    logger.debug("Running command: '%s'", ' '.join(command))
    try:
        process = subprocess.run(
            command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            universal_newlines=True)
    except subprocess.CalledProcessError:
        message = f"Command failed: '{' '.join(command)}'"
        logger.error(message)
        raise CommandError(message)
    except subprocess.TimeoutExpired:
        message = f"Command timed-out: '{' '.join(command)}'"
        logger.error(message)
        raise CommandError(message) from None
    return process
