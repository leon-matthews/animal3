
import decimal
import json
import textwrap
from typing import Mapping
from unittest import TestCase

from animal3.utils.testing import assert_deprecated, DocTestLoader, multiline

from .. import text
from ..text import (
    camelcase_to_underscore,
    capitalise_title,
    currency,
    currency_big,
    file_size,
    find_singles,
    force_ascii,
    Fraction,
    html_attributes,
    join_and,
    JSONEncoderForHTML,
    line_random,
    lines,
    make_slug,
    make_slugs,
    MultiReplace,
    paragraphs_split,
    paragraphs_wrap,
    phone_add_separators,
    phone_normalise,
    plain_quotes,
    reverse_replace,
    sentences,
    split_name,
    split_sentences,
    shorten,
    strip_blank,
    strip_tags,
    trademe_emphasis,
    _unique_suffix,
)

from . import DATA_FOLDER
from typing import List, Tuple, Union


class DocTests(TestCase, metaclass=DocTestLoader, test_module=text):
    pass


class CamelCaseToUnderscoreTest(TestCase):
    def test_easy(self) -> None:
        self.assertEqual(camelcase_to_underscore('Address1'), 'address1')
        self.assertEqual(camelcase_to_underscore('ChangeCode'), 'change_code')

    def test_with_number(self) -> None:
        self.assertEqual(camelcase_to_underscore('Person1Email'), 'person1_email')

    def test_keywords(self) -> None:
        """
        Keywords make be munged to avoid producing Python keywords.
        """
        self.assertEqual(camelcase_to_underscore('Class'), 'class')
        self.assertEqual(camelcase_to_underscore('Class', avoid_keywords=True), 'class_')

    def test_valid_indentifier(self) -> None:
        self.assertEqual(camelcase_to_underscore('1BigProblem'), 'big_problem')

    def test_whitespace(self) -> None:
        self.assertEqual(camelcase_to_underscore('First Name'), 'first_name')
        self.assertEqual(
            camelcase_to_underscore(' Too much   whitespace '), 'too_much_whitespace')


class CapitaliseTitleTest(TestCase):
    def test_empty(self) -> None:
        self.assertEqual(capitalise_title(''), '')
        self.assertEqual(capitalise_title(' '), '')

    def test_easy(self) -> None:
        """
        So easy `str.title()` could do it.
        """
        # 1990
        titles = (
            ('blind fury', 'Blind Fury'),
            ('die hard 2', 'Die Hard 2'),
            ('ghost', 'Ghost'),
            ('home alone', 'Home Alone'),
            ('house party', 'House Party'),
            ('kindergarten cop', 'Kindergarten Cop'),
            ('stella', 'Stella'),
            ('tremors', 'Tremors'),
        )
        self.compare(titles)

    def test_exceptions(self) -> None:
        """
        Excepted words should be lower case, unless they're the first or last words.
        """
        # 1991
        titles = (
            ('the adams family', 'The Adams Family'),
            ('beauty and the beast', 'Beauty and the Beast'),
            ('flight of the intruder', 'Flight of the Intruder'),
            ('guilty by suspicion', 'Guilty by Suspicion'),
            ('out for justice', 'Out for Justice'),
            ('nothing but trouble', 'Nothing but Trouble'),
            ('the silence of the lambs', 'The Silence of the Lambs'),
            ('scenes from a mall', 'Scenes from a Mall'),
            ('sleeping with the enemy', 'Sleeping with the Enemy'),
            ('talent for the game', 'Talent for the Game'),
            ('at play in the fields of the lord', 'At Play in the Fields of the Lord'),
        )
        self.compare(titles)

    def test_odd_input(self) -> None:
        titles = (
            ('beauty and the beast', 'Beauty and the Beast'),
            ('Beauty And The Beast', 'Beauty and the Beast'),
            ('BEAUTY AND THE BEAST', 'Beauty and the Beast'),
        )
        self.compare(titles)

    def test_hyphenated(self) -> None:
        """
        Both parts of a hyphenated word should be capitalised
        """
        self.assertEqual(
            capitalise_title('the alaska-siberian expedition'),
            'The Alaska-Siberian Expedition')

    def compare(self, pairs: Tuple[Tuple[str, str], ...]) -> None:
        for title, expected in pairs:
            self.assertEqual(capitalise_title(title), expected)


class CleanPhoneTest(TestCase):
    def test_mobile(self) -> None:
        self._check(
            ('021555123', '021 555 123'),
            ('025 555123', '025 555 123'),
            ('0225 55 1234', '022 555 1234'),
            ('0225-55-1234', '022 555 1234'),
            ('0275551234', '027 555 1234'),
        )

    def test_local(self) -> None:
        self._check(
            ('1234567', '123 4567'),
            ('1234 567', '123 4567'),
            ('1 234 567', '123 4567'),
        )

    def test_national(self) -> None:
        self._check(
            ('091234567', '09 123 4567'),
            ('031234 567', '03 123 4567'),
            ('04 1 234 567', '04 123 4567'),
        )

    def test_tollfree_and_premium(self) -> None:
        self._check(
            ('0800 637 742', '0800 637 742'),
            ('0800637742', '0800 637 742'),
            ('0800MESSIAH', '0800 MESSIAH'),
            ('0508 637 742', '0508 637 742'),
            ('0900 DIKDIK', '0900 DIKDIK'),
        )

    def _check(self, *numbers: Tuple[str, str]) -> None:
        for source, expected in numbers:
            self.assertEqual(phone_add_separators(source), expected)


class CurrencyTest(TestCase):
    def test_currency(self) -> None:
        self.assertEqual(currency(10, currency='NZD'), 'NZD $10.00')

    def test_decimal(self) -> None:
        """
        Decimal values should be handled properly.
        """
        price = decimal.Decimal('54500')
        self.assertEqual(currency(price), '$54,500.00')

    def test_negative(self) -> None:
        self.assertEqual(currency(-19), "-$19.00")

    def test_simple(self) -> None:
        self.assertEqual(currency(19), "$19.00")
        self.assertEqual(currency(19.5), "$19.50")
        self.assertEqual(currency(19.95), "$19.95")

    def test_symbol(self) -> None:
        self.assertEqual(currency(10, symbol=''), '10.00')
        self.assertEqual(currency(10, symbol='€'), '€10.00')
        self.assertEqual(currency(10, symbol='¤'), '¤10.00')

    def test_round_to_cents(self) -> None:
        self.assertEqual(currency(19.99), "$19.99")
        self.assertEqual(currency(19.994), "$19.99")

        self.assertEqual(currency(19.995), "$20.00")
        self.assertEqual(currency(20), "$20.00")
        self.assertEqual(currency(20.004), "$20.00")
        self.assertEqual(currency(20.005), "$20.00")

        self.assertEqual(currency(20.006), "$20.01")
        self.assertEqual(currency(20.014), "$20.01")

    def test_rounded_to_dollar(self) -> None:
        self.assertEqual(currency(19.49, rounded=True), "$19")
        self.assertEqual(currency(19.50, rounded=True), "$20")
        self.assertEqual(currency(19.99, rounded=True), "$20")

    def test_invalid(self) -> None:
        with self.assertRaises(TypeError):
            currency('sausage')                             # type: ignore[arg-type]
        with self.assertRaises(TypeError):
            currency(None)                                  # type: ignore[arg-type]
        with self.assertRaises(TypeError):
            currency({})                                    # type: ignore[arg-type]

    def test_boolean_suprise(self) -> None:
        """
        Recall that booleans are a sub-class of int.
        """
        self.assertEqual(currency(False), '$0.00')
        self.assertEqual(currency(True), '$1.00')


class CurrencyBigTest(TestCase):
    def test_default_arguments(self) -> None:
        """
        Run `currency_big()` with no arguments.
        """
        def check(value: int, expected: str) -> None:
            self.assertEqual(currency_big(value), expected)

        check(0, '$0')
        check(200, '$200')
        check(40000, '$40k')
        check(8000000, '$8.0M')
        check(1600000000, '$1.6B')
        check(3200000000000, '$3.2T')
        check(640000000000000, '$640T')
        check(12800000000000000, '$13,000T')

    def test_currency_big_suffix(self) -> None:
        """
        Run `currency_big()` with custom currency.
        """
        def check(value: int, expected: str) -> None:
            self.assertEqual(currency_big(value, currency='NZD'), expected)

        check(0, '$0 NZD')
        check(200, '$200 NZD')
        check(40000, '$40k NZD')
        check(8000000, '$8.0M NZD')
        check(1600000000, '$1.6B NZD')
        check(3200000000000, '$3.2T NZD')
        check(640000000000000, '$640T NZD')
        check(12800000000000000, '$13,000T NZD')


class FileSizeTest(TestCase):
    def test_decimal(self) -> None:
        """
        Decimal values should be handled properly.
        """
        size = decimal.Decimal('54100')
        self.assertEqual(file_size(size), '54kB')           # type: ignore[arg-type]

    def test_invalid(self) -> None:
        with self.assertRaises(ValueError):
            file_size(-245)
        with self.assertRaises(ValueError):
            file_size('banana')                             # type: ignore[arg-type]

    def test_iso(self) -> None:
        data = (
            (0, '0B'),
            (1, '1B'),
            (21, '21B'),
            (321, '321B'),
            (4321, '4.3kB'),
            (54321, '54kB'),
            (654321, '650kB'),
            (7654321, '7.7MB'),
            (87654321, '88MB'),
            (987654321, '990MB'),
            (1987654321, '2.0GB'),
            (21987654321, '22GB'),
            (321987654321, '320GB'),
            (4321987654321, '4.3TB'),
            (54321987654321, '54TB'),
            (654321987654321, '650TB'),
            (7654321987654321, '7.7PB'),
            (87654321987654321, '88PB'),
            (987654321987654321, '990PB'),
            (1987654321987654321, '2.0EB'),
            (12987654321987654321, '13EB'),
            (123987654321987654321, '120EB'),
            (1234987654321987654321, '1.2ZB'),
            (12345987654321987654321, '12ZB'),
            (123456987654321987654321, '120ZB'),
            (1234567987654321987654321, '1.2YB'),
            (12345678987654321987654321, '12YB'),
            (123456789876543219876543210, '120YB'),
            (1234567898765432198765432100, '1.2RB'),
            (12345678987654321987654321000, '12RB'),
            (123456789876543219876543210000, '120RB'),
            (1234567898765432198765432100000, '1.2QB'),
            (12345678987654321987654321000000, '12QB'),
            (123456789876543219876543210000000, '120QB'),
            (1234567898765432198765432100000000, '1,235QB'),
        )
        for size, expected in data:
            self.assertEqual(file_size(size), expected)

    def test_traditional(self) -> None:
        data = (
            (0, '0B'),
            (1, '1B'),
            (21, '21B'),
            (321, '321B'),
            (4321, '4.2kiB'),
            (54321, '53kiB'),
            (654321, '640kiB'),
            (7654321, '7.3MiB'),
            (87654321, '84MiB'),
            (987654321, '940MiB'),
            (1987654321, '1.9GiB'),
            (21987654321, '20GiB'),
            (321987654321, '300GiB'),
            (4321987654321, '3.9TiB'),
            (54321987654321, '49TiB'),
            (654321987654321, '600TiB'),
            (7654321987654321, '6.8PiB'),
            (87654321987654321, '78PiB'),
            (987654321987654321, '880PiB'),
            (1987654321987654321, '1.7EiB'),
            (12987654321987654321, '11EiB'),
            (123987654321987654321, '110EiB'),
            (1234987654321987654321, '1.0ZiB'),
            (12345987654321987654321, '10ZiB'),
            (123456987654321987654321, '100ZiB'),
            (1234567987654321987654321, '1.0YiB'),
            (12345678987654321987654321, '10YiB'),
            (123456789876543219876543210, '100YiB'),
            (1234567898765432198765432100, '1,000YiB'),
            (12345678987654321987654321000, '10RiB'),
            (123456789876543219876543210000, '100RiB'),
            (1234567898765432198765432100000, '1,000RiB'),
            (12345678987654321987654321000000, '9.7QiB'),
            (123456789876543219876543210000000, '97QiB'),
            (1234567898765432198765432100000000, '970QiB'),
            (12345678987654321987654321000000000, '9,739QiB'),
        )
        for size, expected in data:
            self.assertEqual(file_size(size, traditional=True), expected)


class FindSinglesTest(TestCase):
    def test_find_singles(self) -> None:
        strings = ['a', 'b', 'b', 'c', 'd', 'e', 'a', 'a']
        self.assertEqual(find_singles(strings), set(['c', 'd', 'e']))
        self.assertEqual(set(strings), set(['a', 'b', 'c', 'd', 'e']))


class ForceAsciiTest(TestCase):
    def test_input_types(self) -> None:
        """
        Allow different input types.
        """
        self.assertEqual(force_ascii('beach'), 'beach')
        self.assertEqual(force_ascii('beach'), 'beach')
        self.assertEqual(force_ascii(42), '42')             # type: ignore[arg-type]

    def test_remove_accents(self) -> None:
        """
        Remove accent, but preserve accented letter.
        """
        self.assertEqual(force_ascii('Café'), 'Cafe')
        self.assertEqual(force_ascii('naïve'), 'naive')
        self.assertEqual(force_ascii('Über'), 'Uber')

    def test_accents_and_quotes(self) -> None:
        received = '«Él me dijo, “Estoy muy próspero”.»'
        expected = '"El me dijo, "Estoy muy prospero"."'
        self.assertEqual(force_ascii(received), expected)

    def test_break_ligatures(self) -> None:
        received = '\ufb02an'
        expected = 'flan'
        self.assertEqual(force_ascii(received), expected)


class FractionTest(TestCase):
    def test_best_match(self) -> None:
        self.assertEqual(Fraction.best_match(0.0), (0.0, ''))
        self.assertEqual(Fraction.best_match(0.1), (0.0, ''))
        self.assertEqual(Fraction.best_match(0.2), (0.25, '¼'))
        self.assertEqual(Fraction.best_match(0.3), (0.25, '¼'))
        self.assertEqual(Fraction.best_match(0.4), (0.5, '½'))
        self.assertEqual(Fraction.best_match(0.5), (0.5, '½'))
        self.assertEqual(Fraction.best_match(0.6), (0.5, '½'))
        self.assertEqual(Fraction.best_match(0.7), (0.75, '¾'))
        self.assertEqual(Fraction.best_match(0.8), (0.75, '¾'))
        self.assertEqual(Fraction.best_match(0.9), (1.0, None))
        self.assertEqual(Fraction.best_match(1.0), (1.0, None))

    def test_best_match_value_error(self) -> None:
        message = r'Fraction should be in range \[0.0, 1.0\]'
        with self.assertRaisesRegex(ValueError, message):
            Fraction.best_match(2.5)

    def test_entity(self) -> None:
        self.assertEqual(Fraction.entity(0.0), '0')             # 0
        self.assertEqual(Fraction.entity(0.5), '&#xbd;')        # ½
        self.assertEqual(Fraction.entity(2.2), '2&#xbc;')       # 2¼
        self.assertEqual(Fraction.entity(2.5), '2&#xbd;')       # 2½
        self.assertEqual(Fraction.entity(2.8), '2&#xbe;')       # 2¾
        self.assertEqual(Fraction.entity(2.9), '3')             # Rounded up to 3

    def test_unicode(self) -> None:
        self.assertEqual(Fraction.unicode(0.0), '0')            # 0
        self.assertEqual(Fraction.unicode(0.2), '¼')            # ¼
        self.assertEqual(Fraction.unicode(0.8), '¾')            # ¾
        self.assertEqual(Fraction.unicode(2.2), '2¼')           # 2¼
        self.assertEqual(Fraction.unicode(2.5), '2½')           # 2½
        self.assertEqual(Fraction.unicode(2.8), '2¾')           # 2¾
        self.assertEqual(Fraction.unicode(2.9), '3')            # Rounded up to 3


class HtmlAttributesTest(TestCase):
    def test_img(self) -> None:
        mapping = {
            'width': '640px',
            'height': '480px',
            'src': '/s/common/images/animal-skeleton.png',
        }
        expected = 'height="480px" src="/s/common/images/animal-skeleton.png" width="640px"'
        self.assertEqual(html_attributes(mapping), expected)

    def test_inline_js(self) -> None:
        mapping = {
            'onclick': "alert(Date());",
            'style': 'display: inline-block; padding: 15px;'
        }
        expected = 'onclick="alert(Date());" style="display: inline-block; padding: 15px;"'
        self.assertEqual(html_attributes(mapping), expected)

    def test_booleans(self) -> None:
        # Don't show false values
        mapping = {
            'hidden': False,
            'readonly': False,
        }
        self.assertEqual(html_attributes(mapping), '')

        # HTML5 style for booleans
        mapping['hidden'] = True
        self.assertEqual(html_attributes(mapping), 'hidden')

        mapping['readonly'] = True
        self.assertEqual(html_attributes(mapping), 'hidden readonly')

    def test_escape(self) -> None:
        mapping: Mapping[str, Union[bool, str]] = {
            'bad<key': True,
            'message': "<strong>Hello World</strong>",
        }
        expected = 'bad&lt;key message="&lt;strong&gt;Hello World&lt;/strong&gt;"'
        self.assertEqual(html_attributes(mapping), expected)

    def test_not_ordered(self) -> None:
        # Dictionary order is preserved in Python 3.7+
        mapping = {
            'width': '640px',
            'height': '480px',
            'src': '/s/common/images/animal-skeleton.png',
        }
        expected = 'width="640px" height="480px" src="/s/common/images/animal-skeleton.png"'
        self.assertEqual(html_attributes(mapping, sort_keys=False), expected)


class JoinAndTest(TestCase):
    def test_empty(self) -> None:
        parts: List[str] = []
        self.assertEqual(join_and(parts), '')

    def test_one_part(self) -> None:
        parts = ['Me']
        self.assertEqual(join_and(parts), 'Me')

    def test_two_parts(self) -> None:
        parts = ['Me', 'myself']
        self.assertEqual(join_and(parts), 'Me and myself')

    def test_three_parts(self) -> None:
        parts = ['Me', 'myself', 'I']
        self.assertEqual(join_and(parts), 'Me, myself, and I')

    def test_three_parts_sloppy(self) -> None:
        parts = ['Me', 'myself', 'I']
        self.assertEqual(join_and(parts, oxford_comma=False), 'Me, myself and I')


class JSONEncoderForHTMLTest(TestCase):
    """
    Tests for the JSONEncoderForHTML from simplejson 2.1
    """
    def setUp(self) -> None:
        self.decoder = json.JSONDecoder()
        self.encoder = JSONEncoderForHTML()

    def test_basic_encode(self) -> None:
        self.assertEqual(self.encoder.encode('&'), str('"\\u0026"'))
        self.assertEqual(self.encoder.encode('<'), str('"\\u003c"'))
        self.assertEqual(self.encoder.encode('>'), str('"\\u003e"'))

    def test_basic_roundtrip(self) -> None:
        for char in '&<>':
            self.assertEqual(
                char, self.decoder.decode(
                    self.encoder.encode(char)))

    def test_ensure_ascii(self) -> None:
        s = '«Él me dijo, “Estoy muy próspero”.»'

        encoder = JSONEncoderForHTML(ensure_ascii=True)
        self.assertEqual(
            encoder.encode(s),
            str('"\\u00ab\\u00c9l me dijo, \\u201cEstoy muy pr\\u00f3spero\\u201d.\\u00bb"')
        )

        encoder = JSONEncoderForHTML(ensure_ascii=False)
        self.assertEqual(
            encoder.encode(s),
            '"{}"'.format(s))

    def test_prevent_script_breakout(self) -> None:
        bad_string = '</script><script>alert("gotcha")</script>'
        self.assertEqual(
            self.encoder.encode(bad_string),
            str('"\\u003c/script\\u003e\\u003cscript\\u003e'
                'alert(\\"gotcha\\")\\u003c/script\\u003e"'))
        self.assertEqual(
            bad_string,
            self.decoder.decode(self.encoder.encode(bad_string)))


class LineRandomTest(TestCase):
    def test_line_random(self) -> None:
        path = DATA_FOLDER / 'haiku.txt'
        message = "line_random() moved to files module"
        with assert_deprecated(message):
            line_random(path)


class LinesTest(TestCase):
    def test_lines_easy(self) -> None:
        string = """
            the first cold shower

            even the monkey seems to want

            a little coat of straw
        """
        self.assertEqual(
            lines(string),
            ['the first cold shower',
             'even the monkey seems to want',
             'a little coat of straw'])


class MakeSlugTest(TestCase):
    def test_entities(self) -> None:
        self.assertEqual(
            make_slug('O&rsquo;Reilly'), 'oreilly')
        self.assertEqual(
            make_slug('Crosby, Stills, Nash &amp; Young'), 'crosby-stills-nash-young')

    def test_max_length(self) -> None:
        silly = "This is the song that doesn't end" * 10

        # Limit defaults to 50 (same as Django's `models.SlugField`)
        self.assertEqual(len(make_slug(silly)), 50)

        # Tweak limit
        self.assertEqual(len(make_slug(silly, max_length=128)), 128)

        # Remove limit
        self.assertEqual(len(make_slug(silly, max_length=None)), 320)


class MakeSlugsTest(TestCase):
    def test_make_slugs(self) -> None:
        header = (
            'Thickness (mm)',
            'Colour',
            'Finish',
            'Has Grain',
            'Allow Partial',
            'Percentage Wastage (%)',
            'Board Length (mm)',
            'Board Width (mm)',
            'Wholesale Price ($)',
            'Retail Price ($)',
            'Default',
        )
        slugs = make_slugs(header)
        expected = [
            'thickness_mm',
            'colour',
            'finish',
            'has_grain',
            'allow_partial',
            'percentage_wastage',
            'board_length_mm',
            'board_width_mm',
            'wholesale_price',
            'retail_price',
            'default',
        ]
        self.assertEqual(slugs, expected)

    def test_make_slugs_blank(self) -> None:
        header = (
            'Thickness (mm)',
            '',
            'Finish',
            '',
            '',
        )
        slugs = make_slugs(header)
        self.assertEqual(slugs, ['thickness_mm', '_', 'finish', '_2', '_3'])

    def test_make_slugs_keywords(self) -> None:
        header = [
            'assert',
            'lambda',
            'return',
            'assert',
        ]
        self.assertEqual(
            make_slugs(header),
            ['assert_', 'lambda_', 'return_', 'assert_2'],
        )

    def test_make_slugs_unique(self) -> None:
        header = (
            'Thickness (mm)',
            'Colour',
            'Finish',
            'Colour',
            'Colour',
        )

        self.assertEqual(
            make_slugs(header),
            ['thickness_mm', 'colour', 'finish', 'colour2', 'colour3'],
        )

    def test_make_slugs_not_unique(self) -> None:
        header = (
            'Thickness (mm)',
            'Colour',
            'Finish',
            'Colour',
            'Colour',
        )
        self.assertEqual(
            make_slugs(header, unique=False),
            ['thickness_mm', 'colour', 'finish', 'colour', 'colour'],
        )


class MultiReplaceTest(TestCase):
    def test_words(self) -> None:
        s = 'The quick brown fox jumped over the lazy dog.'
        mapping = {
            'brown': 'green',
            'dog': 'snack',
            'fox': 'pickles',
            'jumped': 'were placed',
            'lazy': 'quick',
            'over': 'on',
            'quick': 'lazy',
            'The': 'Some',
        }
        multi = MultiReplace(mapping)
        self.assertEqual(
            multi.replace(s),
            'Some lazy green pickles were placed on the quick snack.')


class ParagraphsSplitTest(TestCase):
    def test_paragraphs(self) -> None:
        text = textwrap.dedent("""
            Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do
            tempor incididunt ut labore et dolore magna aliqua. Faucibus turpis
            bibendum neque egestas congue.

            Cursus risus at ultrices mi tempus imperdiet nulla. Velit ut tortor
            viverra suspendisse. At tellus at urna condimentum mattis.

            Aliquam amet luctus. Semper auctor neque vitae tempus quam.
        """).strip()
        parts = paragraphs_split(text)
        self._test_paragraphs(parts)

    def test_too_many_newlines(self) -> None:
        text = textwrap.dedent("""
            Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do
            tempor incididunt ut labore et dolore magna aliqua. Faucibus turpis
            bibendum neque egestas congue.


            Cursus risus at ultrices mi tempus imperdiet nulla. Velit ut tortor
            viverra suspendisse. At tellus at urna condimentum mattis.



            Aliquam amet luctus. Semper auctor neque vitae tempus quam.
        """).strip()
        parts = paragraphs_split(text)
        self._test_paragraphs(parts)

    def _test_paragraphs(self, parts: List[str]) -> None:
        self.assertEqual(len(parts), 3)
        paragraph_1 = parts[0]
        self.assertTrue(paragraph_1.startswith('Lorem ipsum'))
        paragraph_2 = parts[1]
        self.assertTrue(paragraph_2.startswith('Cursus risus'))
        paragraph_3 = parts[2]
        self.assertTrue(paragraph_3.startswith('Aliquam amet'))


class ParagraphsWrapTest(TestCase):
    def test_paragraphs_wrap(self) -> None:
        text = textwrap.dedent("""
            Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do
            tempor incididunt ut labore et dolore magna aliqua. Faucibus turpis
            bibendum neque egestas congue.

            Cursus risus at ultrices mi tempus imperdiet nulla. Velit ut tortor
            viverra suspendisse. At tellus at urna condimentum mattis.

            Aliquam amet luctus. Semper auctor neque vitae tempus quam.
        """).strip()

        wrapped = paragraphs_wrap(text, width=60)
        expected = textwrap.dedent("""
            Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed
            do tempor incididunt ut labore et dolore magna aliqua.
            Faucibus turpis bibendum neque egestas congue.

            Cursus risus at ultrices mi tempus imperdiet nulla. Velit ut
            tortor viverra suspendisse. At tellus at urna condimentum
            mattis.

            Aliquam amet luctus. Semper auctor neque vitae tempus quam.
        """).strip()
        self.assertEqual(wrapped, expected)


class PhoneNormaliseTest(TestCase):
    def test_use_hyphen_separators(self) -> None:
        self.assertEqual(phone_normalise('+64 21 555 600'), '+64-21-555-600')

    def test_double_zero(self) -> None:
        self.assertEqual(phone_normalise('0064 9 555 1234'), '+64-9-555-1234')

    def test_no_country_code(self) -> None:
        self.assertEqual(phone_normalise('021 555 600'), '+64-21-555-600')


class TestPlainQuotes(TestCase):
    def test_input_types(self) -> None:
        self.assertEqual(plain_quotes('beach'), 'beach')
        self.assertEqual(plain_quotes('beach'), 'beach')
        with self.assertRaises(AttributeError):
            plain_quotes(42)                                # type: ignore[arg-type]

    def test_replace_quotes(self) -> None:
        received = "not only ‘looks and feels’ like the project"
        expected = "not only 'looks and feels' like the project"
        self.assertEqual(plain_quotes(received), expected)

        received = '(“example”) [“tst”] {“tst”}'
        expected = '("example") ["tst"] {"tst"}'
        self.assertEqual(plain_quotes(received), expected)

        received = '”Good morning, Dave,” said HAL.'
        expected = '"Good morning, Dave," said HAL.'
        self.assertEqual(plain_quotes(received), expected)

        received = '“That’s a ‘magic’ sock.”'
        expected = '"That\'s a \'magic\' sock."'
        self.assertEqual(plain_quotes(received), expected)


class ReverseReplaceTest(TestCase):
    def test_not_found(self) -> None:
        twister = "She sells sea-shells by the sea-shore."
        replaced = reverse_replace(twister, 'conch', '')
        self.assertTrue(replaced is twister)

    def test_limit_one(self) -> None:
        twister = "She sells sea-shells by the sea-shore."
        replaced = reverse_replace(twister, 'sea', 'SEA', limit=1)
        expected = "She sells sea-shells by the SEA-shore."
        self.assertEqual(replaced, expected)

    def test_no_limit(self) -> None:
        twister = "She sells sea-shells by the sea-shore."
        replaced = reverse_replace(twister, 'sea', 'SEA')
        expected = "She sells SEA-shells by the SEA-shore."
        self.assertEqual(replaced, expected)


class ShortenTest(TestCase):
    # Exactly 60-characters long
    string = "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed"

    def test_short_strings_unchanged(self) -> None:
        """
        An input equal or less than maxlen should be left alone.
        """
        self.assertTrue(shorten(self.string, 60) is self.string)

    def test_shortened_maxlen(self) -> None:
        """
        Try various values of `maxlen`.

        Note also that punctuation is stripped before suffix attached.
        """
        short = shorten(self.string, 59)
        self.assertLessEqual(len(short), 60)
        self.assertEqual(
            short,
            'Lorem ipsum dolor sit amet, consectetur adipiscing elit...')

    def test_no_suffix(self) -> None:
        short = shorten(self.string, 28, suffix='')
        self.assertEqual(len(short), 26)
        self.assertEqual(short, "Lorem ipsum dolor sit amet")


class TestSentences(TestCase):
    def test_single(self) -> None:
        received = "This is a short text."
        expected = received
        self.assertEqual(sentences(received), expected)

    def test_single_no_delimeter(self) -> None:
        received = "This is a short text"
        expected = received
        self.assertEqual(sentences(received), expected)

    def test_multiple(self) -> None:
        received = (
            "This is a short text. "
            "It is to be used for testing only!!! "
            "Don't doubt me...  "
            "Or else!"
        )
        expected = (
            "This is a short text. "
            "It is to be used for testing only!!!"
        )
        self.assertEqual(sentences(received, 2), expected)


class SplitNameTest(TestCase):
    def test_empty(self) -> None:
        first, last = split_name('')
        self.assertEqual(first, '')
        self.assertEqual(last, '')

    def test_basic(self) -> None:
        first, last = split_name('John Smith')
        self.assertEqual(first, 'John')
        self.assertEqual(last, 'Smith')

    def test_excessive_whitespace(self) -> None:
        first, last = split_name('  John    Smith  ')
        self.assertEqual(first, 'John')
        self.assertEqual(last, 'Smith')

    def test_no_last_name(self) -> None:
        first, last = split_name('John')
        self.assertEqual(first, 'John')
        self.assertEqual(last, '')

    def test_hyphenated(self) -> None:
        first, last = split_name('Helena Bonham-Carter')
        self.assertEqual(first, 'Helena')
        self.assertEqual(last, 'Bonham-Carter')

    def test_triple_barrel(self) -> None:
        first, last = split_name('Sacha Baron Cohen')
        self.assertEqual(first, 'Sacha')
        self.assertEqual(last, 'Baron Cohen')


class SplitSentencesTest(TestCase):
    def test_empty(self) -> None:
        self.assertEqual(split_sentences(''), [])

    def test_no_delimiter(self) -> None:
        string = "This is a sentence without an ending"
        expected = ['This is a sentence without an ending']
        self.assertEqual(split_sentences(string), expected)

    def test_single(self) -> None:
        string = "This is a sentence with an ending."
        expected = ['This is a sentence with an ending.']
        self.assertEqual(split_sentences(string), expected)

    def test_multiple(self) -> None:
        string = (
            "This is a short text. "
            "It is to be used for testing only!!! "
            "Don't doubt me...  "
            "Or else!"
        )
        expected = [
            "This is a short text.",
            "It is to be used for testing only!!!",
            "Don't doubt me...",
            "Or else!",
        ]
        self.assertEqual(split_sentences(string), expected)

    def test_decimal(self) -> None:
        string = (
            "What's new in Python 3.13?"
        )
        expected = ["What's new in Python 3.13?"]
        self.assertEqual(split_sentences(string), expected)


class StripBlankTest(TestCase):
    def test_strip_blank(self) -> None:
        string = multiline("""
            abc

                def

            ghi
        """)
        stripped = strip_blank(string)
        expected = (
            "abc\n"
            "    def\n"
            "ghi")
        self.assertEqual(stripped, expected)


class TestStripTags(TestCase):
    def test_basic(self) -> None:
        received = '<p>Never trust user input</p>'
        expected = 'Never trust user input'
        self.assertEqual(strip_tags(received), expected)


class TrademeEmphasisTest(TestCase):
    maxDiff = None

    def test_no_emphasis(self) -> None:
        string = multiline("""
            The human eye is very receptive to differences in "brightness
            within a text body." Therefore, one can differentiate between
            types of emphasis according to whether the emphasis changes
            the "blackness" of text, sometimes referred to as
            typographic color.
        """)
        self.assertEqual(trademe_emphasis(string), string)

    def test_bold(self) -> None:
        self.assertEqual(trademe_emphasis("apple"), "apple")
        self.assertEqual(trademe_emphasis("**banana**"), "<strong>banana</strong>")
        self.assertEqual(trademe_emphasis("**carrot **"), "**carrot **")
        self.assertEqual(trademe_emphasis("** durian**"), "** durian**")
        self.assertEqual(trademe_emphasis("**e**"), "<strong>e</strong>")

    def test_bold_and_italic(self) -> None:
        self.assertEqual(trademe_emphasis("apple"), "apple")
        self.assertEqual(trademe_emphasis("***banana***"), "<strong><em>banana</em></strong>")
        self.assertEqual(trademe_emphasis("***carrot ***"), "***carrot ***")
        self.assertEqual(trademe_emphasis("*** durian***"), "*** durian***")
        self.assertEqual(trademe_emphasis("***e***"), "<strong><em>e</em></strong>")

    def test_italic(self) -> None:
        self.assertEqual(trademe_emphasis("apple"), "apple")
        self.assertEqual(trademe_emphasis("*banana*"), "<em>banana</em>")
        self.assertEqual(trademe_emphasis("*carrot *"), "*carrot *")
        self.assertEqual(trademe_emphasis("* durian*"), "* durian*")
        self.assertEqual(trademe_emphasis("*e*"), "<em>e</em>")

    def test_multiline_italic(self) -> None:
        string = multiline("""
            The human eye is very receptive to differences in *brightness
            within a text body*. Therefore, one can differentiate ***between
            types*** of emphasis according to whether the emphasis changes
            the **blackness** of text, sometimes referred to as
            typographic color.
        """)
        expected = multiline("""
            The human eye is very receptive to differences in <em>brightness
            within a text body</em>. Therefore, one can differentiate <strong><em>between
            types</em></strong> of emphasis according to whether the emphasis changes
            the <strong>blackness</strong> of text, sometimes referred to as
            typographic color.
        """)
        self.assertEqual(trademe_emphasis(string), expected)


class TestUniqueSuffix(TestCase):
    def test_no_conflict(self) -> None:
        self.assertEqual(_unique_suffix('banana', []), 'banana')

    def test_double(self) -> None:
        self.assertEqual(_unique_suffix('carrot', ['carrot']), 'carrot2')

    def test_triple(self) -> None:
        conflicts = ['pumpkin', 'pumpkin2']
        self.assertEqual(_unique_suffix('pumpkin', conflicts), 'pumpkin3')

    def test_many(self) -> None:
        conflicts = ['apple', 'apple2', 'apple3', 'apple4', 'apple5', 'apple6']
        unique = _unique_suffix('apple', conflicts)
        self.assertEqual(unique, 'apple7')

    def test_not_contiguous(self) -> None:
        """
        Gaps in the slug sequence.
        """
        conflicts = ['apple4', 'apple7', 'apple11', 'apple23', 'apple35', 'apple41']

        # Clash
        self.assertEqual(_unique_suffix('apple7', conflicts), 'apple42')

        # No clash
        self.assertEqual(_unique_suffix('apple', conflicts), 'apple42')
        self.assertEqual(_unique_suffix('apple8', conflicts), 'apple42')

    def test_shared_prefixes_simple(self) -> None:
        conflicts = ['blue', 'blueberry']
        unique = _unique_suffix('blue', conflicts)
        self.assertEqual(unique, 'blue2')

    def test_shared_prefixes_complex(self) -> None:
        conflicts = ['pea3', 'pea12', 'peanut2', 'peanut4', 'peanut15', 'pea13', 'pea42']

        # Clash
        self.assertEqual(_unique_suffix('pea2', conflicts), 'pea43')
        self.assertEqual(_unique_suffix('peanut2', conflicts), 'peanut16')

        # No clash
        self.assertEqual(_unique_suffix('pea', conflicts), 'pea43')
        self.assertEqual(_unique_suffix('peanut', conflicts), 'peanut16')
        self.assertEqual(_unique_suffix('pea30', conflicts), 'pea43')
        self.assertEqual(_unique_suffix('peanut6', conflicts), 'peanut16')
