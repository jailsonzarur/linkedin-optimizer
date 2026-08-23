from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from analysis.models import Analysis, ProfileSnapshot


class AnalysisResultAccessTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = get_user_model().objects.create_user(
            username="owner", password="senha-bem-longa-123"
        )
        cls.intruder = get_user_model().objects.create_user(
            username="intruder", password="senha-bem-longa-123"
        )
        snapshot = ProfileSnapshot.objects.create(user=cls.owner, raw_content="profile")
        cls.analysis = Analysis.objects.create(
            user=cls.owner, profile_snapshot=snapshot, overall_score=68
        )

    def url(self):
        return reverse("analysis:result", args=[self.analysis.pk])

    def test_anonymous_is_redirected_to_login(self):
        response = self.client.get(self.url())
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)

    def test_owner_can_see_the_analysis(self):
        self.client.login(username="owner", password="senha-bem-longa-123")
        self.assertEqual(self.client.get(self.url()).status_code, 200)

    def test_another_user_gets_404(self):
        self.client.login(username="intruder", password="senha-bem-longa-123")
        self.assertEqual(self.client.get(self.url()).status_code, 404)
