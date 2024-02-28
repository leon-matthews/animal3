
import random
from string import ascii_uppercase
from typing import Optional

from animal3.utils.addresses import Address
from animal3.utils.text import make_slug

from .text import numeric_string
from .utils import RandomLine


__all__ = (
    'address',
    'address_multiline',
    'address_postcode',
    'address_street',
    'city',
    'email',
    'first_name',
    'first_name_female',
    'first_name_male',
    'full_name',
    'job',
    'last_name',
    'phone',
    'suburb',
    'website',
)


STREET_ENDINGS = (
    'Avenue',
    'Ave',
    'Drive',
    'Lane',
    'Place',
    'Pl',
    'Road',
    'Rd',
    'Street',
    'St',
    'Way',
)

city = RandomLine('cities.txt')
first_name = RandomLine('first_names_male.txt', 'first_names_female.txt')
first_name_female = RandomLine('first_names_female.txt')
first_name_male = RandomLine('first_names_male.txt')
job = RandomLine('jobs.txt')
last_name = RandomLine('last_names.txt')
suburb = RandomLine('suburbs.txt')

# See `address_street()`, this is just the bare name.
_street = RandomLine('streets.txt')


def address() -> Address:
    """
    Build Address dataclass.
    """
    address_suburb = suburb() if random.randint(0, 1) else ''
    post_code = address_postcode()
    country = '' if random.randint(0, 4) else "New Zealand"
    return Address(
        address1=address_street(),
        address2='',
        suburb=address_suburb,
        city=city(),
        state='',
        post_code=post_code,
        country=country,
    )


def address_multiline() -> str:
    """
    Build 2-4 line address.
    """
    # Street
    parts = [address_street()]

    # Suburb?
    if random.randint(0, 1):
        parts.append(suburb())

    # City + postcode
    if random.randint(0, 2):
        parts.append(f"{city()} {address_postcode()}")
    else:
        parts.append(city())

    # Pedantic?
    if not random.randint(0, 4):
        parts.append("New Zealand")

    return "\n".join(parts)


def address_postcode() -> str:
    """
    Just the postcode part of an address.

    Returns:
        Postcode, eg. '1234'
    """
    return numeric_string(4)


def address_street() -> str:
    """
    Just the street part of address.

    Returns:
        Street part of address, eg. '123 Happy Valley Rd.'
    """
    number = int(random.triangular(1, 100, 1))  # 1-100
    unit = ''
    if random.randint(0, 1):
        unit = ascii_uppercase[int(random.triangular(1, 5, 1))]
    ending = random.choice(STREET_ENDINGS)
    return f"{number}{unit} {_street()} {ending}"


def email(name: Optional[str] = None) -> str:
    if name is None:
        username = numeric_string(8)
    else:
        username = make_slug(name, max_length=64).replace('-', '.')
    return f"{username}@example.com"


def full_name() -> str:
    return f"{first_name()} {last_name()}"


def phone() -> str:
    prefix = random.choice(('021', '022', '025', '03', '04', '09'))
    parts = (prefix, '555', numeric_string(4))
    separator = random.choice(('', '-', ' '))
    return separator.join(parts)


def website(name: Optional[str] = None) -> str:
    if name is None:
        username = numeric_string(8)
    else:
        username = make_slug(name, max_length=64).replace('-', '.')
    return f"https://{username}.com/"
