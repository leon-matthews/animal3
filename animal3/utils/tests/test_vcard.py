
import datetime
import textwrap

from django.test import TestCase

from ..vcard import Address, Name, Card


def strip_indent(string: str) -> str:
    return textwrap.dedent(string).strip()


class TestAddress(TestCase):
    def test_adr(self) -> None:
        address = Address(
            '24e Fairlands Ave',
            'Waterview',
            'Auckland',
            '1026',
            'New Zealand',
            work=False,
            postal=False,
        )

        # ADR
        self.assertEqual(
            address.adr(),
            'ADR;HOME:'
            ';;24e Fairlands Ave;Waterview;Auckland;1026;New Zealand')

        # Types
        address.work = True
        self.assertEqual(
            address.adr(),
            'ADR;WORK:'
            ';;24e Fairlands Ave;Waterview;Auckland;1026;New Zealand')

        address.postal = True
        self.assertEqual(
            address.adr(),
            'ADR;WORK;POSTAL:'
            ';;24e Fairlands Ave;Waterview;Auckland;1026;New Zealand')

        # Plain text
        expected = strip_indent(
            """
            24e Fairlands Ave
            Waterview
            Auckland
            1026
            New Zealand
            """)
        self.assertEqual(address.text(), expected)
        self.assertEqual(str(address), expected)


class TestName(TestCase):
    def test_minimal(self) -> None:
        name = Name('John', 'Doe')
        self.assertEqual(name.n(), 'Doe;John;;;')
        self.assertEqual(name.fn(), 'John Doe')
        self.assertTrue(name.nickname is None)

    def test_full(self) -> None:
        name = Name(
            'John',
            'Jackson',
            additionals=['Philip', 'Paul'],
            nickname='JJ',
            prefixes=['Dr.'],
            suffixes=['Jr.', 'M.D.', 'A.C.P.']
        )

        # Structured
        self.assertEqual(
            name.n(),
            'Jackson;John;Philip,Paul;Dr.;Jr.,M.D.,A.C.P.')

        # Plain text
        expected = 'Dr. John Philip Paul Jackson Jr. M.D. A.C.P.'
        self.assertEqual(name.fn(), expected)
        self.assertEqual(str(name), expected)

        # Nickname
        self.assertEqual(name.nickname, 'JJ')


class TestCard(TestCase):
    def setUp(self) -> None:
        self.date = datetime.datetime(2015, 12, 8, 11, 48)
        self.home = Address(
            '24E Fairlands Ave',
            'Waterview',
            'Auckland',
            '1026',
            'New Zealand',
            work=False,
            postal=False,
        )
        self.work = Address(
            'PO Box 37735',
            'Parnell',
            'Auckland',
            '1151',
            'New Zealand',
            work=True,
            postal=True
        )

    def test_minimal(self) -> None:
        name = Name('Leon', 'Matthews', suffixes=['BSc'])
        card = Card(name)
        expected = strip_indent(
            """
            BEGIN:VCARD
            VERSION:2.1
            N:Matthews;Leon;;;BSc
            FN:Leon Matthews BSc
            UID:urn:uuid:0005b5ad-5fed-5902-895c-29b816c2d723
            END:VCARD
            """)
        self.assertMultiLineEqual(card.render(), expected)

    def test_full(self) -> None:
        name = Name('Leon', 'Matthews', nickname='LGP', suffixes=['BSc'])
        card = Card(
            name,
            addresses=[self.home, self.work],
            email='leon@example.com',
            organisation='Digital Advisor',
            photo='http://example.com/sexy.png',
            title='Technical Advisor',
            work_phone='+64 9 555-1234',
            updated=self.date,
        )

        expected = strip_indent("""
            BEGIN:VCARD
            VERSION:2.1
            N:Matthews;Leon;;;BSc
            FN:Leon Matthews BSc
            NICKNAME:LGP
            ADR;HOME:;;24E Fairlands Ave;Waterview;Auckland;1026;New Zealand
            ADR;WORK;POSTAL:;;PO Box 37735;Parnell;Auckland;1151;New Zealand
            EMAIL:leon@example.com
            ORG:Digital Advisor
            PHOTO;VALUE=URL:http://example.com/sexy.png
            REV:2015-12-08T11:48:00Z
            TEL;type=WORK:+64 9 555-1234
            TITLE:Technical Advisor
            UID:urn:uuid:acd69021-4920-540c-b82f-e66788d12853
            END:VCARD
        """)

        self.assertMultiLineEqual(card.render(), expected)
        self.assertMultiLineEqual(str(card), expected)
