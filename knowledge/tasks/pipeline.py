import logging

from celery import chord, shared_task
from django.db import transaction

from knowledge.models import KnowledgeChunk, KnowledgeEntry, KnowledgeSource
from knowledge.services.chunker import Chunker
from knowledge.services.embedder import Embedder
from knowledge.services.transcriber import Transcriber

logger = logging.getLogger(__name__)

RETRY_KWARGS = {
    "autoretry_for": (Exception,),
    "retry_backoff": True,
    "retry_backoff_max": 300,
    "retry_jitter": True,
    "max_retries": 3,
}


@shared_task
def process_entry(entry_id):
    audio_ids = list(
        KnowledgeSource.objects.filter(
            entry_id=entry_id, type=KnowledgeSource.SourceType.AUDIO
        )
        .exclude(status=KnowledgeSource.Status.DONE)
        .values_list("id", flat=True)
    )

    KnowledgeEntry.objects.filter(pk=entry_id).update(
        status=KnowledgeEntry.Status.PROCESSING
    )

    if not audio_ids:
        finalize_entry.delay(entry_id)
        return

    chord(transcribe_source.s(source_id) for source_id in audio_ids)(
        finalize_entry.si(entry_id)
    )


@shared_task(bind=True, **RETRY_KWARGS)
def transcribe_source(self, source_id):
    source = KnowledgeSource.objects.get(pk=source_id)

    source.status = KnowledgeSource.Status.TRANSCRIBING
    source.save(update_fields=["status", "updated_at"])

    try:
        source.content = Transcriber().transcribe(source)
    except Exception as exc:
        if self.request.retries >= self.max_retries:
            KnowledgeSource.objects.filter(pk=source_id).update(
                status=KnowledgeSource.Status.FAILED
            )
            logger.exception("Transcription gave up on source %s", source_id)
            return source_id
        raise exc

    source.status = KnowledgeSource.Status.DONE
    source.save(update_fields=["content", "status", "updated_at"])
    return source_id


@shared_task(bind=True, **RETRY_KWARGS)
def finalize_entry(self, entry_id):
    entry = KnowledgeEntry.objects.get(pk=entry_id)
    sources = list(entry.sources.all())

    if any(source.status == KnowledgeSource.Status.FAILED for source in sources):
        entry.status = KnowledgeEntry.Status.FAILED
        entry.save(update_fields=["status", "updated_at"])
        return

    contents = [source.content for source in sources if source.content.strip()]
    if not contents:
        entry.status = KnowledgeEntry.Status.READY
        entry.save(update_fields=["status", "updated_at"])
        return

    try:
        extracted = Chunker().extract(contents)
        vectors = Embedder().embed([chunk["content"] for chunk in extracted]) if extracted else []
    except Exception as exc:
        if self.request.retries >= self.max_retries:
            entry.status = KnowledgeEntry.Status.FAILED
            entry.save(update_fields=["status", "updated_at"])
            logger.exception("Extraction gave up on entry %s", entry_id)
            return
        raise exc

    with transaction.atomic():
        # Rebuilding from scratch keeps a retry or an edited transcript from
        # stacking duplicates onto what a previous run already wrote.
        entry.chunks.all().delete()
        KnowledgeChunk.objects.bulk_create(
            [
                KnowledgeChunk(
                    entry=entry,
                    user_id=entry.user_id,
                    content=chunk["content"],
                    category=chunk["category"],
                    embedding=vector,
                )
                for chunk, vector in zip(extracted, vectors)
            ]
        )
        entry.status = KnowledgeEntry.Status.READY
        entry.save(update_fields=["status", "updated_at"])

    discard_audio.delay(entry_id)


@shared_task
def discard_audio(entry_id):
    for source in KnowledgeSource.objects.filter(
        entry_id=entry_id,
        type=KnowledgeSource.SourceType.AUDIO,
        status=KnowledgeSource.Status.DONE,
    ).exclude(audio_file=""):
        try:
            source.audio_file.delete(save=False)
        except Exception:
            logger.exception("Could not delete audio for source %s", source.pk)
            continue
        source.audio_file = None
        source.save(update_fields=["audio_file", "updated_at"])
