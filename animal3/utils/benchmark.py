
from contextlib import contextmanager
from functools import wraps
import logging
import time
from typing import Any


logger = logging.getLogger(__name__)


def benchmark(obj: Any) -> Any:
    """
    Benchmarking tool that can be used as a decorator or a context manager.

    Understanding exactly how every line of this function works is a great
    test of your Python mojo!

    Credit for the heavy lifting to Dave Beazley:
    http://dabeaz.blogspot.co.nz/2010/02/function-that-works-as-context-manager.html
    """
    @contextmanager
    def timethis() -> Any:
        start = time.time()
        yield
        end = time.time()
        label = obj.__name__ + '()' if hasattr(obj, '__name__') else str(obj)
        logger.critical("%s: %0.3fms" % (label, (end - start) * 1000))

    # Callable?
    if hasattr(obj, '__call__'):
        @wraps(obj)
        def timed(*args: Any, **kwargs: Any) -> Any:
            with timethis():
                return obj(*args, **kwargs)
        return timed
    else:
        return timethis()
