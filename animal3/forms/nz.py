
from django.db.models import TextChoices


class Regions(TextChoices):
    """
    New Zealand Regions (ISO 3166-2:NZ)
    https://en.wikipedia.org/wiki/ISO_3166-2:NZ
    """
    NORTHLAND = ('NZ-NTL', 'Northland')
    AUCKLAND = ('NZ-AUK', 'Auckland')
    WAIKATO = ('NZ-WKO', 'Waikato')
    BAY_OF_PLENTY = ('NZ-BOP', 'Bay of Plenty')
    GISBORNE = ('NZ-GIS', 'Gisborne')
    HAWKES_BAY = ('NZ-HKB', "Hawke's Bay")
    TARANAKI = ('NZ-TKI', 'Taranaki')
    MANAWATU_WANGANUI = ('NZ-MWT', 'Manawatu-Wanganui')
    WELLINGTON = ('NZ-WGN', 'Wellington')
    TASMAN = ('NZ-TAS', 'Tasman')
    NELSON = ('NZ-NSN', 'Nelson')
    MARLBOROUGH = ('NZ-MBH', 'Marlborough')
    WEST_COAST = ('NZ-WTC', 'West Coast')
    CANTERBURY = ('NZ-CAN', 'Canterbury')
    OTAGO = ('NZ-OTA', 'Otago')
    SOUTHLAND = ('NZ-STL', 'Southland')
