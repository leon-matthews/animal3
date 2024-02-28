
from pathlib import Path
from typing import List, NamedTuple

from django.test import SimpleTestCase

from ..csv import DictReader, NamedTupleReader

from . import DATA_FOLDER


class DictReaderTest(SimpleTestCase):
    def test_dict_reader(self) -> None:
        path = DATA_FOLDER / 'headings.csv'
        self.assertTrue(path.is_file())

        data = []
        with open(path, newline='') as csvfile:
            reader = DictReader(csvfile)
            for row in reader:
                data.append(row)

        self.assertEqual(len(data), 3)
        expected = {
            'stock_keeping_unit_sku': '2326',
            'size': 'Large ',
            'retail_price': '34.7392',
        }
        self.assertEqual(data[0], expected)


class NamedTupleReaderTest(SimpleTestCase):
    rows: List[NamedTuple]

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        path = Path(DATA_FOLDER) / 'test_data.csv'
        with open(path, 'rt') as fp:
            reader = NamedTupleReader(fp, skip_lines=1)
            cls.rows = [row for row in reader]

    def test_named_tuple_reader(self) -> None:
        self.assertEqual(len(self.rows), 3)
        first = self.rows[0]
        self.assertEqual(first._fields, ('row_index', 'id', 'size', 'price'))
        self.assertEqual(tuple(first), (3, '2326', 'Large', '34.7392'))

        last = self.rows[-1]
        self.assertEqual(tuple(last), (5, '2324', 'Small', '20.950'))
