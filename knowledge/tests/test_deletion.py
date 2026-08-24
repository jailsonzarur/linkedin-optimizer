import io

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from analysis.models import Analysis, AnalysisBullet, AnalysisSection
from knowledge.models import Conversation, Message, ProfileImport


def a_pdf(name="p.pdf"):
    return SimpleUploadedFile(name, b"%PDF-1.4 test", content_type="application/pdf")


class ImportUniquenessTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(username="owner")

    def test_a_user_cannot_hold_two_imports(self):
        ProfileImport.objects.create(user=self.user, linkedin_pdf=a_pdf())
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                ProfileImport.objects.create(user=self.user, linkedin_pdf=a_pdf("q.pdf"))

    def test_two_users_may_each_hold_one(self):
        other = get_user_model().objects.create_user(username="other")
        ProfileImport.objects.create(user=self.user, linkedin_pdf=a_pdf())
        ProfileImport.objects.create(user=other, linkedin_pdf=a_pdf("q.pdf"))
        self.assertEqual(ProfileImport.objects.count(), 2)


class CascadeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(username="owner")
        cls.profile_import = ProfileImport.objects.create(user=cls.user, linkedin_pdf=a_pdf())
        conversation = Conversation.objects.create(
            user=cls.user, profile_import=cls.profile_import
        )
        Message.objects.create(conversation=conversation, role=Message.Role.USER, content="hi")
        analysis = Analysis.objects.create(user=cls.user, profile_import=cls.profile_import)
        section = AnalysisSection.objects.create(
            analysis=analysis, section=AnalysisSection.Section.HEADLINE,
            original_text="a", suggested_text="b",
        )
        AnalysisBullet.objects.create(
            section=section, kind=AnalysisBullet.Kind.ORIGINAL, text="one"
        )

    def test_deleting_the_import_clears_everything_below_it(self):
        self.profile_import.delete()
        self.assertFalse(Conversation.objects.exists())
        self.assertFalse(Message.objects.exists())
        self.assertFalse(Analysis.objects.exists())
        self.assertFalse(AnalysisSection.objects.exists())
        self.assertFalse(AnalysisBullet.objects.exists())


class FileCleanupTests(TestCase):
    def test_the_pdfs_go_with_the_row(self):
        user = get_user_model().objects.create_user(username="owner")
        profile_import = ProfileImport.objects.create(
            user=user, linkedin_pdf=a_pdf(), resume=a_pdf("cv.pdf")
        )
        storage = profile_import.linkedin_pdf.storage
        paths = [profile_import.linkedin_pdf.name, profile_import.resume.name]
        self.assertTrue(all(storage.exists(path) for path in paths))

        profile_import.delete()
        self.assertFalse(any(storage.exists(path) for path in paths))

    def test_recorded_audio_goes_with_its_message(self):
        user = get_user_model().objects.create_user(username="owner")
        profile_import = ProfileImport.objects.create(user=user, linkedin_pdf=a_pdf())
        conversation = Conversation.objects.create(user=user, profile_import=profile_import)
        message = Message.objects.create(
            conversation=conversation,
            role=Message.Role.USER,
            audio_file=SimpleUploadedFile("a.webm", b"audio", content_type="audio/webm"),
        )
        storage, path = message.audio_file.storage, message.audio_file.name
        self.assertTrue(storage.exists(path))

        message.delete()
        self.assertFalse(storage.exists(path))


class ClearViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="owner", password="a-long-password-1"
        )
        cls.other = get_user_model().objects.create_user(
            username="other", password="a-long-password-1"
        )
        ProfileImport.objects.create(user=cls.user, linkedin_pdf=a_pdf())
        ProfileImport.objects.create(user=cls.other, linkedin_pdf=a_pdf("q.pdf"))

    def test_clearing_only_touches_your_own(self):
        self.client.login(username="owner", password="a-long-password-1")
        self.client.post(reverse("knowledge:import_clear"))
        self.assertFalse(ProfileImport.objects.filter(user=self.user).exists())
        self.assertTrue(ProfileImport.objects.filter(user=self.other).exists())

    def test_anonymous_cannot_clear(self):
        response = self.client.post(reverse("knowledge:import_clear"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ProfileImport.objects.count(), 2)
