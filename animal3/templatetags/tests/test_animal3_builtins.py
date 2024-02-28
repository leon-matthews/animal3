
from configparser import ConfigParser
from decimal import Decimal
from typing import Any, Dict
from unittest import skipIf

import django
from django.core.exceptions import ImproperlyConfigured
from django.template import RequestContext
from django.test import RequestFactory, SimpleTestCase

try:
    from animal3.adapters import markdown
except ImportError:
    markdown = None

from animal3.utils.logging import CaptureLogs, logger_hush
from animal3.utils.testing import multiline, render

from ..animal3_builtins import add_gst, email, email_url, entities, file_icon


class AbsoluteURLTest(SimpleTestCase):
    def test_absolute_url(self) -> None:
        """
        Test full and relative paths.
        """
        request = RequestFactory().get('/start/')
        context = RequestContext(request, {
            'full': '/media/some/file.pdf',
            'relative': 'here/',
            'request': request,
        })
        template = multiline("""
            {% load animal3_builtins %}
            {% absolute_url full %}
            {% absolute_url relative %}
        """)
        expected = multiline("""
            http://testserver/media/some/file.pdf
            http://testserver/start/here/
        """)
        output = render(template, context)
        self.assertEqual(output, expected)

    def test_bad_context(self) -> None:
        """
        Context missing a request.
        """
        context = {
            'full': '/media/some/file.pdf',
        }
        template = multiline("""
            {% load animal3_builtins %}
            {% absolute_url full %}
        """)
        message = "Given template context missing 'request'"
        with self.assertRaisesRegex(RuntimeError, message):
            render(template, context)


class AddGSTTest(SimpleTestCase):
    maxDiff = None

    def test_add_gst(self) -> None:
        context = {
            'price': 100.00,
        }
        template = multiline("""
            {% load animal3_builtins %}
            {{ price|currency }}
            {{ price|add_gst }}
            {{ price|add_gst|currency }}
        """)
        expected = multiline("""
            $100.00
            115.00
            $115.00
        """)
        output = render(template, context)
        self.assertEqual(output, expected)

    def test_add_gst_failure(self) -> None:
        message = r"{% add_gst %} given invalid input: 'banana'"
        with self.assertRaisesRegex(ValueError, message):
            add_gst('banana')


class AppInstalledTest(SimpleTestCase):
    def test_add_gst(self) -> None:
        context: Dict[str, Any] = {}
        template = multiline("""
            {% load animal3_builtins %}
            {{ 'common'|app_installed }}
            {{ 'twinkle'|app_installed }}
        """)
        expected = multiline("""
            True
            False
        """)
        output = render(template, context)
        self.assertEqual(output, expected)


class AppReadmeTest(SimpleTestCase):
    @skipIf(markdown is None, 'markdown-it-py is not installed')
    def test_app_readme(self) -> None:
        template = multiline("""
            {% load animal3_builtins %}
            {% app_readme 'animal3' %}
            """)
        output = render(template)
        self.assertTrue("<h1>Animal3</h1>" in output)

    @skipIf(markdown is not None, 'markdown-it-py is installed')
    def test_app_readme_markdown_not_installed(self) -> None:
        """
        Empty output and logger error if tag used while markdown not installed.
        """
        template = multiline("""
            {% load animal3_builtins %}
            {% app_readme 'animal3' %}
            """)
        with logger_hush():
            output = render(template)
        self.assertEqual(output, "")


class AttrsTest(SimpleTestCase):
    def test_full(self) -> None:
        mapping = {
            'action': '',
            'novalidate': False,
            'pattern': '[A-Za-z]{3}',
            'placeholder': 'banana',
            'required': True,
        }
        context = {'mapping': mapping}
        template = multiline("""
                {% load animal3_builtins %}
                {{ mapping|attrs }}
                """)
        self.assertEqual(
            render(template, context),
            'action="" pattern="[A-Za-z]{3}" placeholder="banana" required')

    def test_quoting(self) -> None:
        mapping = {
            'bad<key': '',
            'bad>key2': True,
            'bad-value': 'L&P',
        }
        context = {'mapping': mapping}
        template = multiline("""
                {% load animal3_builtins %}
                {{ mapping|attrs }}
                """)
        self.assertEqual(
            render(template, context),
            'bad-value="L&amp;P" bad&lt;key="" bad&gt;key2')


class BasenameTest(SimpleTestCase):
    def test_basename(self) -> None:
        context = {'path': '/media/folders/cover/my-little-banana.png'}
        template = multiline("""
                {% load animal3_builtins %}
                {{ path }}
                {{ path|basename }}
                {{ path|basename:"./" }}
                """)
        expected = multiline("""
            /media/folders/cover/my-little-banana.png
            my-little-banana.png
            ./my-little-banana.png
        """)
        output = render(template, context)
        self.assertEqual(output, expected)


class CapitaliseTest(SimpleTestCase):
    def test_capitalise(self) -> None:
        template = multiline("""
                {% load animal3_builtins %}
                {{ "at play in the fields of the lord"|capitalise }}
                {{ "silence of the lambs"|capitalise }}
                {{ "the alaska-siberian expedition"|capitalise }}
                """)
        expected = multiline("""
            At Play in the Fields of the Lord
            Silence of the Lambs
            The Alaska-Siberian Expedition
        """)
        output = render(template, {})
        self.assertEqual(output, expected)


class CopyTest(SimpleTestCase):
    def test_add_name_to_context(self) -> None:
        """
        Copy should update context.
        """
        # Create empty context object
        context = django.template.Context()
        self.assertFalse('copy' in context)

        # Render template and check output
        template = multiline("""
            {% load animal3_builtins %}
            {% copy %}
            Hairy MacClary
            {% endcopy %}
        """)
        output = render(template, context)
        self.assertEqual(output, 'Hairy MacClary')

        # Confirm context updated with correct value
        self.assertTrue('copy' in context)
        self.assertEqual(context['copy'], 'Hairy MacClary')

    def test_rename_context(self) -> None:
        """
        Copy context variable can be renamed
        """
        # Render template and check output
        template = multiline("""
            {% load animal3_builtins %}
            {% copy as name %}
            Hairy MacClary
            {% endcopy %}
        """)
        context = django.template.Context()
        output = render(template, context)
        self.assertEqual(output, 'Hairy MacClary')

        # Confirm context updated with correct value
        self.assertFalse('copy' in context)
        self.assertTrue('name' in context)
        self.assertEqual(context['name'], 'Hairy MacClary')

    def test_bad_syntax(self) -> None:
        template = multiline("""
            {% load animal3_builtins %}
            {% copy apple apple apple %}
            Granny Smith
            {% endcopy %}
        """)

        message = (
            r"^{% copy %} tag has invalid arguments: "
            r"\['copy', 'apple', 'apple', 'apple'\]$"
        )
        with self.assertRaisesRegex(django.template.TemplateSyntaxError, message):
            render(template)


class CurrencyTest(SimpleTestCase):
    def test_currency_filter(self) -> None:
        context = {
            'coffee': 3.5,
            'fur': 'possum',
            'house': 550e3,
        }
        template = multiline("""
            {% load animal3_builtins %}
            {{ coffee|currency }}
            {{ fur|currency }}
            {{ house|currency }}
        """)
        expected = multiline("""
            $3.50

            $550,000.00
        """)
        output = render(template, context)
        self.assertEqual(output, expected)


class CurrencyBigTest(SimpleTestCase):
    def test_currency_big_filter(self) -> None:
        context = {
            'auckland_median_salary': 67e3,
            'auckland_median_house': 1.14e6,
            'brotherhood_of_steel': 'Many bottlecaps',
            'nz_gdp': 206.9e9,
            'usa_military': 753e9,
            'usa_gdp': 21.43e12,
        }
        template = multiline("""
            {% load animal3_builtins %}
            {{ auckland_median_salary|currency_big }}
            {{ auckland_median_house|currency_big }}
            {{ brotherhood_of_steel|currency_big }}
            {{ nz_gdp|currency_big:'USD $' }}
            {{ usa_military|currency_big:'USD $' }}
            {{ usa_gdp|currency_big:'USD $' }}
        """)
        expected = multiline("""
            $67k
            $1.1M

            USD $210B
            USD $750B
            USD $21T
        """)
        output = render(template, context)
        self.assertEqual(output, expected)


class CurrencyRoundedTest(SimpleTestCase):
    def test_currency_rounded_filter(self) -> None:
        context = {
            'coffee': 3.5,
            'fur': 'possum',
            'house': 550e3,
        }
        template = multiline("""
            {% load animal3_builtins %}
            {{ coffee|currency_rounded }}
            {{ fur|currency_rounded }}
            {{ house|currency_rounded }}
        """)
        expected = multiline("""
            $4

            $550,000
        """)
        output = render(template, context)
        self.assertEqual(output, expected)


class DurationTest(SimpleTestCase):
    def test_duration(self) -> None:
        context = {
            'modified': 17,
            'expiry': 21545455,
            'nonsense': 'carrot',
        }
        template = multiline("""
            {% load animal3_builtins %}
            {{ modified|duration }}
            {{ nonsense|duration }}
            {{ expiry|duration }}
            """)
        expected = multiline("""
            17 seconds
            unknown
            8 months
        """)
        output = render(template, context)
        self.assertEqual(output, expected)


class EmailTest(SimpleTestCase):
    maxDiff = None

    def test_email(self) -> None:
        expected = (
            '<a href="&#x6d;&#x61;&#x69;&#x6c;&#x74;&#x6f;&#x3a;'
            '&#x61;&#x40;&#x62;&#x2e;&#x63;&#x64;">'
            '&#x61;&#x40;&#x62;&#x2e;&#x63;&#x64;'
            '</a>'
        )
        self.assertEqual(email('a@b.cd', autoescape=False), expected)
        self.assertEqual(email('a@b.cd', autoescape=True), expected)

    def test_email_url_error(self) -> None:
        """
        Log error and return empty string if value not ane mail address
        """
        with CaptureLogs() as captured:
            self.assertEqual(email('abc'), '')
        warnings = [r.getMessage() for r in captured.records]
        expected = ["Template filter 'email' unexpected input: 'abc'"]
        self.assertEqual(warnings, expected)

    def test_email_in_template(self) -> None:
        context = {
            'address': 'a@b.cd',
            'unsafe': '<script>',
        }
        template = multiline("""
            {% load animal3_builtins %}

            {{ address }}
            {{ address|email }}
            {{ address|email:'class="button"' }}
            {{ unsafe|email }}
            {{ unsafe }}

            {% autoescape off %}
            {{ address }}
            {{ address|email }}
            {{ address|email:'class="button"' }}
            {{ unsafe }}
            {{ unsafe|email }}
            {% endautoescape %}
        """)

        expected = multiline("""
            a@b.cd
            <a href="&#x6d;&#x61;&#x69;&#x6c;&#x74;&#x6f;&#x3a;&#x61;&#x40;&#x62;&#x2e;&#x63;&#x64;">&#x61;&#x40;&#x62;&#x2e;&#x63;&#x64;</a>
            <a href="&#x6d;&#x61;&#x69;&#x6c;&#x74;&#x6f;&#x3a;&#x61;&#x40;&#x62;&#x2e;&#x63;&#x64;" class="button">&#x61;&#x40;&#x62;&#x2e;&#x63;&#x64;</a>

            &lt;script&gt;


            a@b.cd
            <a href="&#x6d;&#x61;&#x69;&#x6c;&#x74;&#x6f;&#x3a;&#x61;&#x40;&#x62;&#x2e;&#x63;&#x64;">&#x61;&#x40;&#x62;&#x2e;&#x63;&#x64;</a>
            <a href="&#x6d;&#x61;&#x69;&#x6c;&#x74;&#x6f;&#x3a;&#x61;&#x40;&#x62;&#x2e;&#x63;&#x64;" class="button">&#x61;&#x40;&#x62;&#x2e;&#x63;&#x64;</a>
            <script>
        """)    # noqa: E501 Ignore long lines

        # Check output
        with CaptureLogs() as captured:
            output = render(template, context)
            self.assertEqual(output, expected)

        # Check warnings
        warnings = [r.message for r in captured.records]
        expected_warnings = [
            "Template filter 'email' unexpected input: '&lt;script&gt;'",
            "Template filter 'email' unexpected input: '<script>'",
        ]
        self.assertEqual(warnings, expected_warnings)


class EmailUrlTest(SimpleTestCase):
    maxDiff = None

    def test_email_url(self) -> None:
        expected = (
            '&#x6d;&#x61;&#x69;&#x6c;&#x74;&#x6f;&#x3a;'
            '&#x61;&#x40;&#x62;&#x2e;&#x63;&#x64;'
        )
        self.assertEqual(email_url('a@b.cd', autoescape=True), expected)
        self.assertEqual(email_url('a@b.cd', autoescape=False), expected)

    def test_email_url_error(self) -> None:
        """
        Log error and return empty string if value not ane mail address
        """
        with CaptureLogs() as captured:
            self.assertEqual(email_url('abc'), '')
        warnings = [r.getMessage() for r in captured.records]
        expected = ["Template filter 'email_url' unexpected input: 'abc'"]
        self.assertEqual(warnings, expected)


class EntitiesTest(SimpleTestCase):
    def test_entities_function(self) -> None:
        string = "<script>"
        expected = '&#x3c;&#x73;&#x63;&#x72;&#x69;&#x70;&#x74;&#x3e;'
        self.assertEqual(entities(string), expected)

    def test_entities_autoescape(self) -> None:
        """
        Entities filter with autoescape enabled and disabled.
        """
        context = {
            'name': 'Leon',
            'unsafe': '<script>',
        }
        template = multiline("""
            {% load animal3_builtins %}

            {{ name }}
            {{ name|entities }}
            {{ unsafe }}
            {{ unsafe|entities }}

            {% autoescape off %}
            {{ name }}
            {{ name|entities }}
            {{ unsafe }}
            {{ unsafe|entities }}
            {% endautoescape %}
        """)

        expected = multiline("""
            Leon
            &#x4c;&#x65;&#x6f;&#x6e;
            &lt;script&gt;
            &#x3c;&#x73;&#x63;&#x72;&#x69;&#x70;&#x74;&#x3e;


            Leon
            &#x4c;&#x65;&#x6f;&#x6e;
            <script>
            &#x3c;&#x73;&#x63;&#x72;&#x69;&#x70;&#x74;&#x3e;
        """)

        output = render(template, context)
        self.assertEqual(output, expected)


class ExtensionTest(SimpleTestCase):
    def test_extension(self) -> None:
        context = {
            'file1': 'easy.jpg',
            'file2': 'more.than.one.period.jpeg',
            'file3': 'no-extension',
            'path': '/media/folders/cover/my-little-banana.png',
        }
        template = multiline("""
            {% load animal3_builtins %}
            {{ file1|extension }}
            {{ file2|extension }}
            {{ file3|extension }}
            {{ path|extension }}
        """)
        expected = multiline("""
            jpg
            jpeg

            png
        """)
        output = render(template, context)
        self.assertEqual(output, expected)


class FileIconTest(SimpleTestCase):
    def test_from_name(self) -> None:
        context: Dict[str, Any] = {}
        template = multiline("""
            {% load animal3_builtins %}
            {% file_icon 'apple.png' %}
            {% file_icon 'banana.mp4' %}
            {% file_icon 'carrots' %}
            {% file_icon 'durian.xyz' %}
        """)
        expected = multiline("""
            <span class="icon icon-file-picture"></span>
            <span class="icon icon-file-video"></span>
            <span class="icon icon-file-empty"></span>
            <span class="icon icon-file-empty"></span>
        """)
        output = render(template, context)
        self.assertEqual(output, expected)

    def test_from_path(self) -> None:
        context: Dict[str, Any] = {}
        template = multiline("""
            {% load animal3_builtins %}
            {% file_icon '/tmp/apple.png' %}
            {% file_icon 'tmp/banana.mp4' %}
            {% file_icon 'no/such/folder/carrots.jpg' %}
            {% file_icon '/no/such/folder/carrots.webp' %}
        """)
        expected = multiline("""
            <span class="icon icon-file-picture"></span>
            <span class="icon icon-file-video"></span>
            <span class="icon icon-file-picture"></span>
            <span class="icon icon-file-picture"></span>
        """)
        output = render(template, context)
        self.assertEqual(output, expected)

    def test_file_icon_type_error(self) -> None:
        """
        We want an exception in this case, as it's a caller error.
        """
        message = r"^Template tag 'file_icon' expects a file field or name, given: 9973$"
        with self.assertRaisesRegex(TypeError, message):
            file_icon(9973)                                 # type: ignore[arg-type]


class FileSizeTest(SimpleTestCase):
    def test_file_size(self) -> None:
        context = {
            'floppy': 1474560,
            'microsd': 'so large, yet so small',
        }
        template = multiline("""
            {% load animal3_builtins %}

            The venerable floppy disk's capacity peaked at a
            whopping {{ floppy|file_size }} (or {{ floppy|file_size:True }} if
            you're not a fan of ISO-compliant file sizes).

            On the other hand, a micro-SD card is {{ microsd|file_size }}.
        """)
        expected = multiline("""
            The venerable floppy disk's capacity peaked at a
            whopping 1.5MB (or 1.4MiB if
            you're not a fan of ISO-compliant file sizes).

            On the other hand, a micro-SD card is .
        """)
        output = render(template, context)
        self.assertEqual(output, expected)


class GetValueTest(SimpleTestCase):
    def test_render(self) -> None:
        ISO3166 = {
            'AF': 'Afghanistan',
            'NZ': 'New Zealand',
            'ZW': 'Zimbabwe',
        }

        context = {
            'ISO3166': ISO3166,
            'codes': ['NZ', 'ZW', 'XX'],
        }
        template = multiline("""
            {% load animal3_builtins %}
            {% for code in codes %}
                {{ code }} = {{ ISO3166|get_value:code }}
            {% endfor %}
        """)
        expected = "NZ = New Zealand\n\n    ZW = Zimbabwe\n\n    XX ="
        output = render(template, context)
        self.assertEqual(output, expected)


class GoogleAnalyticsTest(SimpleTestCase):
    settings_ini: ConfigParser
    settings_ini_empty: ConfigParser

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()

        cls.settings_ini = ConfigParser()
        cls.settings_ini.add_section('keys')
        cls.settings_ini.set('keys', 'google_tracking_id', 'DONT_TRACK_ME_BRO')

        cls.settings_ini_empty = ConfigParser()
        cls.settings_ini_empty.add_section('keys')
        cls.settings_ini_empty.set('keys', 'google_tracking_id', '')

    def test_usage_error(self) -> None:
        """
        Old usage should cause an error to be thrown.
        """
        template = multiline("""
            '{% load animal3_builtins %}'
            '{% google_analytics "XXXX" %}'
        """)
        message = r"Google Analytics tracking ID must only be set in 'settings.ini'"
        with self.assertRaisesRegex(ImproperlyConfigured, message), logger_hush():
            render(template)

    def test_in_production(self) -> None:
        """
        Tag should expand into correct JavaScript snippet.
        """
        template = multiline("""
            '{% load animal3_builtins %}'
            '{% google_analytics %}'
        """)
        with self.settings(SETTINGS_INI=self.settings_ini):
            output = render(template)

        expected = [
            "gtag('config', 'DONT_TRACK_ME_BRO')",
            'async src="https://www.googletagmanager.com/gtag/js?id=DONT_TRACK_ME_BRO">'
        ]
        for string in expected:
            self.assertIn(string, output)

    def test_only_comment_if_debug(self) -> None:
        """
        Expand into just a comment if DEBUG=True.
        """
        with self.settings(DEBUG=True):
            with self.settings(SETTINGS_INI=self.settings_ini):
                template = multiline("""
                    {% load animal3_builtins %}
                    {% google_analytics %}
                """)
                output = render(template)

        expected = "<!-- Google Analytics for 'DONT_TRACK_ME_BRO' here in producton -->"
        self.assertEqual(output, expected)

    def test_warn_if_tracking_id_empty(self) -> None:
        """
        Emit warning if no value set for GOOGLE_TRACKING_ID.
        """
        template = multiline("""
            {% load animal3_builtins %}
            {% google_analytics %}
        """)
        with self.settings(SETTINGS_INI=self.settings_ini_empty):
            output = render(template)
        expected = "<!-- No value found for 'google_tracking_id' in 'settings.ini' -->"
        self.assertEqual(output, expected)


class IntCommaTest(SimpleTestCase):
    def test_intcomma_numbers(self) -> None:
        context = {
            'small': 42,
            'large': 2**32,
        }
        template = multiline("""
            {% load animal3_builtins %}

            {{ small|intcomma }}
            {{ 4544|intcomma }}
            {{ large|intcomma }}
        """)
        expected = multiline("""
            42
            4,544
            4,294,967,296
            """)
        output = render(template, context)
        self.assertEqual(output, expected)

    def test_intcomma_invalid_input(self) -> None:
        context = {
            'none': None,
            'commas': '4,294,967,296',
            'name': 'Leon',
            'floating': 3.32193,
        }
        template = multiline("""
        {% load animal3_builtins %}

        {{ none|intcomma }}
        {{ commas|intcomma }}
        {{ name|intcomma }}
        {{ floating|intcomma }}
        """)
        expected = multiline("""
        0
        4,294,967,296

        3
        """)
        with logger_hush():
            output = render(template, context)
        self.assertEqual(output, expected)


class PercentageTest(SimpleTestCase):
    def test_percentage(self) -> None:
        context = {
            'half': Decimal('0.5'),
        }
        template = multiline("""
            {% load animal3_builtins %}

            {{ half|percentage }}
            {{ 1.22|percentage }}
            {{ 'banana'|percentage }}
            {{ 0.355|percentage }}

            """)
        expected = multiline('''
            50%
            122%

            35.5%
            ''')
        output = render(template, context)
        self.assertEqual(output, expected)


class PhoneTest(SimpleTestCase):
    def test_phone(self) -> None:
        template = multiline("""
            {% load animal3_builtins %}

            {{ '0800 messiah'|phone }}
            {{ '0800 MESSIAH'|phone }}
            {{ '+64 9 375 4451'|phone }}
            {{ '09 375 4451'|phone }}
            """)
        expected = multiline('''
            <a href="tel:+64-800-6377424">0800 messiah</a>
            <a href="tel:+64-800-6377424">0800 MESSIAH</a>
            <a href="tel:+64-9-375-4451">+64 9 375 4451</a>
            <a href="tel:+64-9-375-4451">09 375 4451</a>
            ''')
        output = render(template)
        self.assertEqual(output, expected)


class PhoneUrlTest(SimpleTestCase):
    def test_phone(self) -> None:
        template = multiline("""
            {% load animal3_builtins %}

            {{ '0800 messiah'|phone_url }}
            {{ '0800 MESSIAH'|phone_url }}
            {{ '+64 9 375 4451'|phone_url }}
            {{ '09 375 4451'|phone_url }}
            """)
        expected = multiline('''
            tel:+64-800-6377424
            tel:+64-800-6377424
            tel:+64-9-375-4451
            tel:+64-9-375-4451
            ''')
        output = render(template)
        self.assertEqual(output, expected)


class QueryTest(SimpleTestCase):
    def test_query(self) -> None:
        """
        Combine pre-existing query variables.
        """
        request = RequestFactory().get('/', {'o': 'author', 'exclude': 'stock'})
        context = RequestContext(request, {
            'request': request,
        })
        template = multiline("""
            {% load animal3_builtins %}
            {% query %}
            {% query page=3 exclude=None %}
        """)
        expected = multiline("""
            exclude=stock&o=author
            o=author&page=3
        """)
        output = render(template, context)
        self.assertEqual(output, expected)


class QueryOrderingTest(SimpleTestCase):
    def test_query_ordering(self) -> None:
        """
        Combine pre-existing query variables.
        """
        request = RequestFactory().get('/', {'o2': 'popular', 'o3': '-author'})
        context = RequestContext(request, {
            'request': request,
        })
        template = multiline("""
            {% load animal3_builtins %}
            {% query_ordering 'price' %}
            {% query_ordering '-price' %}
            {% query_ordering 'popular' 'o2' %}
            {% query_ordering '-popular' 'o2' %}
            {% query_ordering 'author' 'o3' %}
            {% query_ordering '-author' 'o3' %}
        """)
        expected = multiline("""
            o=price
            o=-price
            o2=-popular
            o2=-popular
            o3=author
            o3=author
        """)
        output = render(template, context)
        self.assertEqual(output, expected)


class TrademeEmphasisTest(SimpleTestCase):
    def test_trademe_emphasis(self) -> None:
        template = multiline("""
            {% load animal3_builtins %}
            {{ "Don't worry about it."|trademe_emphasis }}
            {{ 'You *have* to double check!'|trademe_emphasis }}
            {{ "Real **tough** guy, aren't you?"|trademe_emphasis }}
            {{ 'Now ***this*** is drama!'|trademe_emphasis }}
            """)
        expected = multiline('''
            Don't worry about it.
            You <em>have</em> to double check!
            Real <strong>tough</strong> guy, aren't you?
            Now <strong><em>this</em></strong> is drama!
        ''')
        output = render(template)
        self.assertEqual(output, expected)
