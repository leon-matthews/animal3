

class ExcelError(RuntimeError):
    """
    Catch-all for Runtime errors.
    """


class ExcelReaderError(ExcelError):
    """
    Reading spreadsheet when something unexpected happened.
    """


class ExcelWriterError(ExcelError):
    """
    Writing spreadsheet when something unexpected.
    """
