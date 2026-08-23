from django.conf import settings

from knowledge.services.openai_client import get_client


class Transcriber:
    def __init__(self, client=None, model=None):
        self._client = client
        self.model = model or settings.OPENAI_TRANSCRIBE_MODEL

    @property
    def client(self):
        if self._client is None:
            self._client = get_client()
        return self._client

    def transcribe(self, source):
        if not source.audio_file:
            return ""

        with source.audio_file.open("rb") as handle:
            response = self.client.audio.transcriptions.create(
                model=self.model,
                file=(source.audio_file.name, handle),
            )

        return (response.text or "").strip()
