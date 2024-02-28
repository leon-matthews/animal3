"""
Render a vCard (.vcf) file.

We have to use the almost 20 year-old version 2.1 (Sep. 1996) of the vCard
specification here, as it's all our friends from Microsoft support
in Outlook.

This is especially vexing, as version 4 was released all the way back
in 2011 (see IETF's RFC 6350), while v3 was born in 1998.
"""

from typing import Any, Optional
import uuid


class Address:
    def __init__(
        self,
        street: str,
        city: str,
        state: str,
        post_code: str,
        country: str,
        work: bool = True,
        postal: bool = True
    ):
        """
        Self explanitory for the most part.

        In addition to the usual fields, there are three fields that determine
        the type of the address shown:

        work
            `True` if address is work, `False` for home.
        postal
            `True` for postal addresses, `False` for physical.
        preferred
            `True` if this address should be the preferred. Only one address
            should be have preferred set to `True`.
        """
        self.street = street
        self.city = city
        self.state = state
        self.post_code = post_code
        self.country = country
        self.work = work
        self.postal = postal

    def adr(self) -> str:
        parts = [
            '',                     # post office box; (must be empty)
            '',                     # the extended address; (must be empty)
            self.street,            # the street address;
            self.city,              # the locality (e.g., city);
            self.state,             # the region (e.g., state or province);
            self.post_code,
            self.country,
        ]

        key = ['ADR']
        key.append('WORK' if self.work else 'HOME')
        if self.postal:
            key.append('POSTAL')
        return "{}:{}".format(';'.join(key), ';'.join(parts))

    def text(self) -> str:
        parts = [
            self.street,
            self.city,
            self.state,
            self.post_code,
            self.country,
        ]
        return '\n'.join(parts)

    def __str__(self) -> str:
        return self.text()


class Name(object):
    """
    Name object to wrap the sillyness that happens in the vCard 2.1 and 3.0
    'N' field.

    A rose by this name would smell just as sweet, but would mayhaps confuse
    the gentle bard.
    """
    def __init__(self, first: str, last: str, **kwargs: Any):
        """
        first
            Required first name.

        last
            Required last name

        Keyword-only arguments:

        additionals
            Optional list or tuple of middle names.

        nickname
            Optional nickname

        prefixes
            Optional list of tuple of honorific prefixes.

        suffixes
            Optional list of tuple of honorific suffixes.
        """
        self.first = first
        self.last = last
        self.additionals = kwargs.get('additionals', [])
        self.nickname = kwargs.get('nickname')
        self.prefixes = kwargs.get('prefixes', [])
        self.suffixes = kwargs.get('suffixes', [])

    def n(self) -> str:
        """
        Format name according to rules for 'N' field.
        """
        parts = [
            self.last,
            self.first,
            ','.join(self.additionals),
            ','.join(self.prefixes),
            ','.join(self.suffixes),
        ]
        return ";".join(parts)

    def fn(self) -> str:
        """
        Format name according to rules for 'FN' field.
        """
        parts = [
            ' '.join(self.prefixes),
            self.first,
            ' '.join(self.additionals),
            self.last,
            ' '.join(self.suffixes)
        ]
        parts = [p for p in parts if p]
        return " ".join(parts)

    def __str__(self) -> str:
        return self.fn()


class Card(object):
    """
    The `Card` class is the parent to all the others.
    """

    def __init__(self, name: Name, **kwargs: Any):
        """
        Initialiser.

        name
            A `vcard.Name()` object. The only required field.

        Many option keyword arguments are supported:

        addresses
            A list of `vcard.Address()` objects.
        email
            Primary email address
        organisation
            Name of organisation
        photo
            URL to photo of person
        title
            Job title
        updated
            datetime.datetime() object of last update to details.
        work_phone
            Main number for business calls
        """
        self.name = name
        self.addresses = kwargs.get('addresses', [])
        self.email = kwargs.get('email')
        self.organisation = kwargs.get('organisation')
        self.photo = kwargs.get('photo')
        self.title = kwargs.get('title')
        self._updated = kwargs.get('updated')
        self.work_phone = kwargs.get('work_phone')

    def render(self) -> str:
        """
        Render object into a plain-text vCard format, version 2.1.
        """
        # Required
        parts = []
        parts.append('BEGIN:VCARD')
        parts.append('VERSION:2.1')
        assert isinstance(self.name, Name)
        parts.append('N:' + self.name.n())
        parts.append('FN:' + self.name.fn())

        # Optional
        if self.name.nickname:
            parts.append('NICKNAME:' + self.name.nickname)
        for address in self.addresses:
            assert isinstance(address, Address)
            parts.append(address.adr())
        if self.email:
            parts.append('EMAIL:' + self.email)
        if self.organisation:
            parts.append('ORG:' + self.organisation)
        if self.photo:
            parts.append('PHOTO;VALUE=URL:' + self.photo)
        if self.updated:
            parts.append('REV:' + self.updated)
        if self.work_phone:
            parts.append('TEL;type=WORK:' + self.work_phone)
        if self.title:
            parts.append('TITLE:' + self.title)
        parts.append('UID:urn:uuid:' + self.uuid())
        parts.append('END:VCARD')
        return "\n".join(parts)

    @property
    def updated(self) -> Optional[str]:
        """
        Datetime record last updated as UTC/ISO timestamp.
        """
        if not self._updated:
            return None

        string = str(self._updated.isoformat() + 'Z')
        return string

    def uuid(self) -> str:
        """
        Build a UUID for this version of this vCard.

        Value returned is based on hash of full name, time updated,
        and (if given) the 'rev' and 'email' fields.
        """
        data = self.name.fn()
        updated = self.updated
        if updated is not None:
            data += updated
        if self.email:
            data += self.email

        return str(uuid.uuid5(uuid.NAMESPACE_URL, data))

    def __str__(self) -> str:
        return self.render()
