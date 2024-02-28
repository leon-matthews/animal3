
import datetime
from decimal import Decimal
from tempfile import NamedTemporaryFile
from typing import Any, BinaryIO, List, Union

from django.conf import settings
from django.db import models
from django.utils.encoding import force_str

from animal3.utils.serialisers import QuerysetSerialiser

from .writer import ExcelWriter


class ExcelSerialiserBase(QuerysetSerialiser):
    """
    Prepare data for export to spreadsheet.
    """
    file_suffix = 'xlsx'

    def excel_value(self, value: Any) -> Union[datetime.datetime, float, int, str]:
        """
        Convert value to one of the four allowed types for an Excel spreadsheet.
        """
        value_type = type(value)

        if value is None:
            value = ''
        if value_type is bool:
            value = 'Yes' if value else ''
        elif value_type is datetime.datetime:
            value = value.isoformat()
        elif value_type is int or value_type is float:
            pass
        elif value_type is Decimal:
            value = float(value)
        else:
            value = force_str(value)

        return value

    def get_header(self) -> List[str]:
        """
        Get the table row.

        Returns (list):
            Verbose names for all fields.
        """
        return self.get_field_names_verbose()

    def get_row(self, obj: models.Model) -> List[str]:
        """
        Values may be either string, float, int, or datetime.datetime values.
        """
        original = super().get_row(obj)
        row = []
        for value in original:
            row.append(self.excel_value(value))
        return row

    def write(self, output: BinaryIO) -> None:
        """
        Write the bytes of Excel file to the given file-like object.

        output
            May be a HTTP response, a StringIO, or... a file.

        Returns:
            None
        """
        with NamedTemporaryFile(
            prefix=f"{settings.SITE_DOMAIN}_",
            suffix='.xlsx',
        ) as tmp:
            # Create
            writer = ExcelWriter()
            writer.add_header(self.get_header())
            writer.add_rows(self.get_rows())
            writer.save(tmp.name)

            # Read bytes
            content = tmp.read()

        # Write bytes to output
        output.write(content)
