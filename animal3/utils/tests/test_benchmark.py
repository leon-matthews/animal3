
import logging
import time
from unittest import TestCase

from ..benchmark import benchmark
from ..logging import CaptureLogs


class BenchmarkTest(TestCase):
    """
    Capture the logging output of the benchmark utility.
    """

    @benchmark
    def slow(self) -> None:
        time.sleep(0.01)

    def test_as_decorator(self) -> None:
        # Benchmark code
        with CaptureLogs('animal3', logging.DEBUG) as log:
            self.slow()

        # Check captured logs
        self.assertEqual(len(log.records), 1)
        message = log.records[0].message
        # eg. 'slow(): 10.093ms'
        self.assertTrue(message.startswith("slow(): "))
        self.assertTrue(message.endswith("ms"))

    def test_benchmark_as_context_manager(self) -> None:
        # Benchmark code
        with CaptureLogs('animal3', logging.DEBUG) as log:
            with benchmark('slow context'):
                time.sleep(0.01)

        # Check captured logs
        self.assertEqual(len(log.records), 1)
        message = log.records[0].message
        # eg. 'slow(): 10.093ms'
        self.assertTrue(message.startswith("slow context: "))
        self.assertTrue(message.endswith("ms"))
