
from typing import Any, Dict, List, Optional, Union

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.mail import EmailMultiAlternatives
from django.db import models
from django.http import HttpRequest
from django.template import Context, Template
from django.template.loader import render_to_string

from .files import allowed_path, PathLike
from .html import html2text
from .mimetype import guess_mimetype


def build_address(email: str, name: Optional[str] = None) -> str:
    """
    Add name to email address, where possible.

        >>> build_address('john@example.com', 'John Doe')
        'John Doe <john@example.com>'
        >>> build_address('john@example.com')
        'john@example.com'

    Args:
        email:
            Valid email address, eg. 'john@example.com'
        name:
            Optional name. If not none, will be added to email address.

    Returns:
        Valid email address.
    """
    if '@' not in email:
        raise RuntimeError(f"Does not appear to be an email address: {email!r}")

    if name is None:
        return email

    name = name.strip()
    if not name:
        return email

    return f"{name} <{email}>"


class HtmlEmail:
    """
    HTML email class with similar API to Django DetailView CBV.

    Sub-class and provide attributes, like so:

        class RegistrationEmail(HtmlEmail):
            subject = "Thank you {{ registration.name }}"
            template_name = "registrations/emails/thanks.html"

    Instantiate with a view's request (needed to create absolute URLs in
    template) and an optional instance, eg.

        email = RegistrationEmail(request, registration)
        email.send()

    Wraps a Django `EmailMultiAlternatives` classes and is mostly concerned
    with populating attributes of that class. For example, we generate
    the plain-text body automatically from the rendered HTML body, then
    attach the HTML as a (preferred) alternative.

    Instantiate with a context, then send:

    Attributes:
        context_object_name:
            Optionally override the name of given model instance inside
            template. Uses lower-case model name if by default (and 'object').
        extra_context:
            Optional hard-coded context data, taking precedence over that from
            other sources.
        subject:
            Required email subject template. Same context variables as
            body template.
        subject_prefix:
            Optionally override Django's EMAIL_SUBJECT_PREFIX setting.
        template_name:
            Required (relative) path to HTML email body
            template, eg. 'contact/emails/thanks.html'

    See:
        `animal3.utils.html.html2text()`:
            Function used to create fall-back plain-text email body.
    """
    context_object_name: Optional[str] = None
    extra_context: Optional[Dict[str, Any]] = None
    subject: str
    subject_prefix: Optional[str] = None
    template_name: str

    def __init__(
        self,
        request: HttpRequest,
        instance: Optional[models.Model] = None,
        /,
        **extra_context: Any,
    ):
        """
        Initialiser.

        Args:
            request:
                HTTP Request, needed to build URLs in HTML template.
            instance:
                Optional model instance to add to template context.

        Returns None:
        """
        # Quick error message for previous function signature
        if not isinstance(request, HttpRequest):
            raise TypeError(
                f"{self.__class__.__name__}() takes a request as its first argument"
            )

        # Defaults
        self.message = EmailMultiAlternatives(
            to=self._build_recipients(settings.DEFAULT_FROM_EMAIL),
            from_email=settings.DEFAULT_FROM_EMAIL,
        )
        self.object = instance
        self.request = request
        self.context = self.get_context_data(**extra_context)

        # Required attributes
        required_attributes = ('subject', 'template_name')
        for name in required_attributes:
            value = getattr(self, name, None)
            if not value:
                raise ImproperlyConfigured(f"Missing required {name!r} attribute")

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Build context for rendering body and subject templates.

        Args:
            kwargs:
                Additional variables to add to context.

        Returns:
            Context dictionary.
        """
        # Default context
        context: Dict[str, Any] = {
            'DEFAULT_EMAIL': settings.DEFAULT_EMAIL,
            'DEFAULT_PHONE': settings.DEFAULT_PHONE,
            'META_COPYRIGHT': settings.META_COPYRIGHT,
            'META_DESCRIPTION': settings.META_DESCRIPTION,
            'META_KEYWORDS': settings.META_KEYWORDS,
            'META_TITLE': settings.META_TITLE,
            'request': self.request,
            'SITE_NAME': settings.SITE_NAME,
        }

        # Add model?
        if self.object:
            context['object'] = self.object
            context_object_name = self._get_context_object_name(self.object)
            if context_object_name:
                context[context_object_name] = self.object

        # Add kwargs
        context.update(kwargs)

        # Use `extra_context`?
        if self.extra_context is not None:
            context.update(self.extra_context)

        return context

    def add_bcc(self, bcc: Optional[Union[str, List[str]]]) -> None:
        """
        Set's the list of BCC recipients for email.

        For example:

            message = ThanksEmail(request)
            message.add_bcc('micromanager@example.com')

        Despite name, subsequent calls overwrites existing BCC data.

        Args:
            bcc:
                One or more addresses. Set to none to reset CC list.

        Returns:
            None
        """
        self.message.bcc = self._build_recipients(bcc)

    def add_cc(self, cc: Optional[Union[str, List[str]]]) -> None:
        """
        Set's the list of CC recipients for email.

        For example:

            message = ThanksEmail(request)
            message.add_cc('Staff <staff@example.com>')

        Despite name, subsequent calls overwrites existing CC data.

        Args:
            cc:
                One or more addresses. Set to none to reset CC list.

        Returns:
            None
        """
        self.message.cc = self._build_recipients(cc)

    def attach(
        self,
        filename: str,
        contents: bytes,
        mimetype: Optional[str] = None,
    ) -> None:
        """
        Attach file to email.

        Args:
            filename:
                File name to use.
            contents:
                File contents.
            mimetype:
                If not provided, mimetype will be guessed from file name.

        See:
            `attach_file()`:
                To quickly attach file from path.

        Returns:
            None
        """
        if mimetype is None:
            mimetype = guess_mimetype(filename)

        self.message.attach(filename, contents, mimetype)

    def attach_file(self, path: PathLike) -> None:
        """
        Attach file to email from path.

        Args:
            path:
                Full path to file.

        See:
            `attach()`:
                For full control over file name and mimetype.

        Raises:
            SuspiciousFileOperation:
                If path not under allowed roots.

        Returns:
            None
        """
        path = allowed_path(path)
        self.message.attach_file(str(path))

    def render_body(self) -> str:
        """
        Render body template.

        Returns:
            Email body
        """
        body = render_to_string(self.template_name, self.context)
        return body

    def render_subject(self) -> str:
        """
        Render subject template.

        Returns:
            Plain-string subject.
        """
        # Render subject template
        context = Context(self.context)
        template = Template(self.subject)
        subject = str(template.render(context))

        # Add prefix
        prefix = self.subject_prefix
        if prefix is None:
            prefix = settings.EMAIL_SUBJECT_PREFIX
        if prefix:
            subject = f"{prefix} {subject}"

        return subject

    def pre_send(self) -> None:
        """
        Hook that is run just before email is sent.

        Can be used to modify message before it goes out. For example,
        to attach a file to the email from a model field:

            def pre_send(self):
                if self.object.attachment:
                    self.attach_file(self.object.attachment.path)

        """
        pass

    def post_send(self) -> None:
        """
        Hook that is run just after email is sent.

        Could be used to add logging or messages, eg.:

            def post_send(self):
                logger.info("Email sent to %s", self.object.recipient)
                messages.success(self.request, "Email successfully sent")

        """
        pass

    def send(self, to: Optional[Union[str, List[str]]] = None) -> None:
        """
        Send HTML email to given recipients.

        Args:
            to:
                Optional address (or addresses) to send email to.
                If not provided, the site's DEFAULT_FROM_EMAIL is used.
                Full name format supported, eg.
                "John Smith <jsmith@example.com>".

        See:
            `build_address()`:
                To build address string.

        Returns:
            None
        """
        # Prepare properties
        if to:
            self.message.to = self._build_recipients(to)
        html = self.render_body()
        self.message.body = html2text(html, maxlen=79)
        self.message.attach_alternative(html, 'text/html')
        self.message.subject = self.render_subject()

        # Send email
        self.pre_send()
        self.message.send()
        self.post_send()

    def _build_recipients(
        self,
        recipients: Optional[Union[str, List[str]]],
    ) -> List[str]:
        """
        Convert various reciptient types to a plain list of strings.

        Args:
            recipients:
                A single email address, a list of email addresses, or simple None.

        Returns:
            A plain (possibly empty) list of strings.
        """
        if recipients is None:
            return []
        elif isinstance(recipients, str):
            return [recipients]
        else:
            return list(recipients)

    def _get_context_object_name(self, obj: Optional[models.Model]) -> Optional[str]:
        """
        Get the name to use in our templates for the option model instance.

        The name 'object' is always used, but more friendly names can be
        used also.
        """
        if self.context_object_name:
            return self.context_object_name
        elif isinstance(obj, models.Model):
            return obj._meta.model_name
        else:
            return None
