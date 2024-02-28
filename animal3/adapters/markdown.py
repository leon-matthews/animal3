
from pathlib import Path

from animal3.utils.files import PathLike

from markdown_it import MarkdownIt
from mdit_py_plugins import deflist


def commonmark_render(source: str) -> str:
    """
    Render HTML from CommonMark source.

    Returns:
        HTML string.
    """
    options = {
        'typographer': True,
    }
    md = MarkdownIt('commonmark', options)
    md.use(deflist.deflist_plugin)
    md.enable(['replacements', 'table'])
    html = md.render(source).strip()
    assert isinstance(html, str)
    return html


def commonmark_render_file(path: PathLike, encoding: str = 'utf-8') -> str:
    """
    Render HTML from given file path.

    Returns:
        HTML string.
    """
    path = Path(path)
    with open(path, 'rt', encoding=encoding) as fp:
        source = fp.read()
    return commonmark_render(source)
