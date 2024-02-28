
from typing import Any

from django.conf import settings
from django.core.mail import EmailMessage
from django.core.management.base import CommandParser

from animal3 import fake
from animal3.management.base import CommandBase
from animal3.utils.text import paragraphs_wrap


class Command(CommandBase):
    help = "Send test message to given email address"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            'email', metavar='EMAIL_ADDRESS',
            help="email address to send test message to",
        )
        super().add_arguments(parser)

    def handle(self, *args: Any, **options: Any) -> None:
        self.send_email(options['email'])

    def send_email(self, address: str) -> None:
        """
        Send sample message to given email address.

        Args:
            address:
                Email address to send sample message to

        Returns:
            None
        """
        self.info(f"Send email to {address!r}")
        email = EmailMessage()
        email.subject = self._build_subject('Sample Message')
        email.body = self._build_body()
        email.to = [address]
        email.send()

    def _build_body(self) -> str:
        """
        Build sample body text.
        """
        paragraphs = fake.paragraphs(2, 4)
        return paragraphs_wrap(paragraphs)

    def _build_subject(self, subject: str) -> str:
        """
        Add the site's default subject prefix.
        """
        prefix = settings.EMAIL_SUBJECT_PREFIX
        subject = f"{prefix} {subject}"
        return subject
