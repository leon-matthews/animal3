
from typing import Any, Dict
import warnings

from django.db import transaction
from django.http import HttpRequest, HttpResponse
from django.views.generic import TemplateView

from braces.views import StaffuserRequiredMixin

from ..utils.email import HtmlEmail

__all__ = (
    'AdminEmailPreview',
    'AdminPreviewEmail',
)


class AdminEmailPreview(
    StaffuserRequiredMixin,                                 # type: ignore[no-any-unimported]
    TemplateView,
):
    """
    Show admin a preview of the what the email to be sent would look like.

    Override this class, provide values to class attributes, then override
    `get_email_context()` to pass context to email.

    Any database writes are rolled-back at the end of the request.

    Attributes:
        email_class:
            The HtmlEmail subclass to use.
        model:
            Primary Django model for email. Used by admin for its breadcrumbs.
        template_name:
            Path to HTML template. Usually shared among all users of base class.
        title:
            Admin title to use.

    """
    template_name = 'admin/preview_email.html'
    title: str = 'Email Preview'

    def build_email(self, request: HttpRequest) -> HtmlEmail:
        """
        Hook for subclasses to build an HtmlEmail instance.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} class requires a build_email() method"
        )

    def get(
        self,
        request: HttpRequest,
        *args: Any,
        **kwargs: Any
    ) -> HttpResponse:
        """
        Wrap GET handler is a database transaction and roll it back.
        """
        self.email = self.build_email(request)
        with transaction.atomic():
            response = super().get(request, *args, **kwargs)
            transaction.set_rollback(True)
        return response

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Build context for admin template.
        """
        # Context for admin breadcrumbs.
        context = super().get_context_data(**kwargs)
        context.update({
            'bcc': self.email.message.bcc,
            'body': self.email.render_body(),
            'cc': self.email.message.cc,
            'from_email': self.email.message.from_email,
            'has_permission': True,
            'object_meta': self.email.object._meta if self.email.object else None,
            'site_url': '/',
            'subject': self.email.render_subject(),
            'title': self.title,
            'to': self.email.message.to,
        })
        return context


class AdminPreviewEmail(AdminEmailPreview):
    def __init_subclass__(cls, **kwargs: Any):
        # Deprecated: 2022-12-17
        message = "AdminPreviewEmail has been renamed to AdminEmailPreview"
        warnings.warn(message, DeprecationWarning, stacklevel=2)
        super().__init_subclass__(**kwargs)
