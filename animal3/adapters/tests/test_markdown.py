
from unittest import skipIf, TestCase

from animal3.utils.testing import multiline

try:
    from ..markdown import commonmark_render, commonmark_render_file
except ImportError:
    commonmark_render = commonmark_render_file = None

from . import DATA_FOLDER


@skipIf(commonmark_render is None, "markdown-it-py not installed")
class CommonMarkRenderTest(TestCase):
    def test_render(self) -> None:
        source = multiline("""
            # Heading 1

            Be **bold** and *italic* in the face of danger.

            Don't worry about `variables` outside your control.
        """)

        expected = multiline("""
            <h1>Heading 1</h1>
            <p>Be <strong>bold</strong> and <em>italic</em> in the face of danger.</p>
            <p>Don't worry about <code>variables</code> outside your control.</p>
        """)
        html = commonmark_render(source)
        self.assertEqual(html, expected)

    def test_replacements(self) -> None:
        source = "Copyright (c) 2023 --- Leon Matthews"
        html = commonmark_render(source)
        expected = "<p>Copyright © 2023 — Leon Matthews</p>"
        self.assertEqual(html, expected)


@skipIf(commonmark_render_file is None, "markdown-it-py not installed")
class CommonMarkRenderFileTest(TestCase):
    def test_render(self) -> None:
        html = commonmark_render_file(DATA_FOLDER / 'commonmark.md')
        expected = multiline("""
            <h1>Heading 1</h1>
            <p>Be <strong>bold</strong> and <em>italic</em> in the face of danger.</p>
            <p>Don't worry about <code>variables</code> outside your control.</p>
        """)
        self.assertEqual(html, expected)
