
from unittest import SkipTest, TestCase

try:
    from ..exceptions import ExcelReaderError
    from ..reader import ExcelReader, open_spreadsheet
except ImportError:                                         # pragma: no cover
    raise SkipTest('OpenPyXL not installed')

from . import BOARD_DATA, DATA_FOLDER


class ExcelReaderErrors(TestCase):
    def test_bad_file_type(self) -> None:
        message = r"Invalid file given: 'commonmark.md'"
        with self.assertRaisesRegex(ExcelReaderError, message):
            path = DATA_FOLDER / 'commonmark.md'
            ExcelReader(path)

    def test_bad_file_type2(self) -> None:
        message = "^Invalid file given: 'old.xls'$"
        with self.assertRaisesRegex(ExcelReaderError, message):
            path = DATA_FOLDER / 'old.xls'
            ExcelReader(path)

    def test_bad_path(self) -> None:
        message = r"No such file or directory: '/.*/no-such-file'$"
        with self.assertRaisesRegex(ExcelReaderError, message):
            path = DATA_FOLDER / 'no-such-file'
            ExcelReader(path)

    def test_bad_open_mode(self) -> None:
        message = r"Unknown mode: 'x'$"
        with self.assertRaisesRegex(ExcelReaderError, message):
            open_spreadsheet(None, 'x')

    def test_read_empty_worksheet(self) -> None:
        """
        Worksheet completely empty.
        """
        path = DATA_FOLDER / 'products.xlsx'
        reader = ExcelReader(path)
        reader.set_worksheet('Empty Sheet')
        message = r"^Could not find data in worksheet 'Empty Sheet'$"
        with self.assertRaisesRegex(ExcelReaderError, message):
            next(reader.read())

    def test_no_data_table(self) -> None:
        """
        Worksheet has content - but no data table.
        """
        path = DATA_FOLDER / 'products.xlsx'
        reader = ExcelReader(path)
        reader.set_worksheet('No Data Table')
        message = r"^Could not find data in worksheet 'No Data Table'$"
        with self.assertRaisesRegex(ExcelReaderError, message):
            next(reader.read())


class ExcelReaderTest(TestCase):
    reader: ExcelReader

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        path = DATA_FOLDER / 'products.xlsx'
        cls.reader = ExcelReader(path)

    def setUp(self) -> None:
        # Reset spreadheet reader before each operation
        self.reader.reset()

    def test_get_worksheet(self) -> None:
        self.assertEqual(self.reader.get_worksheet(), 'Simple')

    def test_get_worksheets(self) -> None:
        self.assertEqual(
            self.reader.get_worksheets(),
            [
                'Simple',
                'Skip Rows',
                'Too Few Data',
                'Too Many Data',
                'Odd Header Types',
                'Empty Sheet',
                'No Data Table',
            ],
        )

    def test_read_simple(self) -> None:
        """
        Read simple table where table is nice and square.
        """
        rows = [row for row in self.reader.read()]
        self.assertEqual(rows, BOARD_DATA)

    def test_read_skip_rows(self) -> None:
        self.reader.set_worksheet('Skip Rows')
        rows = [row for row in self.reader.read()]
        self.assertEqual(rows, BOARD_DATA)

    def test_read_too_few_data(self) -> None:
        """
        Fill in the blanks if too few fields found in row data.
        """
        self.reader.set_worksheet('Too Few Data')
        rows = [row for row in self.reader.read()]
        expected = [{
            'header': 'One',
            'header2': 'Two',
            'header3': None,
        }, {
            'header': None,
            'header2': 'Two',
            'header3': 'Three',
        }]
        self.assertEqual(rows, expected)

    def test_read_too_few_data_change_restval(self) -> None:
        """
        Fill in the blanks if too few fields found in row data.
        """
        self.reader.set_worksheet('Too Few Data')
        rows = [row for row in self.reader.read(restval='')]
        expected = [{
            'header': 'One',
            'header2': 'Two',
            'header3': '',
        }, {
            'header': None,
            'header2': 'Two',
            'header3': 'Three',
        }]
        self.assertEqual(rows, expected)

    def test_read_too_many_data(self) -> None:
        """
        Capture excess data if row has more fields than header.
        """
        self.reader.set_worksheet('Too Many Data')
        rows = [row for row in self.reader.read()]
        expected = [{
            'header': 'One',
            'header2': 'Two',
            'header3': 'Three',
            None: ['Four'],
        }, {
            'header': 'One',
            'header2': 'Two',
            'header3': 'Three',
            None: ['Four', 'Five', 'Six'],
        }]
        self.assertEqual(rows, expected)

    def test_read_too_many_data_change_restkey(self) -> None:
        """
        Capture excess data if row has more fields than header.
        """
        self.reader.set_worksheet('Too Many Data')
        rows = [row for row in self.reader.read(restkey='excess')]
        expected = [{
            'header': 'One',
            'header2': 'Two',
            'header3': 'Three',
            'excess': ['Four'],
        }, {
            'header': 'One',
            'header2': 'Two',
            'header3': 'Three',
            'excess': ['Four', 'Five', 'Six'],
        }]
        self.assertEqual(rows, expected)

    def test_read_odd_header_types(self) -> None:
        """
        Header row with missing or non-string types.
        """
        self.reader.set_worksheet('Odd Header Types')
        rows = [row for row in self.reader.read()]
        expected = [{
            'one': 1,
            '2': 2,
            '31': 3,
            '_': 4,
            'five': 5,
            '2006_06_06_000000': 6,
        }]
        self.assertEqual(rows, expected)

    def test_restkey_clash(self) -> None:
        """
        Chosen restkey clashes with generated field names.
        """
        reader = self.reader.read(restkey='default')
        message = r"^Given restkey 'default' clashes with fieldnames$"
        with self.assertRaisesRegex(ValueError, message):
            next(reader)

    def test_set_worksheet(self) -> None:
        self.assertEqual(self.reader.get_worksheet(), 'Simple')
        self.reader.set_worksheet('Too Few Data')
        self.assertEqual(self.reader.get_worksheet(), 'Too Few Data')

    def test_set_worksheet_default(self) -> None:
        self.reader.set_worksheet('Too Few Data')
        self.reader.set_worksheet()
        self.assertEqual(self.reader.get_worksheet(), 'Simple')

    def test_set_worksheet_error(self) -> None:
        message = r"^'Worksheet Silly Name does not exist.'$"
        with self.assertRaisesRegex(KeyError, message):
            self.reader.set_worksheet('Silly Name')

    def test_build_fieldnames(self) -> None:
        header = ('Header', None, 'header', None, 'HEADER', None, None)
        fieldnames = self.reader._build_fieldnames(header)
        expected = ('header', '_', 'header2', '_2', 'header3')
        self.assertEqual(fieldnames, expected)
