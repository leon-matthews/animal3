
from typing import Any, List

from django.core.management.base import CommandParser

from animal3.management.base import CommandBase


class Command(CommandBase):
    help = "Send SMS message using the TNZ API"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            'message', metavar='MESSAGE',
            help="message to send in quotes, eg. 'Merry Christmas!'",
        )
        parser.add_argument(
            'numbers', metavar='NUMBER', nargs='+',
            help="one or more mobile phone numbers",
        )
        super().add_arguments(parser)

    def handle(self, *args: Any, **options: Any) -> None:
        numbers = options['numbers']
        message = options['message']
        self.send_sms(numbers, message)

    def send_sms(self, numbers: List[str], message: str) -> None:
        self.info(f"Send SMS (dry-run) to {', '.join(numbers)}: {message!r}")
