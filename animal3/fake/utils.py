
from pathlib import Path
import random
from typing import List, Optional

from animal3.utils.files import load_lines


__all__ = (
    'DATA_FOLDER',
    'get_count',
    'RandomLine',
)


DATA_FOLDER = Path(__file__).parent / 'data'


def get_count(low: int, high: Optional[int] = None) -> int:
    """
    Pick a concrete number from given number or range.

    number:
        May be an integer, or a range tuple, eg. (low, high)
    """
    if high is None:
        return low

    if low > high:
        raise ValueError(f"Low is greater than high: {low} > {high}")

    return random.randint(low, high)


class RandomLine:
    """
    Create function-like object to fetch random lines from given file or files.

    Reads file into memory, but only on first use.
    """
    def __init__(self, *file_names: str):
        self.lines: Optional[List[str]] = None
        self.paths = []
        for name in file_names:
            path = DATA_FOLDER / name
            if not path.is_file():
                raise ValueError(f"File not found: {path}")
            self.paths.append(path)

    def __call__(self) -> str:
        # Load lines from files?
        if self.lines is None:
            self.lines = []
            for path in self.paths:
                lines = load_lines(path)
                self.lines.extend(lines)

        return random.choice(self.lines)
