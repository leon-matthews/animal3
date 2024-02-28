"""
Utilities for dealing with CSV data.

See:
    animal3.adapters.excel:
        Read data from an XLSX spreadsheet
    animal3.utils.testing.assertCSVEqualMixin:
        Provides a `assertCSVEqual()` method to a TestCase.
    animal3.utils.serialisers.CSVSerialiserBase:
        Provides flexible CSV export of a QuerySet.
"""

from collections import namedtuple
import csv
import re
from typing import Any, Dict, Iterator, List, NamedTuple, Set, TextIO

from .serialisers import CSVSerialiserBase as ActualCSVSerialiserBase
from .text import make_slugs


class CSVSerialiser(ActualCSVSerialiserBase):
    def __init_subclass__(cls, **kwargs: Any):
        # Deprecated: 2021 January
        import warnings
        warnings.warn(
            "animal3.utils.csv.CSVSerialiser has been moved "
            "and renamed 'animal3.utils.serialisers.CSVSerialiserBase'",
            category=DeprecationWarning,
            stacklevel=2)
        super().__init_subclass__(**kwargs)


class CSVSerialiserBase(ActualCSVSerialiserBase):
    def __init_subclass__(cls, **kwargs: Any):
        # Deprecated: 2021 January
        import warnings
        warnings.warn(
            "animal3.utils.csv.CSVSerialiserBase has been moved "
            "to 'animal3.utils.serialisers.CSVSerialiserBase'",
            category=DeprecationWarning,
            stacklevel=2)
        super().__init_subclass__(**kwargs)


class QuerysetSerialiser(ActualCSVSerialiserBase):
    def __init_subclass__(cls, **kwargs: Any):
        # Deprecated: 2021 January
        import warnings
        warnings.warn(
            "animal3.utils.csv.QuerysetSerialiser has been moved "
            "and renamed 'animal3.utils.serialisers.CSVSerialiserBase'",
            category=DeprecationWarning,
            stacklevel=2)
        super().__init_subclass__(**kwargs)


class DictReader:
    """
    Same as `csv.DictReader` but with cleaned field names.

    Field names make lower case and transformed to be legal Python
    variable names.

    Usage:

        with open(path, newline='') as csvfile:
            reader = DictReader(csvfile)
            for row in reader:
                ...

    Note the use of newline='' in the call to open(). This is recommended
    in the standard library docs

    See:
        https://docs.python.org/3/library/csv.html
    """
    def __init__(self, file_: TextIO, **kwargs: Any):
        self.reader = csv.DictReader(file_, **kwargs)
        assert self.reader.fieldnames is not None
        self.reader.fieldnames = make_slugs(self.reader.fieldnames)

    def __iter__(self) -> Iterator[Dict[str, str]]:
        return iter(self.reader)


class NamedTupleReader:
    """
    Read CSV file, using first heading row as namedtuple keys.

    Columns with no heading in the first row are skipped.

    The first key in the named tuple is 'row_index' and corresponds to the
    line number or spreadsheet index of the source file.
    """
    clean_heading_regex = re.compile(r'[^a-z0-9_]+')

    def __init__(self, csvfile: TextIO, skip_lines: int = 0):
        """
        Keep data in ordered dictionary.

        csvfile
           Open file object.
        """
        self.rows: List[NamedTuple] = []
        self.headings: List[str] = []
        self.headings_used: Set[str] = set()
        self.namedtuple = None
        self.skip_columns: List[int] = []
        self.skip_lines = skip_lines
        self.read_csv(csvfile)

    def __iter__(self) -> Iterator:
        return iter(self.rows)

    def read_csv(self, csvfile: TextIO) -> None:
        """
        Read CSV file.
        """
        # Skip header lines
        for _ in range(self.skip_lines):
            next(csvfile)

        # Read header line
        reader = csv.reader(csvfile)
        headings = next(reader)
        headings = [self._clean_heading(heading) for heading in headings]

        # Skip columns if heading empty
        self.skip_columns = [index for (index, h) in enumerate(headings) if not h]
        self.headings = [h for h in headings if h]
        names = ['row_index'] + self.headings
        Row = namedtuple('Row', names)                      # type: ignore[misc]

        # Read data
        for index, data in enumerate(reader, (2 + self.skip_lines)):
            for to_skip in reversed(self.skip_columns):
                del data[to_skip]
            data = [datum.strip() for datum in data]
            args = [index] + data
            row = Row(*args)
            self.rows.append(row)

    def _clean_heading(self, heading: str) -> str:
        """
        Convert heading into a valid Python identifier
        """
        cleaned = heading.lower()
        cleaned = self.clean_heading_regex.sub('_', cleaned)
        cleaned = cleaned.strip('_')
        return cleaned
