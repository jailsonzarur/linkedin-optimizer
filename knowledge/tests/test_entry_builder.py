from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from knowledge.models import KnowledgeEntry, KnowledgeSource
from knowledge.services.entry_builder import KnowledgeEntryBuilder


class KnowledgeEntryBuilderTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(username="tester")

    def audio(self, name="speech.mp3", size=1024):
        return SimpleUploadedFile(name, b"x" * size, content_type="audio/mpeg")

    def test_empty_submission_is_invalid(self):
        builder = KnowledgeEntryBuilder(self.user)
        self.assertFalse(builder.is_valid())

    def test_blank_text_is_ignored(self):
        builder = KnowledgeEntryBuilder(self.user)
        builder.add_text("   ")
        self.assertFalse(builder.is_valid())

    def test_each_block_becomes_its_own_source(self):
        builder = KnowledgeEntryBuilder(self.user, title="TechCorp")
        builder.add_text("first")
        builder.add_text("second")
        builder.add_audio(self.audio())
        self.assertTrue(builder.is_valid())

        entry = builder.save()
        self.assertEqual(entry.sources.count(), 3)
        self.assertEqual(entry.sources.filter(type=KnowledgeSource.SourceType.TEXT).count(), 2)
        self.assertEqual(entry.sources.filter(type=KnowledgeSource.SourceType.AUDIO).count(), 1)

    def test_entry_starts_pending_until_extraction_runs(self):
        builder = KnowledgeEntryBuilder(self.user)
        builder.add_text("no audio at all")
        entry = builder.save()
        self.assertEqual(entry.status, KnowledgeEntry.Status.PENDING)

    def test_text_source_needs_no_transcription(self):
        builder = KnowledgeEntryBuilder(self.user)
        builder.add_text("already written down")
        source = builder.save().sources.get()
        self.assertEqual(source.status, KnowledgeSource.Status.DONE)

    def test_entry_with_audio_waits_for_transcription(self):
        builder = KnowledgeEntryBuilder(self.user)
        builder.add_audio(self.audio())
        entry = builder.save()
        source = entry.sources.get()
        self.assertEqual(source.status, KnowledgeSource.Status.PENDING)
        self.assertEqual(source.content, "")

    def test_oversized_audio_is_rejected(self):
        builder = KnowledgeEntryBuilder(self.user)
        builder.add_audio(self.audio(size=KnowledgeEntryBuilder.MAX_AUDIO_BYTES + 1))
        self.assertFalse(builder.is_valid())
        self.assertIn("25 MB", builder.errors[0])

    def test_unsupported_extension_is_rejected(self):
        builder = KnowledgeEntryBuilder(self.user)
        builder.add_audio(SimpleUploadedFile("resume.exe", b"x", content_type="audio/mpeg"))
        self.assertFalse(builder.is_valid())

    def test_positions_are_sequential(self):
        builder = KnowledgeEntryBuilder(self.user)
        builder.add_text("a")
        builder.add_audio(self.audio())
        entry = builder.save()
        self.assertEqual(list(entry.sources.values_list("position", flat=True)), [0, 1])
