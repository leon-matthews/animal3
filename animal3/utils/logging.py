
import collections
from contextlib import contextmanager
import logging
from typing import Iterable, Iterator


LoggingWatcher = collections.namedtuple("LoggingWatcher", ["records", "output"])


class CapturingHandler(logging.Handler):
    """
    A logging handler capturing all (raw and formatted) logging output.
    """
    def __init__(self) -> None:
        logging.Handler.__init__(self)
        self.watcher = LoggingWatcher([], [])

    def emit(self, record: logging.LogRecord) -> None:
        self.watcher.records.append(record)
        msg = self.format(record)
        self.watcher.output.append(msg)


class CaptureLogs:
    """
    A context manager to capture log messages.

    Adapted from Python3 the standard library code used to
    implement ``TestCase.assertLogs()``.

    For example:

        with CaptureLogs() as logs:
            ...

    Or:

        with CaptureLogs('contact', logging.WARNING) as logs:
            ...

    Produce a simple list of message strings using a list comprehension::

        messages = [record.message for record in logs.records]

    Returns:
        A `logging.LoggingWatcher` instance. Its `records` attribute contains a list of
        `logging.LogRecord` instances.
    """
    LOGGING_FORMAT: str = "%(levelname)s:%(name)s:%(message)s"
    msg: str

    def __init__(self, logger_name: str = '', level: int = logging.DEBUG):
        """
        Initialiser.

        Args:
            logger_name:
                Restrict capture to given logger, or capture all if blank.
            level:
                Capture logs of this level and higher.
        """
        self.logger_name = logger_name
        self.logger = logging.getLogger(self.logger_name)
        self.level = level

    def __enter__(self) -> LoggingWatcher:
        formatter = logging.Formatter(self.LOGGING_FORMAT)
        handler = CapturingHandler()
        handler.setFormatter(formatter)
        self.watcher = handler.watcher
        self.old_handlers = self.logger.handlers[:]
        self.old_level = self.logger.level
        self.old_propagate = self.logger.propagate
        self.logger.handlers = [handler]
        self.logger.setLevel(self.level)
        self.logger.propagate = False
        return handler.watcher

    def __exit__(self, exc_type, exc_val, exc_tb):          # type: ignore[no-untyped-def]
        self.logger.handlers = self.old_handlers
        self.logger.propagate = self.old_propagate
        self.logger.setLevel(self.old_level)

        # Always allow exceptions to be raised
        return False


def indent_records(records: Iterable[logging.LogRecord]) -> str:
    """
    Produce nicely-indented plain-text formatting for
    given list of log record objects.
    """
    max_level = max(set(record.levelno for record in records))
    lines = []
    for record in records:
        depth = ((max_level - record.levelno) // 5) * 2
        indent = ' ' * depth
        if record.levelno == max_level:
            lines.append('')
        lines.append(indent + record.message)
    formatted = '\n'.join(lines)
    return formatted.strip()


@contextmanager
def logger_hush(level: int = logging.ERROR) -> Iterator[None]:
    """
    Context manager to disable logging at or below the given level.

            with logger_hush():
                noisy_operation()

    Especially useful when writing unittests. Although in that case, you may
    want to try the `CaptureLogs` context manager to test logging messages.
    """
    logging.disable(level)
    try:
        yield
    finally:
        logging.disable(logging.NOTSET)
