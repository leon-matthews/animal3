
from typing import Any, Dict

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.mail.message import EmailMultiAlternatives
from django.db import models
from django.http import HttpRequest
from django.test import RequestFactory, SimpleTestCase

from animal3.utils.testing import DocTestLoader, multiline
from animal3.tests.models import SimpleModel

from .. import email
from ..email import build_address, HtmlEmail

from . import DATA_FOLDER


class DocTests(SimpleTestCase, metaclass=DocTestLoader, test_module=email):
    pass


class BuildAddressTest(SimpleTestCase):
    def test_email_only(self) -> None:
        self.assertEqual(
            build_address('john@example.com'),
            'john@example.com',
        )

    def test_email_and_name(self) -> None:
        self.assertEqual(
            build_address('john@example.com', 'John Smith'),
            'John Smith <john@example.com>',
        )

    def test_email_and_empty_name(self) -> None:
        self.assertEqual(
            build_address('john@example.com', '   '),
            'john@example.com',
        )

    def test_invalid_email_error(self) -> None:
        """
        Arguments in the wrong order?
        """
        message = "Does not appear to be an email address: 'John Smith'"
        with self.assertRaisesRegex(RuntimeError, message):
            build_address('John Smith', 'john@example.com')


class EmailSimple(HtmlEmail):
    subject = "Just heard about {{ problem }}!"
    template_name = 'animal3/utils/tests/example_message.html'


class EmailExtraAttributes(HtmlEmail):
    context_object_name = 'silly'
    extra_context = {
        'META_TITLE': 'This takes precedence',
    }
    subject = "Just heard about {{ problem }}!"
    subject_prefix = "[ADMIN]"
    template_name = 'animal3/utils/tests/example_message.html'


class EmailMissingSubject(HtmlEmail):
    template_name = 'animal3/utils/tests/example_message.html'


class EmailMissingTemplateName(HtmlEmail):
    subject = "Just heard about {{ problem }}!"


class HtmlEmailInitialiserTest(SimpleTestCase):
    """
    Test just the actions taken by the `HtmlEmail` class's initialiser.
    """
    request: HttpRequest

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.request = RequestFactory().get('/')

    def test_context_default(self) -> None:
        email = EmailSimple(self.request)
        self.assertIsInstance(email.context, dict)
        expected = {
            'DEFAULT_EMAIL',
            'DEFAULT_PHONE',
            'META_COPYRIGHT',
            'META_DESCRIPTION',
            'META_KEYWORDS',
            'META_TITLE',
            'request',
            'SITE_NAME',
        }
        self.assertEqual(email.context.keys(), expected)

    def test_extra_context(self) -> None:
        email = EmailSimple(self.request, name='Leon', problem='Busy as, bro!')
        self.assertEqual(email.context['name'], 'Leon')
        self.assertEqual(email.context['problem'], 'Busy as, bro!')

    def test_context_instance_not_model(self) -> None:
        email = EmailSimple(self.request, 'Not a model')    # type: ignore[arg-type]
        self.assertEqual(email.context['object'], 'Not a model')

    def test_context_instance_missing(self) -> None:
        email = EmailSimple(self.request)
        self.assertFalse('object' in email.context)
        self.assertFalse('silly' in email.context)

    def test_context_instance_is_model(self) -> None:
        instance = SimpleModel()
        email = EmailSimple(self.request, instance)
        self.assertIs(email.context['object'], instance)
        self.assertIs(email.context['simplemodel'], instance)

    def test_context_override_names(self) -> None:
        instance = SimpleModel()
        email = EmailExtraAttributes(self.request, instance)
        self.assertEqual(email.context['META_TITLE'], 'This takes precedence')
        self.assertIs(email.context['object'], instance)
        self.assertIs(email.context['silly'], instance)

    def test_message_object(self) -> None:
        email = EmailSimple(self.request)
        self.assertIsInstance(email.message, EmailMultiAlternatives)

    def test_missing_subject(self) -> None:
        message = r"^Missing required 'subject' attribute$"
        with self.assertRaisesRegex(ImproperlyConfigured, message):
            EmailMissingSubject(self.request)

    def test_missing_template_name(self) -> None:
        message = r"^Missing required 'template_name' attribute$"
        with self.assertRaisesRegex(ImproperlyConfigured, message):
            EmailMissingTemplateName(self.request)

    def test_recipient_defaults(self) -> None:
        """
        To and from addresses set to value in settings.ini
        """
        email = EmailSimple(self.request)

        self.assertIsInstance(email.message.from_email, str)
        self.assertEqual(email.message.from_email, settings.DEFAULT_FROM_EMAIL)

        self.assertIsInstance(email.message.to, list)
        self.assertEqual(len(email.message.to), 1)
        self.assertEqual(email.message.to[0], settings.DEFAULT_FROM_EMAIL)

    def test_wrong_arguments(self) -> None:
        context: Dict[str, Any] = {}
        message = r"^EmailSimple\(\) takes a request as its first argument$"
        with self.assertRaisesRegex(TypeError, message):
            EmailSimple(context)                            # type: ignore[arg-type]


class HtmlEmailMethodsTest(SimpleTestCase):
    """
    Test the behaviour of the rest of the email's methoods.
    """
    extra_context: Dict[str, str]
    instance: models.Model
    maxDiff = None
    request: HttpRequest

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.extra_context = {
            'first_name': 'Beelzebub',
            'companion': 'Mary',
            'problem': 'Hell freezing over',
            'sender': 'God',
        }
        cls.instance = SimpleModel(
            title="Welding for Beginners",
            description="An 12-week course, for two hours every Wednesday night",
        )
        cls.request = RequestFactory().get('/')

    def setUp(self) -> None:
        self.email = EmailSimple(self.request, self.instance, **self.extra_context)

    def test_add_bcc(self) -> None:
        # Add single recipient
        self.email.add_bcc('somegirl@example.com')
        self.assertEqual(self.email.message.bcc, ['somegirl@example.com'])

    def test_add_cc(self) -> None:
        # Add list of recipients
        self.email.add_cc(['somegirl@example.com', 'someguy@example.com'])
        self.assertEqual(
            self.email.message.cc,
            ['somegirl@example.com', 'someguy@example.com']
        )

    def test_add_cc_none(self) -> None:
        self.email.add_cc(None)
        self.assertEqual(self.email.message.cc, [])

    def test_attach_file(self) -> None:
        path = DATA_FOLDER / 'bean.zip'
        self.email.attach_file(path)

        self.assertEqual(len(self.email.message.attachments), 1)
        name, data, mimetype = self.email.message.attachments[0]
        self.assertEqual(name, 'bean.zip')
        self.assertIsInstance(data, bytes)
        self.assertEqual(mimetype, 'application/zip')

    def test_attach(self) -> None:
        self.email.attach('bean.zip', b'', 'application/zip')

        self.assertEqual(len(self.email.message.attachments), 1)
        name, data, mimetype = self.email.message.attachments[0]
        self.assertEqual(name, 'bean.zip')
        self.assertIsInstance(data, bytes)
        self.assertEqual(mimetype, 'application/zip')

    def test_attach_no_mimetype(self) -> None:
        """
        Mimetype not provided? No problem, we like guessing.
        """
        self.email.attach('bean.zip', b'')

        self.assertEqual(len(self.email.message.attachments), 1)
        name, data, mimetype = self.email.message.attachments[0]
        self.assertEqual(name, 'bean.zip')
        self.assertIsInstance(data, bytes)
        self.assertEqual(mimetype, 'application/zip')

    def test_render_body_html(self) -> None:
        body = self.email.render_body().strip()
        expected = multiline("""

            <section class="header">
            Welcome to HtmlMail™!
            </section>


            <section class="body">
            <p>
            Dear Beelzebub.
            </p>

            <p>
            I was sorry to hear about Hell freezing over. We all hope that the situation is resolved
            to your satisfaction shortly. Mary and I will be travelling to assist you
            as soon as can be arranged.
            </p>

            <p>
            Yours, etc.
            </p>

            <p>
            God
            </p>
            </section>


            <section class="footer">
            Unsubscribe?! LOL, No... Why would we even let you do that?
            </section>

        """)
        self.assertEqual(body, expected)

    def test_render_body_text(self) -> None:
        self.email.send()
        expected = multiline("""
            Welcome to HtmlMail™!

            Dear Beelzebub.

            I was sorry to hear about Hell freezing over. We all hope that the situation is
            resolved to your satisfaction shortly. Mary and I will be travelling to assist
            you as soon as can be arranged.

            Yours, etc.

            God

            Unsubscribe?! LOL, No... Why would we even let you do that?
        """)
        self.assertEqual(self.email.message.body, expected)

    def test_render_subject(self) -> None:
        with self.settings(EMAIL_SUBJECT_PREFIX='[example.com]'):
            subject = self.email.render_subject()
        expected = '[example.com] Just heard about Hell freezing over!'
        self.assertEqual(subject, expected)

    def test_render_subject_prefix_custom(self) -> None:
        email = EmailExtraAttributes(self.request, self.instance, **self.extra_context)
        subject = email.render_subject()
        expected = '[ADMIN] Just heard about Hell freezing over!'
        self.assertEqual(subject, expected)

    def test_render_subject_prefix_empty(self) -> None:
        with self.settings(EMAIL_SUBJECT_PREFIX=''):
            subject = self.email.render_subject()
        expected = 'Just heard about Hell freezing over!'
        self.assertEqual(subject, expected)


class HtmlEmailSendTest(SimpleTestCase):
    extra_context: Dict[str, str]
    maxDiff = None
    request: HttpRequest

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.extra_context = {
            'first_name': 'Beelzebub',
            'companion': 'Mary',
            'problem': 'Hell freezing over',
            'sender': 'God',
        }
        cls.request = RequestFactory().get('/')

    def setUp(self) -> None:
        address = build_address('dude@example.com', 'Default Dude')
        with self.settings(DEFAULT_FROM_EMAIL=address):
            self.email = EmailSimple(self.request, **self.extra_context)

    def test_send_default(self) -> None:
        """
        Default 'to' and 'from' addresses.
        """
        self.email.send()
        default = 'Default Dude <dude@example.com>'
        self.assertEqual(self.email.message.from_email, default)
        self.assertEqual(self.email.message.to, [default])

    def test_send_one_recipient(self) -> None:
        self.email.send('Customer <customer@example.com>')
        self.assertEqual(self.email.message.to, ['Customer <customer@example.com>'])

    def test_send_many_recipient(self) -> None:
        recipients = [
            'first@example.com',
            'second@example.com',
            'third@example.com',
        ]
        self.email.send(recipients)
        self.assertEqual(self.email.message.to, recipients)
