
import argparse
import logging
from pathlib import Path
import textwrap
from typing import Any, TYPE_CHECKING
from typing import Callable

from django.core.management.base import (
    BaseCommand as DjangoBaseCommand,
    CommandError,
    CommandParser,
)


if TYPE_CHECKING:
    CommandMixin = DjangoBaseCommand
else:
    CommandMixin = object


logger = logging.getLogger(__name__)


def existing_file_type(string: str) -> Path:
    """
    An `argparse` type to convert string to a `Path` object.

    Raises `argparse.ArgumentTypeError` if path does not exist.
    """
    path = Path(string).expanduser().resolve()
    error = None
    if not path.exists():
        error = f"File does not exist: {path}"
    if not path.is_file():
        error = f"Path is not a file: {path}"

    if error is not None:
        raise argparse.ArgumentTypeError(error)
    return path


def existing_folder_type(string: str) -> Path:
    """
    An `argparse` type to convert string to a `Path` object.

    Raises `argparse.ArgumentTypeError` if path is not an existing folder.
    """
    path = Path(string).expanduser().resolve()
    error = None
    if not path.exists():
        error = f"Folder does not exist: {path}"
    if not path.is_dir():
        error = f"Path is not a folder: {path}"

    if error is not None:
        raise argparse.ArgumentTypeError(error)
    return path


class CommandBase(DjangoBaseCommand):
    """
    Add a new niceties to Django's command base class.
    """
    def execute(self, *args: Any, **options: Any) -> None:
        self.force_logging(options['verbosity'])
        super().execute(*args, **options)

    def force_logging(self, verbosity: int) -> None:
        """
        Force a basic logging setup and level globally.

        verbosity:
            A value from zero to four, set from Django's parent class.
            Defaults to 1.

        Returns:
            None
        """
        if verbosity == 0:
            level = logging.ERROR
        elif verbosity == 1:
            level = logging.WARNING
        elif verbosity == 2:
            level = logging.INFO
        elif verbosity >= 3:
            level = logging.DEBUG

        logging.basicConfig(
            level=level,
            format="%(levelname)-7s %(message)s",
            force=True,
        )

    # Printing #############################################
    def info(self, string: str) -> None:
        self.stdout.write(string)

    def notice(self, string: str) -> None:
        self.stdout.write(self.style.NOTICE(string))

    def success(self, string: str) -> None:
        self.stdout.write(self.style.SUCCESS(string))

    def warning(self, string: str) -> None:
        self.stdout.write(self.style.WARNING(string))

    def error(self, string: str) -> None:
        self.stdout.write(self.style.ERROR(string))


class BaseCommand(CommandBase):
    def __init_subclass__(self) -> None:
        # 2020-11-16 Renamed
        import warnings
        warnings.warn("Class has been renamed to 'CommandBase'", DeprecationWarning, 2)


class ConfirmationMixin(CommandMixin):
    """
    A mixin that adds a confirmation step to commands that write to database.
    """
    warning: Callable

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            '--no-input',
            action='store_true',
            help="skip confirmation step and run command immediately.",
        )
        super().add_arguments(parser)

    def confirm(self) -> bool:
        """
        Print confirmation message and fetch answer.
        """
        question = textwrap.dedent("""
            This operation will IRREVERSIBLY DESTROY any existing
            data for this application in the database.

            Are you sure you want to do this [y/N]? """)
        answer = input(question)
        if answer.lower().startswith('y'):
            return True
        else:
            return False

    def execute(self, *args: Any, **options: Any) -> Any:
        if options['no_input']:
            self.stdout.write(self.style.NOTICE(
                "Option '--no-input' given, skipping confirmation"))
        else:
            if not self.confirm():
                raise CommandError("Command aborted")
        return super().execute(*args, **options)
