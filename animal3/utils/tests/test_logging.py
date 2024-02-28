
import logging
import textwrap

from django.test import SimpleTestCase

from ..logging import CaptureLogs, indent_records, LoggingWatcher

logger = logging.getLogger(__name__)


class CaptureLogsTest(SimpleTestCase):
    def test_simple(self) -> None:
        name = 'CaptureLogsTest'
        logger = logging.getLogger(name)

        with CaptureLogs(name) as logs:
            logger.debug("A debug message")
            logger.info("Another message, info this time")

        # logs
        self.assertIsInstance(logs, LoggingWatcher)

        # logs.output is a list of strings
        self.assertIsInstance(logs.output, list)
        self.assertEqual(len(logs.output), 2)
        expected = [
            'DEBUG:CaptureLogsTest:A debug message',
            'INFO:CaptureLogsTest:Another message, info this time',
        ]
        self.assertEqual(logs.output, expected)

        # logs.records is a list of `logging.LogRecord` objects
        self.assertIsInstance(logs.records, list)
        self.assertEqual(len(logs.records), 2)
        for record in logs.records:
            self.assertIsInstance(record, logging.LogRecord)
            self.assertEqual(record.name, 'CaptureLogsTest')
            self.assertEqual(record.filename, 'test_logging.py')
            self.assertEqual(record.funcName, 'test_simple')

        first = logs.records[0]
        self.assertEqual(first.levelname, 'DEBUG')
        self.assertEqual(first.levelno, logging.DEBUG)
        self.assertEqual(first.msg, 'A debug message')

        last = logs.records[1]
        self.assertEqual(last.levelname, 'INFO')
        self.assertEqual(last.levelno, logging.INFO)
        self.assertEqual(last.msg, 'Another message, info this time')


class IndentRecordsTest(SimpleTestCase):
    def setUp(self) -> None:
        name = 'CaptureLogsTest'
        logger = logging.getLogger(name)
        with CaptureLogs(name) as logs:
            logger.info("Another message, info this time")
            logger.debug("A debug message")
        self.records = logs.records

    def test_indent_records(self) -> None:
        output = indent_records(self.records)
        expected = textwrap.dedent("""
            Another message, info this time
                A debug message
        """).strip()
        self.assertEqual(output, expected)
