
import io
from typing import Any, Type

from django.core.exceptions import ImproperlyConfigured
from django.http import HttpRequest, HttpResponse
from django.views.generic.list import BaseListView

from .serialiser import ExcelSerialiserBase


class ExcelListView(BaseListView):
    excel_serialiser: Type[ExcelSerialiserBase]

    def __init__(self, **kwargs: Any):
        serialiser = getattr(self, 'excel_serialiser', None)
        if serialiser is None:
            raise ImproperlyConfigured("An 'excel_serialiser' class must be provided")

        self.model = self.excel_serialiser.model
        super().__init__(**kwargs)

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """
        Download XLSX file.

        Arguments:
            request:
                Incoming request.
            args:
                Passed on to the serialiser class.
            kwargs:
                Passed on to the serialiser class.

        Returns:
            An Excel file download
        """
        # XLSX
        serialiser = self.excel_serialiser(*args, **kwargs)
        serialiser.queryset = self.get_queryset()
        content = io.BytesIO()
        serialiser.write(content)
        content.seek(0)

        # Response
        response = HttpResponse(content_type='application/octet-stream')
        filename = serialiser.get_filename()
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response.content = content.read()
        return response
