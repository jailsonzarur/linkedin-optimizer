import logging

from celery import shared_task

from knowledge.models import Message
from knowledge.services.transcriber import Transcriber

logger = logging.getLogger(__name__)


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True,
             retry_backoff_max=120, max_retries=2)
def transcribe_message(self, message_id):
    message = Message.objects.get(pk=message_id)

    message.status = Message.Status.TRANSCRIBING
    message.save(update_fields=["status"])

    try:
        message.content = Transcriber().transcribe(message)
    except Exception as exc:
        if self.request.retries >= self.max_retries:
            Message.objects.filter(pk=message_id).update(status=Message.Status.FAILED)
            logger.exception("Transcription gave up on message %s", message_id)
            return message_id
        raise exc

    message.status = Message.Status.DONE
    message.save(update_fields=["content", "status"])

    if message.audio_file:
        try:
            message.audio_file.delete(save=False)
        except Exception:
            logger.exception("Could not delete audio for message %s", message_id)
        else:
            message.audio_file = None
            message.save(update_fields=["audio_file"])

    return message_id
