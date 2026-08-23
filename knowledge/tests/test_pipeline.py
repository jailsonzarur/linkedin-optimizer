from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from knowledge.models import KnowledgeChunk, KnowledgeEntry, KnowledgeSource
from knowledge.tasks.pipeline import finalize_entry, process_entry, transcribe_source


def make_entry(user, texts=(), audios=0):
    entry = KnowledgeEntry.objects.create(user=user)
    position = 0
    for text in texts:
        KnowledgeSource.objects.create(
            entry=entry,
            type=KnowledgeSource.SourceType.TEXT,
            content=text,
            status=KnowledgeSource.Status.DONE,
            position=position,
        )
        position += 1
    for index in range(audios):
        KnowledgeSource.objects.create(
            entry=entry,
            type=KnowledgeSource.SourceType.AUDIO,
            audio_file=SimpleUploadedFile(f"clip{index}.mp3", b"xyz", content_type="audio/mpeg"),
            status=KnowledgeSource.Status.PENDING,
            position=position,
        )
        position += 1
    return entry


class TranscribeSourceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(username="tester")

    def test_transcript_lands_on_the_source(self):
        entry = make_entry(self.user, audios=1)
        source = entry.sources.get()

        with patch("knowledge.tasks.pipeline.Transcriber") as transcriber:
            transcriber.return_value.transcribe.return_value = "I built REST APIs."
            transcribe_source(source.pk)

        source.refresh_from_db()
        self.assertEqual(source.content, "I built REST APIs.")
        self.assertEqual(source.status, KnowledgeSource.Status.DONE)

    def test_source_is_marked_failed_once_retries_run_out(self):
        entry = make_entry(self.user, audios=1)
        source = entry.sources.get()

        with patch("knowledge.tasks.pipeline.Transcriber") as transcriber:
            transcriber.return_value.transcribe.side_effect = RuntimeError("api down")
            with patch.object(transcribe_source, "max_retries", 0):
                transcribe_source(source.pk)

        source.refresh_from_db()
        self.assertEqual(source.status, KnowledgeSource.Status.FAILED)


class FinalizeEntryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(username="tester")

    def run_finalize(self, entry, extracted):
        with (
            patch("knowledge.tasks.pipeline.Chunker") as chunker,
            patch("knowledge.tasks.pipeline.Embedder") as embedder,
            patch("knowledge.tasks.pipeline.discard_audio"),
        ):
            chunker.return_value.extract.return_value = extracted
            embedder.return_value.embed.return_value = [[0.1] * 1536 for _ in extracted]
            finalize_entry(entry.pk)
            return chunker.return_value.extract

    def test_every_source_content_reaches_one_extraction_call(self):
        entry = make_entry(self.user, texts=["first story", "second story"])
        extract = self.run_finalize(entry, [{"content": "a claim", "category": "skill"}])

        extract.assert_called_once()
        self.assertEqual(extract.call_args.args[0], ["first story", "second story"])

    def test_chunks_are_saved_against_the_entry(self):
        entry = make_entry(self.user, texts=["a story"])
        self.run_finalize(
            entry,
            [
                {"content": "Built REST APIs", "category": "experience"},
                {"content": "Django", "category": "skill"},
            ],
        )

        entry.refresh_from_db()
        self.assertEqual(entry.status, KnowledgeEntry.Status.READY)
        self.assertEqual(entry.chunks.count(), 2)
        self.assertEqual(KnowledgeChunk.objects.filter(user=self.user).count(), 2)

    def test_rerunning_replaces_chunks_instead_of_duplicating(self):
        entry = make_entry(self.user, texts=["a story"])
        payload = [{"content": "Built REST APIs", "category": "experience"}]

        self.run_finalize(entry, payload)
        self.run_finalize(entry, payload)

        self.assertEqual(entry.chunks.count(), 1)

    def test_a_failed_source_fails_the_entry(self):
        entry = make_entry(self.user, audios=1)
        entry.sources.update(status=KnowledgeSource.Status.FAILED)

        finalize_entry(entry.pk)

        entry.refresh_from_db()
        self.assertEqual(entry.status, KnowledgeEntry.Status.FAILED)


class ProcessEntryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(username="tester")

    def test_text_only_entry_skips_the_chord(self):
        entry = make_entry(self.user, texts=["only text"])

        with (
            patch("knowledge.tasks.pipeline.chord") as chord,
            patch("knowledge.tasks.pipeline.finalize_entry") as finalize,
        ):
            process_entry(entry.pk)

        chord.assert_not_called()
        finalize.delay.assert_called_once_with(entry.pk)

    def test_audio_entry_fans_out_through_a_chord(self):
        entry = make_entry(self.user, texts=["some text"], audios=2)

        with patch("knowledge.tasks.pipeline.chord") as chord:
            process_entry(entry.pk)

        chord.assert_called_once()
        entry.refresh_from_db()
        self.assertEqual(entry.status, KnowledgeEntry.Status.PROCESSING)

    def test_already_transcribed_audio_is_not_queued_again(self):
        entry = make_entry(self.user, audios=2)
        entry.sources.update(status=KnowledgeSource.Status.DONE)

        with (
            patch("knowledge.tasks.pipeline.chord") as chord,
            patch("knowledge.tasks.pipeline.finalize_entry") as finalize,
        ):
            process_entry(entry.pk)

        chord.assert_not_called()
        finalize.delay.assert_called_once_with(entry.pk)
