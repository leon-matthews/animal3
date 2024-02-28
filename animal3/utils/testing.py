"""
Tools for writing unit tests.
"""

from contextlib import contextmanager
import csv
import doctest
from io import StringIO
from itertools import zip_longest
import json
from pathlib import Path
import tempfile
import textwrap
from types import ModuleType
from typing import (
    Any,
    Callable,
    Dict,
    Iterator,
    Iterable,
    List,
    Optional,
    Mapping,
    TYPE_CHECKING,
    Union,
    Tuple,
    Type,
)
import warnings

from django.apps import apps
from django.apps.config import AppConfig
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.sitemaps import Sitemap
from django.contrib.sites.shortcuts import get_current_site
from django.core.management import call_command
from django.http import HttpRequest, HttpResponse
from django.template import Context, Template
from django.test import RequestFactory
from django.views.generic import View


JSON = Union[Dict[str, Any], List[Any]]


# Show mypy which interface we're using
if TYPE_CHECKING:
    from django.test import TestCase
    TestCaseMixin = TestCase
else:
    TestCaseMixin = object


@contextmanager
def assert_deprecated(expected_message: Optional[str] = None) -> Iterator[None]:
    """
    Raise an `AssertionError` if a single `DeprecationWarning` is not raised.

    Use it within a unittest to simply test your deprecated functions.

        with assert_deprecated():
            old_function()

    Args:
        expected_message (str):
            Optionally match expected warning message.

    Raises:
        AssertionError:
            If DeprecationWarning not raised, of if the warning
            message (if given) does not match.
    """
    try:
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            yield
            if not (len(w) > 0) or not issubclass(w[0].category, DeprecationWarning):
                raise AssertionError("DeprecationWarning not raised")

            if expected_message is not None:
                issued_message = str(w[0].message)
                if expected_message != issued_message:
                    message = (
                        f"DeprecationWarning message mismatch {expected_message!r} ",
                        f"!= {issued_message!r}"
                    )
                    raise AssertionError(message)
    except Exception:
        raise
    finally:
        pass


def decorate_request(
        request: HttpRequest,
        session: Optional[Dict] = None,
        user: Optional[Any] = None) -> HttpRequest:
    """
    Add user, session, and messages support to request.

    Args:
        request:
            An empty request object, ie. from `RequestFactory.get()`.
        session:
            Optional dictionary to emulate Django session store.
        user:
            Optional user.

    Returns: An `django.http.HttpRequest` object.
    """
    def fake_get_response(
            request: HttpRequest,
            *args: Any,
            **kwargs: Any) -> HttpResponse:
        return HttpResponse(b"Fake response")

    # User
    if user is None:
        user = AnonymousUser()
    request.user = user

    # Session middleware
    if session is None:
        session = {}
    SessionMiddleware(fake_get_response).process_request(request)
    request.session.update(session)
    request.session.save()

    # Messages middleware (requires session)
    MessageMiddleware(fake_get_response).process_request(request)
    request.session.save()

    return request


def json_unserialise(response: HttpResponse) -> JSON:
    """
    Extract data from binary JSON string in body of HTTP response.

    Args:
        response:
            A response object with JSON data in body.

    Raises:
        json.decoder.JSONDecodeError:
            If body is empty or invalid.

    Returns:
        List or dictionary of data.
    """
    string = response.content.decode(encoding=response.charset)
    data = json.loads(string)
    assert isinstance(data, (dict, list))
    return data


def GET(
    cbv: Type[View],
    url: str = '/',
    *args: Any,
    data: Optional[Dict[str, Any]] = None,
    session: Optional[Dict[str, Any]] = None,
    user: Optional[Any] = None,
    **kwargs: Any,
) -> HttpResponse:
    """
    Test a GET request directly on a CBV class (ie. not via test client).

    Render form view in a GET::

        response = GET(ExampleFormView)
        self.assertEqual(response.status_code, 200)
        form = response.context_data['form']
        self.assertFalse(form.is_bound)

    Args:
        See the `POST()` method below. All the same, except that `data` represents
        values from the path query parameters.

    Returns:
        A `django.http.HttpResponse` object.
    """
    request = RequestFactory().get(url, data=data)
    decorated = decorate_request(request, session, user)
    view = cbv()
    view.setup(decorated, *args, **kwargs)
    response = view.dispatch(decorated, *args, **kwargs)

    # Force a copy of request for testing cookies, messages, sessions, etc...
    if not hasattr(response, '_request'):
        response._request = decorated                       # type: ignore[attr-defined]

    assert isinstance(response, HttpResponse)
    return response


def multiline(value: str) -> str:
    """
    Removing leading indentation from given string.
    """
    return textwrap.dedent(value).strip()


def multiline_strip(string: str, *, keep_blank: bool = False) -> str:
    """
    Remove indentation from input, optionally stripping blank lines.

    Args:
        multiline:
            Multiline string
        keep_blank:
            Preserve blank lines from input if True.

    Returns:
        Stripped version of input lines.
    """
    lines = []
    for line in string.strip().splitlines():
        line = line.strip()
        if not line and not keep_blank:
            continue
        lines.append(line)
    return "\n".join(lines)


class DocTestLoader(type):
    """
    Metaclass to automatically create test methods from doctests.

    Runs all of the doctests found in in module `test_module` as individual test
    cases. For example (note the `test_module` argument given to the metaclass):

        from .. import utils

        class DocTests(TestCase, metaclass=DocTestLoader, test_module=utils):
            pass

    Created as a work-around to a problem running Django tests in parallel. In
    particular, using the normal `load_tests()` method to integrate doctests into
    unittests caused the `multiprocessing` module to fail with:

        TypeError: cannot pickle 'module' object

    In this work-around we use the module under test, but do not retain a
    reference to it for `multiprocessing` to choke on.
    """
    def __new__(
        meta: Type[type],
        class_name: str,
        bases: Tuple[type, ...],
        /,
        namespace: Dict,
        **kwargs: Any,
    ) -> type:
        """
        Prevent `test_module` argument from going further.
        """
        kwargs.pop('test_module')
        return type.__new__(meta, class_name, bases, namespace, **kwargs)

    @classmethod
    def __prepare__(
        meta: Type[type],
        class_name: str,
        bases: Tuple[type, ...],
        /,
        **kwargs: Any,
        # ~ test_module: ModuleType,
    ) -> Mapping[str, object]:
        """
        Create test methods and add them to the class.
        """
        prepared = type.__prepare__(class_name, bases)
        test_module: ModuleType = kwargs.pop('test_module')
        suite = doctest.DocTestSuite(
            test_module,
            optionflags=doctest.NORMALIZE_WHITESPACE,
        )

        for test in suite:
            name = meta.create_test_name(test)              # type: ignore
            prepared[name] = meta.create_test_method(test)  # type: ignore

        return prepared

    @classmethod
    def create_test_method(cls, test: doctest.DocTestCase) -> Callable:
        def test_method(self) -> None:                      # type: ignore
            return test.runTest()
        return test_method

    @classmethod
    def create_test_name(cls, test: doctest.DocTestCase) -> str:
        name = repr(test).partition(' ')[0]
        name = f"test_doctest_{name}"
        return name


def POST(
    cbv: Type[View],
    url: str = '/',
    *args: Any,
    data: Optional[Dict[str, Any]] = None,
    session: Optional[Dict[str, Any]] = None,
    user: Optional[Any] = None,
    **kwargs: Any,
) -> HttpResponse:
    """
    Test a GET request directly on a CBV class (ie. not via test client).

    Check redirect on good POST to a form view:

        data = {..good data...}
        response = POST(ExampleFormView, data=data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers['location'], reverse('example:thanks'))
        self.assertEqual(Example.objects.count(), 1)

    Bad POST to a form view should re-render form with errors:

        empty = {}
        response = POST(ExampleFormView, data=empty)
        self.assertEqual(response.status_code, 200)
        form = response.context_data['form']
        self.assertTrue(form.is_bound)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors, {...})

    Ignores CSRF checks, using back-door Django devs left in place for
    testing.

    Args:
        cbv:
            A Template view class (*not* an instance)
        url:
            Optional URL of request. Not used.
        data:
            Optional dictionary of POST data to use.
        session:
            Optional dictionary of session data. See `decorate_request()`.
        user:
            Optional User object. See `decorate_request()`.
        args:
            Positional arguments, as from a captured URL.
        kwargs:
            Keyword arguments, as from a captured URL.

    Returns:
        Response instance.
    """
    if data is None:
        data = {}
    request = RequestFactory().post(url, data)
    request._dont_enforce_csrf_checks = True                # type: ignore[attr-defined]
    decorated = decorate_request(request, session, user)
    view = cbv()
    view.setup(decorated, *args, **kwargs)
    response = view.dispatch(decorated, *args, **kwargs)

    # Force a copy of request for testing cookies, messages, sessions, etc...
    if not hasattr(response, '_request'):
        response._request = decorated                       # type: ignore[attr-defined]

    assert isinstance(response, HttpResponse)
    return response


def render(
    template: str,
    context: Optional[Union[Dict, Context]] = None
) -> str:
    """
    Render plain string with context dictionary.

    Note that whitespace is stripped from both ends of the returned
    string to make comparisons tidier.
    """
    if context is None:
        context = {}
    output = str(Template(template).render(Context(context)))
    return output.strip()


def run_management_command(
    command: str,
    *args: Iterable[str],
) -> str:
    """
    Run Django management command and capture its output.

    Args:
        command:
            Name of command to run, eg. 'feedback_fake_data'
        *args:
            Command arguments. Will be  parsed by command, so should all be
            strings. eg. ('--no-color', '--no-input', '--verbosity=3')

    Raises:
        django.core.management.CommandError:
            If command files for some reason.

    Returns:
        Command's console output as multiline string.
    """
    out = StringIO()
    call_command(
        command,
        *args,
        stdout=out,
        stderr=out,
    )
    return out.getvalue()


def setup_test_app(package: str, label: Optional[str] = None) -> None:
    """
    Setup a Django test app for the provided package to allow test models
    tables to be created if the containing app has migrations.

    Create a ``models.py`` in the tests directory, then run this function, ie. in
    the file myapp/tests/__init__.py::

        from animal3.utils.testing import setup_test_app

        setup_test_app(__package__)

    This function should be called from app.tests __init__ module and pass
    along __package__.

    Credit to users on Django bug #7835:

        "Provide the ability for model definitions that are only availably
         during testing"

        https://code.djangoproject.com/ticket/7835

    """
    app_config = AppConfig.create(package)
    app_config.apps = apps
    if label is None:
        containing_app_config = apps.get_containing_app_config(package)
        assert containing_app_config is not None
        label = f'{containing_app_config.label}_tests'
    if label in apps.app_configs:
        raise ValueError(f"There's already an app registered with the '{label}' label.")
    app_config.label = label
    apps.app_configs[app_config.label] = app_config
    app_config.import_models()
    apps.clear_cache()


def sitemap_get_urls(sitemap: Sitemap) -> List[Dict[str, Any]]:
    """
    Build a list of URL data from the given sitemap instance.

    The Django sitemap framework can be confusing to work with. There are
    odd requirements and concepts map to different names. This function
    simply takes a Sitemap class and returns the data in produces.

    For example:

        [{'item': 3,
         'location': 'http://testserver/3/',
         'lastmod': None,
         'changefreq': None,
         'priority': '',
         'alternates': []'}]

    Args:
        sitemap_class:
            The sitemap class you wish to test.

    Returns:
        A list of dictionaries, as detailed above.
    """
    factory = RequestFactory()
    request = factory.get('/')
    request_site = get_current_site(request)
    return sitemap.get_urls(site=request_site)


class FakeRequestResponse:
    """
    Fakes the interface of `requests.Response`.

    Use as the return value for mocked calls, eg.

        return_value = FakeRequestResponse(json={})

        with mock.patch.object(
            client.session, 'get', return_value=return_value) as mocked:
                response = client.get('/some/path')

        self.assertEqual(response.json(), {})
    """
    def __init__(
        self,
        *,
        content: Optional[bytes] = None,
        json: Optional[JSON] = None,
        text: Optional[str] = None,
    ):
        """
        Initialiser.

        Args:
            content:
                Byte string to use as `response.content` property.
            json:
                Dictionary or list to return from `response.json()` method.
            text:
                String to use as `response.text` property.
        """
        self._content = b'' if content is None else content
        self._json = {} if json is None else json
        self._text = '' if text is None else text

    @property
    def content(self) -> bytes:
        return self._content

    def json(self) -> JSON:
        return self._json

    @property
    def text(self) -> str:
        return self._text

    def raise_for_status(self) -> None:
        pass


class TempFolderMixin(TestCaseMixin):
    """
    TestCase mixin to create a temporary folder for the whole test class.

    The attribute `temp_folder` is a `pathlib.Path` object to the folder.

    The folder is created in the `setUpClass()` method, so is therefore
    shared between all tests in the class. Any files saved to the folder
    will of course be deleted in the `tearDownClass()`.

    Very useful for testing forms that upload files:

        class UploadFormTest(TempFolderMixin, SimpleTestCase):
            def test_form_valid(self):
                with self.settings(MEDIA_ROOT=self.temp_folder):
                    POST(views.UploadFormView, data=VALID)

    """
    _temp_folder: tempfile.TemporaryDirectory
    temp_folder: Path

    @classmethod
    def setUpClass(cls) -> None:
        cls._temp_folder = tempfile.TemporaryDirectory(prefix=f"{cls.__name__}_")
        cls.temp_folder = Path(cls._temp_folder.name)
        super().setUpClass()

    @classmethod
    def tearDownClass(cls) -> None:
        cls._temp_folder.cleanup()
        super().tearDownClass()


class assertCSVEqualMixin(TestCaseMixin):
    """
    A TestCase mixin that provides the `assertCSVEqual` method.

    This provides richer feedback about the errors in the two CSV inputs.
    """
    assertEqual: Callable
    fail: Callable

    def assertCSVEqual(
        self,
        first: str,
        second: str,
        *,
        dialect: Type[csv.Dialect] = csv.excel,
    ) -> Any:
        """
        Compare two multi-line CSV strings for equality, including line endings.

        Args:
            first (string):
                Multi-line string for the first CSV file.
            second (string):
                Multi-line string for the second CSV file.

        Raises:
            AssertionError:
                If any mis-matches are detected.

        Returns: None
        """
        lines1 = first.splitlines(keepends=True)
        lines2 = second.splitlines(keepends=True)
        for line_num, (line1, line2) in enumerate(zip_longest(lines1, lines2), 1):
            if line1 is None:
                self.fail(f"Line {line_num}: Too few lines in first string")
            if line2 is None:
                self.fail(f"Line {line_num}: Too few lines in second string")

            assert isinstance(line1, str)
            assert isinstance(line2, str)
            if line1 != line2:
                self._compare_endings(line_num, line1, line2)
                self._compare_fields(line_num, line1, line2, dialect)
                self.assertEqual(line1, line2, f"Line {line_num}: Strings are not equal")

    def _compare_endings(
        self,
        line_num: int,
        line1: str,
        line2: str
    ) -> None:
        ending1 = line1[len(line1.rstrip()):]
        ending2 = line2[len(line2.rstrip()):]
        if ending1 != ending2:
            self.fail(
                f"Line {line_num}: First string ends with {ending1!r}, "
                f"second with {ending2!r}"
            )

    def _compare_fields(
        self,
        line_num: int,
        line1: str,
        line2: str,
        dialect: Type[csv.Dialect]
    ) -> None:
        lines = [line1, line2]
        reader = csv.reader(lines, dialect=dialect)
        fields1 = next(reader)
        fields2 = next(reader)

        # Number of fields
        if len(fields1) != len(fields2):
            message = []
            message.append(
                f"Line {line_num}: First string has {len(fields1)} fields, "
                f"second has {len(fields2)} fields:")
            message.append(f"  {line1.strip()}")
            message.append(f"  {line2.strip()}")
            self.fail("\n".join(message))

        # Contents of fields
        for count, (column1, column2) in enumerate(zip(fields1, fields2), 1):
            if column1 != column2:
                self.fail(f"Line {line_num}: Column {count}: {column1!r} != {column2!r}")
