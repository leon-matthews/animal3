
from typing import Callable

from .admin import *                                        # noqa: F401, F403
from .generic import *                                      # noqa: F401, F403
from .html_editor import *                                  # noqa: F401, F403
from .mixins import *                                       # noqa: F401, F403
from .simple import *                                       # noqa: F401, F403


def template_view(template_name: str) -> Callable:
    # Deprecated 2021-02-24
    import warnings
    warnings.warn(
        "template_view() moved to animal3.views.simple.template()",
        DeprecationWarning,
        stacklevel=2)
    return template(template_name)                          # noqa: F405
