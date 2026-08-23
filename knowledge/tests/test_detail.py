from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from knowledge.models import KnowledgeChunk, KnowledgeEntry, KnowledgeSource


class DetailAccessTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = get_user_model().objects.create_user(username="owner", password="a-long-password-1")
        cls.other = get_user_model().objects.create_user(username="other", password="a-long-password-1")
        cls.entry = KnowledgeEntry.objects.create(user=cls.owner, title="Mine")

    def url(self):
        return reverse("knowledge:detail", args=[self.entry.pk])

    def test_anonymous_is_redirected(self):
        response = self.client.get(self.url())
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)

    def test_owner_can_open_it(self):
        self.client.login(username="owner", password="a-long-password-1")
        self.assertEqual(self.client.get(self.url()).status_code, 200)

    def test_another_user_gets_404(self):
        self.client.login(username="other", password="a-long-password-1")
        self.assertEqual(self.client.get(self.url()).status_code, 404)


class DetailContentTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(username="owner", password="a-long-password-1")
        cls.entry = KnowledgeEntry.objects.create(
            user=cls.user, title="Mine", status=KnowledgeEntry.Status.READY
        )
        KnowledgeSource.objects.create(
            entry=cls.entry,
            type=KnowledgeSource.SourceType.TEXT,
            content="I built REST APIs.",
            status=KnowledgeSource.Status.DONE,
        )
        for category in ("experience", "skill"):
            KnowledgeChunk.objects.create(
                entry=cls.entry,
                user=cls.user,
                content=f"a {category} claim",
                category=category,
                embedding=[0.1] * 1536,
            )

    def setUp(self):
        self.client.login(username="owner", password="a-long-password-1")

    def test_transcript_and_chunks_are_rendered(self):
        body = self.client.get(reverse("knowledge:detail", args=[self.entry.pk])).content.decode()
        self.assertIn("I built REST APIs.", body)
        self.assertIn("a experience claim", body)
        self.assertIn("a skill claim", body)

    def test_settled_entry_does_not_poll(self):
        body = self.client.get(reverse("knowledge:detail", args=[self.entry.pk])).content.decode()
        self.assertNotIn("hx-trigger", body)

    def test_unfinished_entry_polls(self):
        KnowledgeEntry.objects.filter(pk=self.entry.pk).update(
            status=KnowledgeEntry.Status.PROCESSING
        )
        body = self.client.get(reverse("knowledge:detail", args=[self.entry.pk])).content.decode()
        self.assertIn('hx-trigger="every 3s"', body)


class SourceUpdateTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(username="owner", password="a-long-password-1")
        cls.other = get_user_model().objects.create_user(username="other", password="a-long-password-1")
        cls.entry = KnowledgeEntry.objects.create(
            user=cls.user, status=KnowledgeEntry.Status.READY
        )
        cls.source = KnowledgeSource.objects.create(
            entry=cls.entry,
            type=KnowledgeSource.SourceType.AUDIO,
            content="mis-heard transcript",
            status=KnowledgeSource.Status.DONE,
        )

    def url(self):
        return reverse("knowledge:source_update", args=[self.source.pk])

    def test_editing_saves_and_requeues_the_entry(self):
        self.client.login(username="owner", password="a-long-password-1")

        with patch("knowledge.views.entry_detail.process_entry") as task:
            # TestCase never commits, so on_commit callbacks need to be drained
            # explicitly — which is also proof the dispatch really is deferred.
            with self.captureOnCommitCallbacks(execute=True):
                response = self.client.post(self.url(), {"content": "corrected transcript"})

        self.assertRedirects(response, reverse("knowledge:detail", args=[self.entry.pk]))
        self.source.refresh_from_db()
        self.entry.refresh_from_db()
        self.assertEqual(self.source.content, "corrected transcript")
        self.assertEqual(self.entry.status, KnowledgeEntry.Status.PENDING)
        task.delay.assert_called_once_with(self.entry.pk)

    def test_another_user_cannot_edit(self):
        self.client.login(username="other", password="a-long-password-1")
        response = self.client.post(self.url(), {"content": "hijacked"})
        self.assertEqual(response.status_code, 404)
        self.source.refresh_from_db()
        self.assertEqual(self.source.content, "mis-heard transcript")

    def test_get_is_rejected(self):
        self.client.login(username="owner", password="a-long-password-1")
        self.assertEqual(self.client.get(self.url()).status_code, 405)


class ListPollingTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(username="owner", password="a-long-password-1")

    def setUp(self):
        self.client.login(username="owner", password="a-long-password-1")

    def test_list_polls_while_something_is_unfinished(self):
        KnowledgeEntry.objects.create(user=self.user, status=KnowledgeEntry.Status.PROCESSING)
        body = self.client.get(reverse("knowledge:list")).content.decode()
        self.assertIn('hx-trigger="every 3s"', body)

    def test_list_stops_polling_once_everything_settled(self):
        KnowledgeEntry.objects.create(user=self.user, status=KnowledgeEntry.Status.READY)
        body = self.client.get(reverse("knowledge:list")).content.decode()
        self.assertNotIn("hx-trigger", body)

    def test_body_fragment_excludes_other_users(self):
        KnowledgeEntry.objects.create(user=self.user, title="Mine")
        stranger = get_user_model().objects.create_user(username="stranger")
        KnowledgeEntry.objects.create(user=stranger, title="Theirs")

        body = self.client.get(reverse("knowledge:list_body")).content.decode()
        self.assertIn("Mine", body)
        self.assertNotIn("Theirs", body)

    def test_failed_entry_does_not_keep_the_list_polling(self):
        KnowledgeEntry.objects.create(user=self.user, status=KnowledgeEntry.Status.FAILED)
        body = self.client.get(reverse("knowledge:list")).content.decode()
        self.assertNotIn("hx-trigger", body)
        self.assertNotIn("still processing", body)

    def test_failed_detail_does_not_keep_polling(self):
        entry = KnowledgeEntry.objects.create(
            user=self.user, status=KnowledgeEntry.Status.FAILED
        )
        body = self.client.get(reverse("knowledge:detail", args=[entry.pk])).content.decode()
        self.assertNotIn("hx-trigger", body)

    def test_polling_fragment_carries_the_status_pill(self):
        entry = KnowledgeEntry.objects.create(
            user=self.user, title="Refreshing", status=KnowledgeEntry.Status.PROCESSING
        )
        body = self.client.get(
            reverse("knowledge:detail_body", args=[entry.pk])
        ).content.decode()
        self.assertIn("Refreshing", body)
        self.assertIn("processing", body)

    def test_list_fragment_carries_the_counter(self):
        KnowledgeEntry.objects.create(user=self.user, status=KnowledgeEntry.Status.PROCESSING)
        body = self.client.get(reverse("knowledge:list_body")).content.decode()
        self.assertIn("still processing", body)
