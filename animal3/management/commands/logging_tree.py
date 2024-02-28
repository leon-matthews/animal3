"""
Print logging configuration.

https://pypi.org/project/logging_tree/
"""

from contextlib import redirect_stdout
from typing import Any

from animal3.management.base import CommandBase

import logging_tree


class Command(CommandBase):
    help = "Print current logging configuration. Try different settings files."

    def handle(self, *args: Any, **options: Any) -> None:
        with redirect_stdout(self.stdout):                  # type: ignore[type-var]
            logging_tree.printout()
