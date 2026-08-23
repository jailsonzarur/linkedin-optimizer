from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class SignupTests(TestCase):
    def test_creates_user_and_logs_in(self):
        response = self.client.post(
            reverse("accounts:signup"),
            {
                "username": "novato",
                "email": "novato@example.com",
                "password1": "uma-senha-bem-longa-123",
                "password2": "uma-senha-bem-longa-123",
            },
        )
        self.assertRedirects(response, reverse("knowledge:onboarding_start"))
        user = get_user_model().objects.get(username="novato")
        self.assertEqual(user.email, "novato@example.com")
        self.assertEqual(self.client.session["_auth_user_id"], str(user.pk))

    def test_duplicate_email_is_rejected(self):
        get_user_model().objects.create_user(username="antigo", email="dup@example.com")
        response = self.client.post(
            reverse("accounts:signup"),
            {
                "username": "novo",
                "email": "DUP@example.com",
                "password1": "uma-senha-bem-longa-123",
                "password2": "uma-senha-bem-longa-123",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(get_user_model().objects.filter(username="novo").exists())

    def test_authenticated_user_is_redirected_away(self):
        get_user_model().objects.create_user(username="logado", password="senha-longa-123")
        self.client.login(username="logado", password="senha-longa-123")
        response = self.client.get(reverse("accounts:signup"))
        self.assertRedirects(response, reverse("accounts:home"))


class LoginTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="rafael", password="senha-bem-longa-123"
        )

    def test_valid_credentials_land_on_home(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "rafael", "password": "senha-bem-longa-123"},
        )
        self.assertRedirects(response, reverse("accounts:home"))

    def test_invalid_credentials_stay_on_the_form(self):
        response = self.client.post(
            reverse("accounts:login"), {"username": "rafael", "password": "errada"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_logout_returns_to_login(self):
        self.client.login(username="rafael", password="senha-bem-longa-123")
        response = self.client.post(reverse("accounts:logout"))
        self.assertRedirects(response, reverse("accounts:login"))


class HomeAccessTests(TestCase):
    def test_anonymous_is_redirected_to_login(self):
        response = self.client.get(reverse("accounts:home"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)

    def test_authenticated_user_sees_home(self):
        get_user_model().objects.create_user(username="rafael", password="senha-longa-123")
        self.client.login(username="rafael", password="senha-longa-123")
        response = self.client.get(reverse("accounts:home"))
        self.assertEqual(response.status_code, 200)


class SignupFormRenderTests(TestCase):
    def test_password_help_is_condensed_not_the_django_default(self):
        response = self.client.get(reverse("accounts:signup"))
        body = response.content.decode()
        self.assertIn("At least 8 characters", body)
        self.assertNotIn("too similar to", body)

    def test_confirmation_field_has_no_help_text(self):
        response = self.client.get(reverse("accounts:signup"))
        self.assertNotIn("Enter the same password as before", response.content.decode())
