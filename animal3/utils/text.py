
import collections
import decimal
from itertools import zip_longest
import json
import keyword
from pathlib import Path
import re
from string import punctuation, whitespace
import textwrap
from typing import (
    Any, Dict, Generator, Iterable, List,
    Mapping, Match, Optional, Sequence, Set, Tuple, Union,
)
import unicodedata

from django.utils.encoding import force_str
from django.utils.html import conditional_escape, format_html
from django.utils.safestring import mark_safe, SafeText
from django.utils.text import slugify

from .math import round_significant


Numeric = Union[decimal.Decimal, float]


class MultiReplace:
    """
    Perform multiple text search and replace operations in a single pass.
    """
    def __init__(self, mapping: Dict[str, str]):
        self.mapping = mapping

        # Longest key first!
        keys = sorted(self.mapping.keys(), reverse=True)
        pattern = '|'.join(r'\b' + re.escape(key) + r'\b' for key in keys)
        self.pattern = re.compile(pattern)

    def replace(self, given: str) -> str:
        def r(match: Match[str]) -> str:
            key = match.group(0)
            return self.mapping.get(key, key)
        return self.pattern.sub(r, given)


def camelcase_to_underscore(name: str, avoid_keywords: bool = False) -> str:
    """
    Convert a CamelCase name to an underscore_name.

        >>> camelcase_to_underscore("JavaIsTooVerbose")
        'java_is_too_verbose'

    Args:
        name
            CamelCase name to change
        avoid_keywords
            Append an underscore if a name clashes with a Python keywords.

    Returns:
        Underscore-style idenitifier
    """
    # Convert camelcase into underscore style
    name = name.strip()
    name = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', name)
    name = name.lower()
    name = re.sub(r'\s+', '_', name)

    # Remove leading numbers, non alphanumeric characters.
    name = re.sub(r'^[0-9]+', '_', name)
    name = re.sub(r'[^a-z0-9]', '_', name)

    # Remove excess underscores
    name = re.sub(r'_+', '_', name)
    name = name.strip('_')

    # Python keyword?
    if avoid_keywords and keyword.iskeyword(name):
        name += '_'

    return name


def capitalise_title(title: str) -> str:
    """
    Capitalise given title.

    Performs better than Python's `str.title()`, but does not attempt to
    properly identify parts-of-speech, etc...

        >>> capitalise_title("taming of the shrew")
        'Taming of the Shrew'

    Args:
        title:
            Title to capitalise.

    Returns:
        Capitalised title string
    """
    # Empty?
    title = title.strip()
    if not title:
        return ''

    # Break title into words
    words = title.lower().split()

    # Capitalise (almost) all words
    exceptions = {
        'a', 'an', 'and', 'but', 'by', 'for', 'from', 'in', 'of', 'the', 'with',
    }
    capitalised = []
    for word in words:
        # Skip exceptions
        if word not in exceptions:
            word = word.title()
        capitalised.append(word)

    # Always capitalise the first and last words
    capitalised[0] = capitalised[0].title()
    capitalised[-1] = capitalised[-1].title()
    return ' '.join(capitalised)


def currency(
    amount: Numeric,
    *,
    symbol: str = '$',
    currency: Optional[str] = None,
    rounded: bool = False,
) -> str:
    """
    Format currency value.

    Rounds (not truncates) to two decimal points and adds commas and a
    prefix.

        >>> currency(19.95)
        '$19.95'
        >>> currency(35, symbol='€', currency='EURO')
        'EURO €35.00'

    Negative values are represented by a hyphen before the symbol.

    Args:
        value:
            Amount of money.
        symbol:
            Replace default currency symbol '$' with some other string.
        currency:
            Currency suffix to add to value, eg. 'NZD'
        rounded:
            Set to True to round value to nearest integer, no cents shown.

    Returns:
        Short currency string
    """
    # Round amount to two decimal places, allow decimal input.
    try:
        amount = decimal.Decimal(amount)
    except (TypeError, decimal.InvalidOperation):
        raise TypeError("Could not format '{}' to currency".format(amount))

    # Negative number?
    if amount < 0:
        amount = abs(amount)
        symbol = '-' + symbol

    # Round to nearest integer?
    if rounded:
        amount = amount.quantize(decimal.Decimal('1'), rounding=decimal.ROUND_HALF_UP)
        dollars = "{:,}".format(int(amount))
        return f"{symbol}{dollars}"
    else:
        amount = amount.quantize(decimal.Decimal('0.01'), rounding=decimal.ROUND_HALF_UP)

        # Add commas and other decorations
        dollars = "{:,}".format(int(amount))
        cents = "{:.2f}".format(amount)[-3:]

        if currency is None:
            return f"{symbol}{dollars}{cents}"
        else:
            return f"{currency} {symbol}{dollars}{cents}"


def currency_big(
    amount: Numeric,
    *,
    symbol: str = '$',
    currency: Optional[str] = None
) -> str:
    """
    Format large amounts of money.

    For example:

        >>> currency_big(40e3)
        '$40k'
        >>> currency_big(12e6, currency='NZD')
        '$12M NZD'

    Args:
        value:
            Amount of money.
        symbol:
            Replace default currency symbol '$' with some other string.
        currency:
            Currency suffix to add to value.

    Returns:
        Short currency string

    """
    def formatted(amount: Numeric, suffix: str) -> str:
        value = round_significant(float(amount), 2)
        value = int(value) if value >= 10 else value
        suffix = suffix if currency is None else f"{suffix} {currency}"
        return f"{symbol}{value:,}{suffix}"

    if not amount:
        return formatted(0, '')

    if amount < 1000:
        return formatted(amount, '')

    suffixes = ['k', 'M', 'B', 'T']
    value = float(amount)
    for suffix in suffixes:
        value /= 1000
        if value < 1000:
            return formatted(value, suffix)

    return formatted(value, suffix)


def duration(seconds: int) -> str:      # pragma: no cover
    raise NameError("Function 'duration()' moved to 'animal3.utils.dates'")


def file_size(size: int, traditional: bool = False) -> str:
    """
    Convert a file size in bytes to a easily human-parseable form, using only
    one or two significant figures.

        >>> file_size(4200)
        '4.2kB'
        >>> file_size(4200, traditional=True)
        '4.1kiB'

    Args:
        size:
            file size in bytes
        traditional:
            Use traditional base-2 units, otherwise default to using
            'proper' SI multiples of 1000.

    Raises:
        ValueError: If given size has an error in its... ah... value.

    Returns:
        Short string, like '4.3kB'
    """
    try:
        size = int(size)
    except (ValueError, TypeError):
        raise ValueError("Given file size '{}' not numeric.".format(size))

    if size < 0:
        raise ValueError("Given file size '{}' not positive".format(size))

    if size < 1000:
        return '{}B'.format(size)

    suffixes = {
        1000: ['kB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB', 'RB', 'QB'],
        1024: ['kiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB', 'RiB', 'QiB']
    }

    multiple = 1024 if traditional else 1000
    divided = float(size)
    for suffix in suffixes[multiple]:
        divided /= multiple
        if divided < multiple:
            divided = round_significant(divided, 2)
            divided = int(divided) if divided >= 10 else divided
            return '{:,}{}'.format(divided, suffix)

    # Greater than 1000 Quettabytes!?
    # https://en.wikipedia.org/wiki/Quetta-
    return '{:,}{}'.format(int(round(divided)), suffix)


def find_singles(strings: Iterable[str]) -> Set[str]:
    """
    Return a set containing the strings from the given iterable occur exactly
    once.

        >>> find_singles(['a', 'a', 'b', 'c', 'c'])
        {'b'}

    This is not the same as a set of unique strings.
    """
    counts = collections.Counter(strings)
    unique = set(x for x, count in counts.items() if count == 1)
    return unique


def force_ascii(given: str) -> str:
    """
    Return ASCII version of given unicode string.

    This is a fairly quick-and-dirty approach, with the advantage that it
    requires no extra modules.

        >>> force_ascii('Café')
        'Cafe'

    See:
        Check out the 'Unidecode' package for a comprehensive solution
        https://pypi.org/project/Unidecode/

    Returns:
        ASCII version of given string.
    """
    plain = force_str(given)
    plain = plain_quotes(plain)
    plain = unicodedata.normalize('NFKD', plain)
    plain = plain.encode('ASCII', 'ignore').decode('ASCII')
    return plain


class Fraction:
    """
    Round a floating point number to the nearest quarter to produce clean string.

    Produces a so-called vulgar fraction - a single unicode character::

        >>> Fraction.unicode(2.5)
        '2½'

    For maximal compatibility, we have limited ourselves to the three fractions
    that have been supported since the ISO-8859-1 days: quarter, half, and
    three-quarters.

    There are more general (and involved) ways to format fractions in unicode;
    you can manually mark characters as superscript and subscript as per
    the article below:

    https://en.wikipedia.org/wiki/Unicode_subscripts_and_superscripts
    """
    fractions: Tuple[Tuple[float, Optional[str]], ...] = (
        (0.00, ''),
        (0.25, '\u00bc'),
        (0.50, '\u00bd'),
        (0.75, '\u00be'),
        (1.00, None),       # Used to indicate carry
    )

    @staticmethod
    def best_match(fraction: float) -> Tuple[float, Optional[str]]:
        """
        Find best matching tuple within `self.fractions`.
        """
        if fraction > 1.0 or fraction < 0.0:
            raise ValueError('Fraction should be in range [0.0, 1.0]')
        match = Fraction.fractions[0]
        match_error = 1.0
        for parts in Fraction.fractions:
            error = abs(fraction - parts[0])
            if error < match_error:
                match = parts
                match_error = error
        return match

    @staticmethod
    def entity(value: float) -> str:
        """
        Build 'vulgar' fraction string using HTML/Unicode entity.

            >>> Fraction.entity(2.5)
            '2&#xbd;'

        Args:
            value (float)

        Returns: str
        """
        integer, partial = Fraction._split(value)
        match = Fraction.best_match(partial)
        fraction = match[1]

        if fraction is None:
            fraction = ''
            integer += 1
        elif fraction:
            fraction = f"&#{hex(ord(fraction))[1:]};"

        if integer > 0:
            return f"{integer}{fraction}"
        elif fraction:
            return fraction
        else:
            return '0'

    @staticmethod
    def unicode(value: float) -> str:
        """
        Build unicode string.

            >>> Fraction.unicode(2.5)
            '2½'

        Args:
            value (float)

        Returns: str
        """
        integer, partial = Fraction._split(value)
        match = Fraction.best_match(partial)
        fraction = match[1]

        # Carry the one?
        if fraction is None:
            fraction = ''
            integer += 1

        if integer > 0:
            return f"{integer}{fraction}"
        elif fraction:
            return fraction
        else:
            return '0'

    @staticmethod
    def _split(value: float) -> Tuple[int, float]:
        """
        Break floating point number in whole number and fractional parts.

        Args:
            value (float)

        Returns: (int, float)
        """
        value = float(value)
        full, fraction = divmod(value, 1)
        full = int(full)
        return (full, fraction)


def html_attributes(
    mapping: Mapping[str, Union[bool, str]],
    sort_keys: bool = True,
) -> SafeText:
    """
    Produce an HTML attribute string from the given dictionary.

    No attempt is made to ensure that attribute names are valid HTML, although
    they are escaped for safety.

        >>> mapping = {'width': '640px', 'height': '480px'}
        >>> html_attributes(mapping)
        'height="480px" width="640px"'

    Args:
        mapping:
            Dictionary with string keys and either string or boolean values.
        sort_keys:
            Sort attribute names into alphabetical order.

    Returns:
        A nicely formatted string.
    """
    attributes: List[SafeText] = []

    names = list(mapping.keys())
    if sort_keys:
        names.sort()

    for name in names:
        value = mapping[name]
        if value is False:
            continue
        elif value is True:
            name_escaped = mark_safe(conditional_escape(name))
            attributes.append(name_escaped)
        else:
            attributes.append(format_html('{:}="{:}"', name, value))
    return SafeText(' '.join(attributes))


def join_and(parts: Iterable[str], *, oxford_comma: bool = True) -> str:
    """
    Join multiple strings together as an human don would.

        >>> join_and(['Mary', 'Suzy', 'Jane'])
        'Mary, Suzy, and Jane'

    Args:
        parts:
            The strings to join together.
        oxford_comma:
            Add a comma before the 'and', which is of course the best way.

    Returns:
        The joined string.
    """
    # Empty
    if not parts:
        return ''

    # Just one
    parts = list(parts)
    last = parts.pop()
    if not parts:
        return last

    # More
    string = ", ".join(parts)
    if oxford_comma and len(parts) >= 2:
        string += ','
    string += f" and {last}"
    return string


class JSONEncoderForHTML(json.JSONEncoder):
    """
    An encoder that produces JSON safe to embed in HTML.

    Copied in from simplejson 2.1.

    TODO: Check to see if this is still needed in Django 3+ and Python 3+
    """
    def encode(self, obj: Any) -> str:
        # Override JSONEncoder.encode because it has hacks for
        # performance that make things more complicated.
        chunks = self.iterencode(obj, True)
        if self.ensure_ascii:
            return ''.join(chunks)
        else:
            return u''.join(chunks)

    def iterencode(
        self,
        obj: Any,
        _one_shot: bool = False,
    ) -> Generator[str, None, None]:
        """
        Override parent class to escape generated JSON.

        Yields: Output JSON, one chunk at a time.
        """
        chunks = super().iterencode(obj, _one_shot)
        for chunk in chunks:
            chunk = chunk.replace('&', '\\u0026')
            chunk = chunk.replace('<', '\\u003c')
            chunk = chunk.replace('>', '\\u003e')
            yield chunk


def line_random(path: Path, encoding: str = 'utf-8') -> str:
    # Deprecated: 2021-01-02 Moved to files module
    import warnings
    warnings.warn("line_random() moved to files module", DeprecationWarning)
    from .files import line_random
    return line_random(path, encoding)


def lines(string: str) -> List[str]:
    """
    Split string into list on newlines, skipping blank lines.

    Differs from str.splitlines() in that blank lines are skipped and all lines
    are stripped (therefore line endings are always discarded).
    """
    string = string.strip()
    lines = string.splitlines()
    lines = [line.strip() for line in lines]    # Strip whitespace
    lines = [line for line in lines if line]    # Skip empty lines
    return lines


def make_slug(string: str, max_length: Optional[int] = 50) -> str:
    """
    Turn arbitrary text into a decent slug.

    Uses a single hyphen to separate parts.

        >>> make_slug('Once upon a time in Shaolin')
        'once-upon-a-time-in-shaolin'

    Args:
        string:
            Input string.

        max_length:
            Truncate the output, if necessary to this length.
            Set to none to ignore length.

    See:
        `animal3.utils.django.unique_slug()`
        `animal3.utils.files.clean_filename()`
        `animal3.utils.files.unique_filename()`

    Returns:
        Short, url-safe, string.

    """
    slug = force_str(string)
    slug = slug.lower()
    slug = re.sub(r'\&[a-z]+\;', '', slug)
    slug = slugify(slug)
    slug = re.sub(r'[^a-z0-9\-]', '-', slug)
    slug = re.sub(r'\-+', '-', slug)
    if max_length is not None:
        slug = slug[:max_length]
    return slug.strip('-')


def make_slugs(
    strings: Sequence[str],
    max_length: Optional[int] = 50,
    unique: bool = True,
) -> List[str]:
    """
    Convert a sequence of strings into a list of unique slugs.

    Despite the name, the intended use is to help create variable names
    from plain english, the header row from a CSV file for example. As such,
    underscores are used instead of the hyphens than `make_slug()` uses, and
    empty strings in input are replaced with a single underscores.

    Args:
        sequence:
            Input strings.
        max_length:
            As per `make_slug()`, except that numeric suffix added for uniqueness
            may cause actual length to be longer in some cases.
        unique:
            Add numerical suffix to ensure that all slugs are unique.
            Set to false to relax this requirement.

    Returns:
        List of slugs.
    """
    seen: Set[str] = set()
    slugs = []
    for string in strings:
        # Pass-off bulk of clean-up work
        slug = make_slug(string, max_length=max_length)
        if not slug:
            slug = '_'
        slug = slug.replace('-', '_')

        # Python keyword?
        if keyword.iskeyword(slug):
            slug += '_'

        # Force unique
        if unique:
            if slug in seen:
                slug = _unique_suffix(slug, seen)
            seen.add(slug)

        slugs.append(slug)
    return slugs


def paragraphs_split(string: str) -> List[str]:
    """
    Break given plain-text string into paragraphs.

    A paragraph is defined as having a blank line between. Care is taken
    to avoid empty paragraphs caused by extraneous blank lines.

    Returns:
        A list of paragraphs
    """
    string = string.strip()
    lines = string.splitlines()

    # Use empty lines to build list of paragraphs
    paragraphs = []
    parts = []
    for line in lines:
        line = line.strip()
        if line:
            parts.append(line)
        else:
            paragraphs.append('\n'.join(parts))
            parts = []
    else:
        paragraphs.append('\n'.join(parts))

    # Drop empty paragraphs caused by extra blank lines
    paragraphs = [p for p in paragraphs if p]

    return paragraphs


def paragraphs_wrap(string: str, width: int = 78) -> str:
    """
    Wrap the paragraphs within `string` to the given width.

    Returns: string
    """
    parts = []
    for paragraph in paragraphs_split(string):
        if len(paragraph) > width:
            paragraph = textwrap.fill(paragraph, width=width)
        parts.append(paragraph)
    return "\n\n".join(parts)


def phone_add_separators(phone: str, separator: str = ' ') -> str:
    """
    Add separators to phone number.

        >>> phone_add_separators('021555123')
        '021 555 123'

    Number may use letters, eg. 0900 DIK DIK
    """
    # Remove existing separators
    phone = re.sub(r'[^0-9A-Za-z]', '', phone)
    # Add space after prefix
    phone = re.sub(r'^(02\d|0800|0900|0508|0\d)', r'\g<1> ', phone)
    # Add space after exchange
    phone = re.sub(r'(\d{3})(\d{3,4})$', r'\g<1> \g<2>', phone)
    return phone


def phone_normalise(phone: str, country_code: str = '64') -> str:
    """
    Produce full formal phone number from given input.

        >>> phone_normalise('021 555 600')
        '+64-21-555-600'

    NB. A country code is prepended only if number does not start with '+'.
    """
    # Replace '00' prefix with '+'
    if phone.startswith('00'):
        phone = f"+{phone[2:]}"

    # Drop '0' prefix
    if phone.startswith('0'):
        phone = phone[1:]

    # Local number?
    if not phone.startswith('+'):
        # ~ phone = phone_add_separators(phone)
        phone = f"+{country_code}-{phone}"

    # Force use of hyphens as separators
    phone = re.sub(r'[^0-9A-Za-z\+]', '-', phone)

    return phone


def plain_quotes(string: str) -> str:
    """
    Replace 'smart' or 'curly' quotes with their 'normal' equivilants.

    >>> plain_quotes('“...”')
    '"..."'

    Returns:
        Plain-ascii double or single quotes.
    """
    string = force_str(string, strings_only=True)
    single = u"'"
    double = u'"'
    mapping = {
        34: single,     # " \u0022 QUOTATION MARK
        39: single,     # ' \u0027 APOSTROPHE
        171: double,    # « \u00ab LEFT-POINTING DOUBLE ANGLE QUOTATION MARK
        187: double,    # » \u00bb RIGHT-POINTING DOUBLE ANGLE QUOTATION MARK
        1370: single,   # ՚ \u055a ARMENIAN APOSTROPHE
        8216: single,   # ‘ \u2018 LEFT SINGLE QUOTATION MARK
        8217: single,   # ’ \u2019 RIGHT SINGLE QUOTATION MARK
        8218: single,   # ‚ \u201a SINGLE LOW-9 QUOTATION MARK
        8219: single,   # ‛ \u201b SINGLE HIGH-REVERSED-9 QUOTATION MARK
        8220: double,   # “ \u201c LEFT DOUBLE QUOTATION MARK
        8221: double,   # ” \u201d RIGHT DOUBLE QUOTATION MARK
        8222: double,   # „ \u201e DOUBLE LOW-9 QUOTATION MARK
        8223: double,   # ‟ \u201f DOUBLE HIGH-REVERSED-9 QUOTATION MARK
        8249: single,   # ‹ \u2039 SINGLE LEFT-POINTING ANGLE QUOTATION MARK
        8250: single,   # › \u203a SINGLE RIGHT-POINTING ANGLE QUOTATION MARK
        12317: double,  # 〝 \u301d REVERSED DOUBLE PRIME QUOTATION MARK
        12318: double,  # 〞 \u301e DOUBLE PRIME QUOTATION MARK
        12319: double,  # 〟 \u301f LOW DOUBLE PRIME QUOTATION MARK
        65282: single,  # ＂\uff02 FULLWIDTH QUOTATION MARK
        65287: single,  # ＇\uff07 FULLWIDTH APOSTROPHE
    }
    return string.translate(mapping)


def reverse_replace(
    string: str, search: str, replace: str, *, limit: Optional[int] = None,
) -> str:
    """
    Search and replace from the end of the string.

    Args:
        string:
            String to search through.
        search:
            String to search for.
        replace:
            String to insert into its place.
        limit:
            Maximum number of occurrences to replace. None for no limit.

    Returns:
        Transformed string. May be the same, if `search` is not found.
    """
    if limit is None:
        limit = -1
    parts = string.rsplit(search, limit)
    return replace.join(parts)


def sentences(string: str, number: int = 1) -> str:
    """
    Returns n sentences from given string.

    Args:
        string (str):
            Input text
        number (int):
            Number of sentences to extract.  Defaults to 1, a single sentence.

    An ordinary string is returned, retaining the delimiters exactly as
    found, excepting that white-space is stripped from both ends of the
    returned string.

    For the purposes of this function, the end of a sentence is defined as
    being one or more full-stops, question, or exclamation marks.

    This is simplistic, but has the advantage of being fast and,
    importantly, makes the function's behaviour easy to predict.  See the
    tests for examples of input that can confuse the function.

    Getting clever with heuristics, eg. looking after delimiters for the
    absence of spaces, or lower-cased words, sure would be fun though, but just
    as error prone.  Advanced sentence tokenising should be left to an advanced
    project like http://nltk.org/
    """
    parts = split_sentences(string, maxsplit=number)
    return " ".join(parts[:number]).strip()


def shorten(given: str, max_length: int = 60, suffix: str = '...') -> str:
    """
    Shorten given string by chopping its end off and adding suffix.

    For the sake of tidiness, whitespace and punctuation is removed from the
    end of the string before adding the suffix. The final length returned
    may therefore be less that `maxlen`.

        >>> shorten("Sphinx of black quartz, judge my vow.", 16)
        'Sphinx of bla...'

    Args:
        given:
            Input string
        maxlen:
            The maximum length allowed.
        suffix:
            A 'continuation' string to append. Defaults to '...'

    Returns:
        A string at most `maxlen` characters long.
    """
    if len(given) <= max_length:
        return given

    short = given[:max_length - len(suffix)]
    short = short.rstrip(punctuation + whitespace).rstrip()
    short += suffix
    return short


def split_name(full_name: str) -> Tuple[str, str]:
    """
    Best-effort attempt to split a full name into first and last-name parts.

        >>> split_name('Leon Matthews')
        ('Leon', 'Matthews')

    Args:
        string (str)

    Returns:
        A 2-tuple of strings (first_name, last_name)
    """
    parts = full_name.split()
    first = parts[0] if parts else ''
    last = ' '.join(parts[1:]) if len(parts) > 1 else ''
    return (first, last)


def split_sentences(string: str, maxsplit: int=0) -> List[str]:
    """
    Break input into sentences.

    Args:
        string:
            Input string.
        maxsplit:
            If maxsplit is nonzero, at most maxsplit splits occur, and the
            remainder of the string is returned as the final element of
            the list.

    Returns:
        List of sentences.
    """
    parts = re.split(r"([\.\?\!]+)(?=\W)", string, maxsplit=maxsplit)
    sentences = []
    for start, end in zip_longest(parts[::2], parts[1::2]):
        sentence = start if end is None else f"{start}{end}"
        sentence = sentence.strip()
        if sentence:
            sentences.append(sentence)
    return sentences


def strip_blank(string: str) -> str:
    """
    Strip blank lines.
    """
    lines = []
    for line in string.splitlines():
        line = line.rstrip()
        if line:
            lines.append(line)
    return "\n".join(lines)


def strip_tags(string: str, replace: str = '') -> str:
    """
    Simple but fast stripping of HTML tags out of string.

    >>> strip_tags("<p><strong>Iced Coffee</strong></p>")
    'Iced Coffee'

    """
    return re.sub(r'<[^<]+?>', replace, string)


def trademe_emphasis(string: str) -> str:
    """
    Add basic subset of markdown-style ephasis on body text using HTML tags.

    Only three styles are supported:

        *italic*
        **bold**
        ***bold & italic***

    Note that there can be no space between the asterix and the word.

    Args:
        string:
            Plain-text input.

    Returns:
        HTML string.
    """
    # Bold & italic
    string = re.sub(r'\*\*\*(?=\w)([^\*]*\w)\*\*\*', r'<strong><em>\1</em></strong>', string)

    # Bold
    string = re.sub(r'\*\*(?=\w)([^\*]*\w)\*\*', r'<strong>\1</strong>', string)

    # Italic
    string = re.sub(r'\*(?=\w)([^\*]*\w)\*', r'<em>\1</em>', string)

    return string


def _unique_suffix(slug: str, conflicts: Iterable[str]) -> str:
    """
    Add a numerical suffix to the end of `slug` to make it unique.

    So that previously deleted names are not re-used, this function works by
    finding the largest existing numerical suffix and adding one to it.

    Args:
        slug (str):
            Some candicate string, eg. 'example'. It may have an existing
            numerical suffix attached, eg. 'example32'.

        conflicts (Iterable[str]):
            A collection of strings that share a non-numeric preix with `slug`.

            This should be a small sub-set of all of the names in a system
            by some sort of filtering operation. Note that any existing
            numerical suffix MUST be stripped off before this filtering takes
            place, with say: ``slug.rstrip('1234567890')``.

    Returns: Unique string
    """
    # Anything to do?
    if not conflicts:
        return slug

    # Drop any numeric suffix
    cleaned = slug.rstrip('1234567890')

    # Find highest value
    length = len(cleaned)
    suffixes = [s[length:] for s in conflicts if s.startswith(cleaned)]
    maximum = 1
    for suffix in suffixes:
        try:
            value = int(suffix)
        except ValueError:
            value = 0
        maximum = max(value, maximum)

    # Build unique slug
    maximum += 1
    unique = f"{cleaned}{maximum}"
    return unique
