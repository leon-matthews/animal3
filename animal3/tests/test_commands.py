
from django.conf import settings
from django.core import mail
from django.core.management import CommandError
from django.test import SimpleTestCase

from animal3.utils.testing import multiline, run_management_command


class LoggingTreeTest(SimpleTestCase):
    def test_logging_tree(self) -> None:
        output = run_management_command('logging_tree')
        self.assertIn('o<--"django"', output)
        self.assertIn('Level NOTSET so inherits level WARNING', output)
        lines = output.splitlines()
        self.assertGreater(len(lines), 100)


class SendEmailTest(SimpleTestCase):
    def test_error_no_email_address(self) -> None:
        message = r"^Error: the following arguments are required: EMAIL_ADDRESS$"
        with self.assertRaisesRegex(CommandError, message):
            run_management_command('send_email')
        self.assertEqual(len(mail.outbox), 0)

    def test_send_email(self) -> None:
        output = run_management_command('send_email', 'Leon <leon@example.com>')
        expected = multiline("""
            Send email to 'Leon <leon@example.com>'
        """)
        self.assertEqual(output.strip(), expected)
        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.to, ['Leon <leon@example.com>'])
        self.assertEqual(message.from_email, settings.DEFAULT_FROM_EMAIL)
        self.assertEqual(
            message.subject,
            f'{settings.EMAIL_SUBJECT_PREFIX} Sample Message',
        )


class SendSMSTest(SimpleTestCase):
    def test_error_no_arguments(self) -> None:
        message = r"^Error: the following arguments are required: MESSAGE, NUMBER$"
        with self.assertRaisesRegex(CommandError, message):
            run_management_command('send_sms')

    def test_error_no_number(self) -> None:
        message = r"^Error: the following arguments are required: NUMBER$"
        with self.assertRaisesRegex(CommandError, message):
            run_management_command('send_sms', 'Call me back')

    def test_send_sms(self) -> None:
        output = run_management_command('send_sms', 'Call me back', '+64215551234')
        self.assertEqual(
            output.strip(),
            "Send SMS (dry-run) to +64215551234: 'Call me back'",
        )
