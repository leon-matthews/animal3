"""
Convert to and from multi-line addresses.

Post code and city handling is very New Zealand centric.
"""

from __future__ import annotations

import dataclasses
import re
from typing import Collection, Dict, Optional


NZ_CITIES = (
    'Auckland',
    'Christchurch',
    'Dunedin',
    'Hamilton',
    'Invercargill',
    'Lower Hutt',
    'Napier',
    'Nelson',
    'Palmerston North',
    'Porirua',
    'Tauranga',
    'Upper Hutt',
    'Wellington',
)


@dataclasses.dataclass(repr=False)
class Address:
    address1: str = ''
    address2: str = ''
    suburb: str = ''
    city: str = ''
    state: str = ''
    country: str = ''
    post_code: str = ''

    def asdict(
        self,
        *,
        exclude: Optional[Collection] = None,
        prefix: str = '',
    ) -> Dict[str, str]:
        """
        Build dictionary of address data.

        Args:
            exclude:
                Fields to exclude, eg. ('state',)
            prefix:
                Add prefix to field names, eg. 'shipping_'
        """
        if exclude is None:
            exclude = ()
        data = {}
        for key, value in dataclasses.asdict(self).items():
            if exclude and key in exclude:
                continue
            data[f"{prefix}{key}"] = value
        return data

    @classmethod
    def from_multiline(cls, string: str) -> Address:
        """
        Construct class from multiline string.
        """
        return from_multiline(string)

    def to_multiline(self, *, commas: Optional[bool] = False) -> str:
        """
        Build multi-line version of address.

        Args:
            commas:
                Set to True if you'd rather have a single-line comma-delimited.

        Returns:
            Address as string.
        """
        return to_multiline(self, commas=commas)

    def __bool__(self) -> bool:
        """
        True if any values are not falsey.
        """
        values = [getattr(self, f.name) for f in dataclasses.fields(self)]
        return any(values)

    def __repr__(self) -> str:
        """
        Don't bother printing fields with default values.
        """
        items = (
            (f.name, value)
            for f in dataclasses.fields(self)
            if (value := getattr(self, f.name))
        )
        formatted = ", ".join(f"{name}={value!r}" for name, value in items)
        return f"{self.__class__.__name__}({formatted})"


# Regexes
re_cities = re.compile('|'.join(NZ_CITIES), re.I)
re_postcode = re.compile(r'\d\d\d\d')
re_lines = re.compile(r'[,\n]')


def to_multiline(address: Address, *, commas: Optional[bool] = False) -> str:
    """
    Produce nicely-formatted multi-line address from dataclass.

        >>> a = Address(address1='123 Main Rd.', city='Auckland', post_code='1026')
        >>> print(to_multiline(a))
        123 Main Rd.
        Auckland 1026

    Args:
        address:
            An instance of the `Address` dataclass.

    Returns:
        Multi-line address string.
    """
    # Fields in definition order, one per line
    exclude = ('post_code')
    parts = []
    for field in dataclasses.fields(address):
        value = getattr(address, field.name)
        if value and field.name not in exclude:
            parts.append(value)

    # Add post code to end of last element
    if address.post_code:
        parts[-1] = f"{parts[-1]} {address.post_code}"

    # Build string
    delimiter = ', ' if commas else '\n'
    string = delimiter.join(parts)
    return string


def from_multiline(string: str) -> Address:
    """
    Best-effort attempt to pull out address parts from free-form format.

    Despite name it can handle comma-delimited addresse too.

        >>> from_multiline("123 Main Rd, auckland 1026")
        Address(address1='123 Main Rd', city='Auckland', post_code='1026')

    Args:
        string:
            Multi-line, free-form address string.

    Returns:
        An instance of an `Address` dataclass.
    """
    # Load fields line-by-line
    fields = {}
    lines = [stripped for line in re_lines.split(string) if (stripped := line.strip())]
    for name in (f.name for f in dataclasses.fields(Address)):
        try:
            fields[name] = lines.pop(0)
        except IndexError:
            fields[name] = ''

    # Specialisations for...

    # ...post code
    for key, value in reversed(fields.items()):
        if (match := re_postcode.search(value)):
            # Four digit number found near the end? Remove and reassign.
            fields[key] = value.replace(match[0], '').strip()
            fields['post_code'] = match[0]
            break

    # ...city
    for key, value in reversed(fields.items()):
        if (match := re_cities.search(value)):
            # City found!
            if key != 'city':
                # Move city correct field
                fields[key] = ''
                fields['city'] = match[0].title()

                # Special case for suburbs in 3-line addresses
                if not fields['suburb'] and fields['address2']:
                    fields['suburb'] = fields['address2']
                    fields['address2'] = ''

    # Build!
    address = Address(**fields)
    return address
