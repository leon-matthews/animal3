
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpRequest
from django.test import TestCase
from django.urls import reverse

from animal3.utils.email import HtmlEmail
from animal3.utils.testing import GET

from ..admin import AdminEmailPreview


User = get_user_model()


class SampleEmail(HtmlEmail):
    subject = "Sample Email"
    template_name = "common/email_base.html"


class SampleView(AdminEmailPreview):
    def build_email(self, request: HttpRequest) -> HtmlEmail:
        return SampleEmail(request)


class AdminEmailPreviewTest(TestCase):
    login_redirect = f"{reverse(settings.LOGIN_URL)}?next=/"
    staff_user: User
    user: User

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = User.objects.create_user('user', 'user@example.com')
        cls.staff_user = User.objects.create_user(
            'staff', 'staff@example.com', is_staff=True,
        )

    def test_base_class_error(self) -> None:
        """
        Cannot use base class directly.
        """
        message = r"^AdminEmailPreview class requires a build_email\(\) method$"
        with self.assertRaisesRegex(NotImplementedError, message):
            GET(AdminEmailPreview, user=self.staff_user)

    def test_not_logged_in(self) -> None:
        """
        Anonymous users should be redirected to login form.
        """
        response = GET(SampleView)
        self.assertEqual(response.status_code, 302)
        assert hasattr(response, 'url'), "Response missing 'url' attribute"
        self.assertEqual(response.url, self.login_redirect)

    def test_user_logged_in(self) -> None:
        """
        Ordinary users should be redirected to login form.
        """
        response = GET(SampleView, user=self.user)
        self.assertEqual(response.status_code, 302)
        assert hasattr(response, 'url'), "Response missing 'url' attribute"
        self.assertEqual(response.url, self.login_redirect)

    def test_staff_logged_in(self) -> None:
        """
        Staff users can see admin preview of HTML email.
        """
        response = GET(SampleView, user=self.staff_user)
        self.assertEqual(response.status_code, 200)
