
from pathlib import Path


DATA_FOLDER = Path(__file__).parent / 'data'

BOARD_HEADER = [
    'Thickness (mm)',
    'Colour',
    'Finish',
    'Has Grain',
    'Allow Partial',
    'Percentage Wastage',
    'Board Length (mm)',
    'Board Width (mm)',
    'Wholesale Price',
    'Retail Price',
    'Default',
]

BOARD_DATA = [{
    'thickness_mm': '16mm',
    'colour': 'Ashen Walnut',
    'finish': 'Embossed',
    'has_grain': 'Yes',
    'allow_partial': 'No',
    'percentage_wastage': None,
    'board_length_mm': 2400,
    'board_width_mm': 1200,
    'wholesale_price': 75.5,
    'retail_price': 100,
    'default': 'No',
}, {
    'thickness_mm': '16mm',
    'colour': 'Dark Walnut',
    'finish': 'Embossed',
    'has_grain': 'Yes',
    'allow_partial': 'No',
    'percentage_wastage': None,
    'board_length_mm': 2400,
    'board_width_mm': 1200,
    'wholesale_price': 75.5,
    'retail_price': 100,
    'default': 'No',
}]
