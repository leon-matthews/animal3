
from unittest import TestCase

from animal3 import fake


class CodeTest(TestCase):
    def test_default(self) -> None:
        string = fake.code()
        self.assertIsInstance(string, str)
        self.assertEqual(len(string), 6)


class LettersTest(TestCase):
    def test_default(self) -> None:
        string = fake.letters()
        self.assertIsInstance(string, str)
        self.assertEqual(len(string), 6)
        self.assertTrue(string.isupper())


class NumericStringTest(TestCase):
    def test_default(self) -> None:
        digits = fake.numeric_string()
        self.assertIsInstance(digits, str)
        self.assertEqual(len(digits), 6)

    def test_check_num_digits(self) -> None:
        digits = fake.numeric_string(27)
        self.assertIsInstance(digits, str)
        self.assertEqual(len(digits), 27)

    def test_arguments_out_of_bound(self) -> None:
        with self.assertRaises(ValueError):
            fake.numeric_string(-560)
        with self.assertRaises(ValueError):
            fake.numeric_string(0)
        with self.assertRaises(ValueError):
            fake.numeric_string(257)
        with self.assertRaises(ValueError):
            fake.numeric_string(1255)


class ParagraphTest(TestCase):
    def test_paragraph(self) -> None:
        string = fake.paragraph()
        self.assertIsInstance(string, str)
        self.assertNotIn('\n', string)


class ParagraphsTest(TestCase):
    def test_paragraphs(self) -> None:
        string = fake.paragraphs(3)

        # Blank line between paragraphs
        self.assertEqual(string.count('\n\n'), 2)

        # No other newlines except those above
        self.assertEqual(string.count('\n'), 2 * 2)


class ParagraphsHtmlTest(TestCase):
    def test_html_paragraphs(self) -> None:
        html = fake.paragraphs_html(3)
        self.assertTrue(html.count('<p>'), 3)
        self.assertTrue(html.count('</p>'), 3)


class WordTest(TestCase):
    def test_word(self) -> None:
        word = fake.word()
        self.assertIsInstance(word, str)
        self.assertGreater(len(word), 0)


class WordsTest(TestCase):
    def test_words(self) -> None:
        words = fake.words(5)
        self.assertEqual(len(words.split()), 5)
