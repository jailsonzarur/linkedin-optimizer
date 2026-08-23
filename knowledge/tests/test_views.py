from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from knowledge.models import KnowledgeEntry


class KnowledgeAccessTests(TestCase):
    def test_list_requires_login(self):
        response = self.client.get(reverse("knowledge:list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)

    def test_create_requires_login(self):
        response = self.client.get(reverse("knowledge:create"))
        self.assertEqual(response.status_code, 302)


class KnowledgeListTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = get_user_model().objects.create_user(username="owner", password="senha-longa-123")
        cls.other = get_user_model().objects.create_user(username="other", password="senha-longa-123")
        KnowledgeEntry.objects.create(user=cls.owner, title="My entry")
        KnowledgeEntry.objects.create(user=cls.other, title="Someone else entry")

    def test_only_own_entries_are_listed(self):
        self.client.login(username="owner", password="senha-longa-123")
        response = self.client.get(reverse("knowledge:list"))
        body = response.content.decode()
        self.assertIn("My entry", body)
        self.assertNotIn("Someone else entry", body)


class KnowledgeCreateTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(username="owner", password="senha-longa-123")

    def setUp(self):
        self.client.login(username="owner", password="senha-longa-123")

    def test_submitting_text_and_audio_creates_one_entry(self):
        response = self.client.post(
            reverse("knowledge:create"),
            {
                "title": "TechCorp",
                "text_content": ["first block", "second block"],
                "audio_files": SimpleUploadedFile("speech.mp3", b"abc", content_type="audio/mpeg"),
            },
        )
        self.assertRedirects(response, reverse("knowledge:list"))
        entry = KnowledgeEntry.objects.get(user=self.user)
        self.assertEqual(entry.title, "TechCorp")
        self.assertEqual(entry.sources.count(), 3)

    def test_empty_submission_is_rejected(self):
        response = self.client.post(reverse("knowledge:create"), {"title": "empty"})
        self.assertEqual(response.status_code, 400)
        self.assertFalse(KnowledgeEntry.objects.exists())
