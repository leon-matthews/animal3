
import datetime
from unittest import SkipTest, TestCase

from animal3.utils.testing import TempFolderMixin

try:
    from ..exceptions import ExcelWriterError
    from ..writer import ExcelWriter
except ImportError:                                         # pragma: no cover
    raise SkipTest('OpenPyXL not installed')

from . import BOARD_DATA, BOARD_HEADER, DATA_FOLDER


class ExcelWriterReadTest(TestCase):
    """
    Test reading existing spreadsheet using writer class.
    """
    reader: ExcelWriter

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        path = DATA_FOLDER / 'products.xlsx'
        cls.reader = ExcelWriter(path)

    def test_read_first(self) -> None:
        """
        Read from default worksheet.
        """
        rows = [row for row in self.reader.read()]
        self.assertEqual(rows, BOARD_DATA)

    def test_read_skip_rows(self) -> None:
        """
        Change worksheet and read its data.
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


class ExcelWriterTest(TempFolderMixin, TestCase):
    """
    Test writing spreadsheet using writer class.
    """
    def test_save_new(self) -> None:
        """
        Create new, empty, spreadsheet file.
        """
        path = self.temp_folder / 'new.xlsx'
        self.assertFalse(path.exists())
        writer = ExcelWriter()
        writer.save(path)
        self.assertTrue(path.is_file())
        self.assertGreater(path.stat().st_size, 4096)

    def test_save_no_path(self) -> None:
        """
        No path given to either initialiser or save method.
        """
        writer = ExcelWriter()
        message = r"^Cannot save without a path$"
        with self.assertRaisesRegex(ExcelWriterError, message):
            writer.save()

    def test_write_title(self) -> None:
        path = self.temp_folder / 'title.xlsx'
        self.assertFalse(path.exists())
        writer = ExcelWriter()
        writer.add_title("Title Test")
        writer.add_subtitle(datetime.date.today().isoformat())
        writer.add_blank()
        writer.add_text("Leon woz here")
        writer.save(path)
        self.assertTrue(path.is_file())
        self.assertGreater(path.stat().st_size, 4096)

    def test_write_data(self) -> None:
        path = self.temp_folder / 'data.xlsx'
        self.assertFalse(path.exists())
        writer = ExcelWriter()
        writer.add_title("Board Data Test")
        writer.add_text(datetime.date.today().isoformat())
        writer.add_blank()
        writer.add_header(BOARD_HEADER)
        rows = [tuple(row.values()) for row in BOARD_DATA]
        writer.add_rows(rows)
        writer.save(path)
        self.assertTrue(path.is_file())
        self.assertGreater(path.stat().st_size, 4096)
