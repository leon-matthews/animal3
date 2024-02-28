
from typing import cast
from unittest import skip

from django.forms.boundfield import BoundField
from django.test import SimpleTestCase

from animal3.utils.testing import multiline, multiline_strip

from ..renderers import BoundFieldRenderer

from .forms import SampleForm


@skip("In pause for Santa Claus")
class BoundFieldRendererTest(SimpleTestCase):
    bound_form: SampleForm
    form: SampleForm
    maxDiff = None
    renderer: BoundFieldRenderer

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.bound_form = SampleForm({})
        cls.bound_form.is_valid()
        cls.form = SampleForm()
        cls.renderer = BoundFieldRenderer()

    def render(self, field: BoundField) -> str:
        string = self.renderer.render(field)
        html = cast(str, string)
        html = multiline_strip(html)
        return html

    def test_render_checkbox(self) -> None:
        html = self.render(self.form['subscribe'])
        expected = multiline("""
            <div class="field">
            <div class="control">
            <label class="checkbox">
            <input type="checkbox" name="subscribe" id="id_subscribe" required>
            Subscribe
            </label>
            </div>
            <p class="help">May we collect your information, then bombard you with emails?</p>
            </div>
        """)
        self.assertEqual(html.strip(), expected)

    def test_render_radioselect(self) -> None:
        html = self.render(self.form['answer2'])
        expected = multiline("""
            <div class="field">
            <label class="label">Answer2</label>
            <div class="control">
            <label class="radio">
            <input type="radio" name="answer2">
            No
            </label>
            <label class="radio">
            <input type="radio" name="answer2">
            Yes
            </label>
            </div>
            <p class="help">Here, let me lay &#x27;em out for you.</p>
            </div>
        """)
        self.assertEqual(html.strip(), expected)

    def test_render_select(self) -> None:
        html = self.render(self.form['answer'])
        expected = multiline("""
            <div class="field">
            <label class="label">Answer</label>
            <div class="control">
            <div class="select">
            <select name="answer" id="id_answer" required>
            <option value="" selected></option>
            <option value="0" >No</option>
            <option value="1" >Yes</option>
            </select>
            </div>
            </div>
            <p class="help">Only two choices here - but only one is correct.</p>
            </div>
        """)
        self.assertEqual(html.strip(), expected)

    def test_render_text(self) -> None:
        html = self.render(self.form['name'])
        expected = multiline("""
            <div class="field">
            <label class="label">Name</label>
            <div class="control">
            <input type="text" name="name" class="input" id="id_name" required>
            </div>
            <p class="help">Put your name in here. Just like on an exam.</p>
            </div>
        """)
        self.assertEqual(html.strip(), expected)

    def test_render_text_error(self) -> None:
        form = SampleForm({})
        html = self.render(form['name'])
        expected = multiline("""
            <div class="field">
            <label class="label">Name</label>
            <div class="control">
            <input type="text" name="name" class="input" id="id_name" required>
            </div>
            <p class="help is-danger">This field is required.</p>
            </div>
        """)
        self.assertEqual(html.strip(), expected)

    def test_render_textarea(self) -> None:
        html = self.render(self.form['message'])
        expected = multiline("""
            <div class="field">
            <label class="label">Message</label>
            <div class="control">
            <textarea name="message" class="textarea" cols="5" id="id_message" required rows="3">
            </textarea>
            </div>
            <p class="help">Lay out your thoughts. The process can be cathartic.</p>
            </div>
        """)
        self.assertEqual(html.strip(), expected)

    def test_build_context(self) -> None:
        """
        Test internal method `BoundFieldRenderer._build_context()`.
        """
        field = self.form['name']
        self.assertIsInstance(field, BoundField)
        context = self.renderer._build_context(field)
        expected = {
            'errors': [],
            'help_text': 'Put your name in here. Just like on an exam.',
            'label': 'Name',
            'label_id': 'id_name',
            'required': True,
            'widget': '<input type="text" name="name" class="input" id="id_name" required>',
            'widget_type': 'text'
        }
        self.assertEqual(context, expected)

    def test_choose_template(self) -> None:
        """
        Test internal method `BoundFieldRenderer._choose_template()`.
        """
        def assert_relpath(field_name: str, relpath: str) -> None:
            self.assertEqual(
                self.renderer._choose_template(self.form[field_name]),
                relpath,
            )

        assert_relpath('name', 'django/forms/fields/text.html')
        assert_relpath('message', 'django/forms/fields/textarea.html')

    def test_get_template(self) -> None:
        """
        Test internal method `BoundFieldRenderer._get_template()`.
        """
        field = self.form['message']
        relpath = self.renderer._choose_template(field)
        template = self.renderer._get_template(relpath)
        self.assertTrue(hasattr(template, 'render'))

    def test_get_template_error(self) -> None:
        """
        Test error raised from internal method `BoundFieldRenderer._get_template()`.
        """
        message = r"^Form field template not found: templates/banana.html$"
        with self.assertRaisesRegex(NotImplementedError, message):
            self.renderer._get_template('banana.html')
