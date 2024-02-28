
from html.parser import HTMLParser
from typing import Dict, List, Optional, Tuple

from .text import paragraphs_wrap


Attrs = List[Tuple[str, Optional[str]]]


class AttributesParser(HTMLParser):
    """
    Build a list of the just the attributes for the given tag type.

    For example, given HTML with several images:

        >>> parser = AttributesParser('input')
        >>> parser.feed(html)
        >>> parser.get_attributes()
        [{'src: '...', 'width': '...'},
         {'src: '...', 'width': '...'}]

    """
    def __init__(self, tag_name: str):
        """
        Initialiser.

        Args:
            tag:
                Tag we're interested in, eg. 'input'
        """
        super().__init__()
        self.tag_name = tag_name.lower()
        self.attributes: List[Dict[str, Optional[str]]] = []

    def get_attributes(self) -> List[Dict[str, Optional[str]]]:
        return self.attributes

    def handle_starttag(self, tag: str, attrs: Attrs) -> None:
        if tag == self.tag_name:
            self.attributes.append(dict(attrs))


class ExtractTextParser(HTMLParser):
    """
    Convert HTML to plain text using standard library's HTML parser.

    Attributes:
        block_tags:
            Text inside these tags will be followed by a blank line.
        hidden_tags:
            Ignore text inside these tags.

    """
    block_tags = {'div', 'head', 'p'}
    hidden_tags = {'script', 'style'}

    def __init__(self, skip_head: bool = True) -> None:
        """
        Initialiser.

        Args:
            skip_head:
                Skip all tags in HTML <head>, if present.

        """
        super().__init__()
        self.current = ''
        self.in_head = False
        self.skip_head = skip_head
        self.text: List[str] = []

    def get_text(self) -> str:
        return ''.join(self.text).strip()

    def handle_starttag(self, tag: str, attrs: Attrs) -> None:
        self.current = tag
        if tag == 'head':
            self.in_head = True

        # Pull out absolute URLs
        if tag == 'a':
            link = dict(attrs).get('href', '')
            assert isinstance(link, str)
            if link.startswith('http'):
                self.text.append(f"\n{link}\n\n")

    def handle_endtag(self, tag: str) -> None:
        if tag == 'head':
            self.in_head = False
        if tag in self.block_tags:
            self.text.append('\n\n')

    def handle_data(self, data: str) -> None:
        # Skip hidden tags
        if self.current in self.hidden_tags:
            return

        # Skip all tags in head
        if self.in_head and self.skip_head:
            return

        # Add another part to output
        stripped = data.strip()
        if stripped:
            self.text.append(data)


def find_csrftoken(html: str) -> Optional[str]:
    """
    Search an HTML document for the token put there by {% csrf_token %}

    Could also be achieved from the DOM:

        <script>
        const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        </script>

    Args:
        html:
            Entire document.

    Returns:
        CSRF token if found, None otherwise.
    """
    parser = AttributesParser('input')
    parser.feed(html)
    csrftoken = None
    for attrs in parser.get_attributes():
        name = attrs.get('name')
        if name == 'csrfmiddlewaretoken':
            csrftoken = attrs.get('value')

    return csrftoken


def html2text(html: str, maxlen: Optional[int] = None, skip_head: bool = True) -> str:
    """
    Convert HTML string into plain text.

    Args:
        maxlen:
            If given, will wrap long lines in output using the algorithm
            in `paragraphs_wrap()`

        skip_head:
            Skip all tags in HTML <head>, if present.

    See:
        `animal3.utils.text.paragraphs_wrap()`

    Returns:
        HTML as plain string.
    """
    parser = ExtractTextParser(skip_head=skip_head)
    parser.feed(html)
    text = parser.get_text()
    if maxlen is not None:
        text = paragraphs_wrap(text, maxlen)
    return text.strip()
