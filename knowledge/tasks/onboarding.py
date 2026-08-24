import logging

from celery import shared_task
from django.db import transaction

from knowledge.models import Conversation, Message, ProfileImport
from knowledge.services.events import publish
from knowledge.services.conversation import opening_question
from knowledge.services.judge import ProfileJudge
from knowledge.services.pdf import ExtractionError, extract_text

logger = logging.getLogger(__name__)


def _fail(profile_import, message):
    profile_import.status = ProfileImport.Status.FAILED
    profile_import.error = message
    profile_import.save(update_fields=["status", "error", "updated_at"])
    publish(profile_import.pk, "failed", message)


@shared_task
def extract_import(import_id):
    profile_import = ProfileImport.objects.get(pk=import_id)

    profile_import.status = ProfileImport.Status.EXTRACTING
    profile_import.save(update_fields=["status", "updated_at"])
    publish(import_id, "extract.started", "")

    try:
        profile_import.linkedin_text = extract_text(profile_import.linkedin_pdf)
    except ExtractionError as exc:
        _fail(profile_import, str(exc))
        return
    publish(import_id, "extract.profile", len(profile_import.linkedin_text))

    if profile_import.resume:
        try:
            profile_import.resume_text = extract_text(profile_import.resume)
            publish(import_id, "extract.resume", len(profile_import.resume_text))
        except ExtractionError as exc:
            profile_import.error = f"Résumé skipped: {exc}"
            publish(import_id, "extract.resume_skipped", str(exc))

    profile_import.save(update_fields=["linkedin_text", "resume_text", "error", "updated_at"])
    judge_import.delay(import_id)


@shared_task
def judge_import(import_id):
    profile_import = ProfileImport.objects.get(pk=import_id)

    profile_import.status = ProfileImport.Status.JUDGING
    profile_import.save(update_fields=["status", "updated_at"])
    publish(import_id, "judge.started", "")

    emit = lambda name, detail: publish(import_id, name, detail)

    try:
        record = ProfileJudge(on_event=emit).run(
            profile_import.linkedin_text, profile_import.resume_text
        )
    except Exception:
        logger.exception("Unexpected failure judging import %s", import_id)
        _fail(profile_import, "Something went wrong analysing that profile.")
        return

    with transaction.atomic():
        profile_import.judgment = record
        profile_import.status = ProfileImport.Status.READY
        profile_import.save(update_fields=["judgment", "status", "updated_at"])

        conversation = Conversation.objects.create(
            user=profile_import.user,
            profile_import=profile_import,
            record=record,
        )

    try:
        Message.objects.create(
            conversation=conversation,
            role=Message.Role.ASSISTANT,
            content=opening_question(record),
            status=Message.Status.DONE,
        )
    except Exception:
        logger.exception("Could not generate the opening question for %s", conversation.pk)

    publish(import_id, "conversation.ready", conversation.pk)
    publish(import_id, "done", conversation.pk)
