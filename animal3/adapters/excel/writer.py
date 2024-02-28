
import datetime
from pathlib import Path
from typing import Any, Iterable, List, Optional, Union

from openpyxl import Workbook
from openpyxl.cell import Cell
from openpyxl.styles import Font

from .exceptions import ExcelWriterError
from .reader import ExcelReader, open_spreadsheet


class ExcelWriter(ExcelReader):
    """
    Open spreadsheet in read/write mode and add functions to write data.

    Multiple worksheets per spreadsheet are supported.

    Note that every function than writes to a worksheet writes an entire row
    by design, to streamline the common-case:

        >>> xl = ExcelWriter(path)
        >>> xl.add_header(header)
        >>> for row in data:
        >>>     xl.add_row(row)
        >>> xl.save()

    """
    default_font: str = 'Calibri'       # OpenPyXL's default font
    default_size: int = 11              # OpenPyXL's default font size

    def __init__(self, path: Optional[Path] = None):
        """
        Initialiser.

        Args:
            path:
                Optionally open existing spreadsheet file.
        """
        self.path = path
        if self.path is None:
            self.workbook = Workbook()
        else:
            self.path = Path(path)
            self.workbook = open_spreadsheet(self.path, 'w')

        self.header_max_widths = []
        self.header_widths = []
        self.reset()

    def save(self, path: Optional[Path] = None) -> None:
        """
        Save current state of workbook back to file.

        Args:
            path:
                Path used in initialiser will be used if not given.

        Returns:
            None
        """
        # Replace existing?
        if path is not None:
            self.path = Path(path)

        # Not set here *or* in initialiser?
        if self.path is None:
            raise ExcelWriterError('Cannot save without a path')

        self.workbook.save(self.path)

    def add_blank(self) -> None:
        """
        Write blank row.
        """
        self.add_text('')

    def add_subtitle(self, subtitle: str, size=default_size) -> None:
        """
        Write bold, normal-sized text subtitle to current row.

        Args:
            subtitle:
                One-line text, eg. help string or date, eg. 113 Oct 2023'
        """
        self.add_text(subtitle, bold=True, size=size)

    def add_text(self, text: str, font=default_font, **kwargs: Any):
        """
        Write a line of text to the current row.

        Args:
            text:
                Single-line of text to write.
            kwargs:
                Arguments to OpenPyXL's Font() object.

        See:
            https://openpyxl.readthedocs.io/en/stable/styles.html
        """
        # No font needed
        sheet = self.workbook.active
        if font == self.default_font and not kwargs:
            sheet.append((text,))
            return

        # Custom format
        font_size = kwargs.get('size', self.default_size)
        cell = Cell(sheet, value=text)
        cell.font = Font(font, **kwargs)
        sheet.append((cell,))

        # Tweak row height
        if font_size != self.default_size:
            height_factor = 1.5
            row_dimensions = sheet.row_dimensions[cell.row]
            row_dimensions.height = int(font_size * height_factor)

    def add_title(self, title: str, size=16) -> None:
        """
        Write large, bold text to current row.

        Args:
            title:
                Worksheet title to write, eg. 'Stock Status'
        """
        self.add_text(title, bold=True, size=size)

    def add_header(self, header: Iterable[str]) -> List[int]:
        """
        Write header row to table.

        Returns:
            List characters written to each cell.
        """
        cells = []
        lengths = []
        sheet = self.workbook.active
        font = Font(self.default_font, bold=True)
        for text in header:
            lengths.append(len(text))
            cell = Cell(sheet, value=text)
            cell.font = font
            cells.append(cell)
        sheet.append(cells)

        # Tweak column width
        for cell, length in zip(cells, lengths):
            dimensions = sheet.column_dimensions[cell.column_letter]
            calculated_width = int(round((length + 2) * 1.2, 0))   # Magic
            dimensions.width = calculated_width

    def add_rows(
        self,
        rows: Iterable[Iterable[Union[float, int, str, datetime.datetime]]],
    ) -> None:
        """
        Write table of data to worksheet.

        Args:
            rows:
                Iterable of row data. Each row is a list or tuple containing
                either string, float, int, or datetime.datetime values.

        Returns:
            None
        """
        sheet = self.workbook.active
        for row in rows:
            sheet.append(row)
