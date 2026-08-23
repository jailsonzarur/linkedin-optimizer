from django.db import transaction

from knowledge.models import KnowledgeEntry, KnowledgeSource


class KnowledgeEntryBuilder:
    MAX_AUDIO_BYTES = 25 * 1024 * 1024
    ALLOWED_AUDIO_SUFFIXES = (".mp3", ".m4a", ".mp4", ".wav", ".webm", ".ogg", ".oga", ".flac")

    def __init__(self, user, title=""):
        self.user = user
        self.title = (title or "").strip()
        self.texts = []
        self.audios = []
        self.errors = []

    def add_text(self, content):
        content = (content or "").strip()
        if content:
            self.texts.append(content)

    def add_audio(self, uploaded_file):
        name = uploaded_file.name.lower()
        if not name.endswith(self.ALLOWED_AUDIO_SUFFIXES):
            self.errors.append(f"{uploaded_file.name}: unsupported audio format.")
            return
        if uploaded_file.size > self.MAX_AUDIO_BYTES:
            self.errors.append(f"{uploaded_file.name}: over the 25 MB limit.")
            return
        self.audios.append(uploaded_file)

    def is_valid(self):
        if not self.texts and not self.audios:
            self.errors.append("Add at least one text or audio block before saving.")
        return not self.errors

    @transaction.atomic
    def save(self):
        entry = KnowledgeEntry.objects.create(user=self.user, title=self.title)

        position = 0
        for text in self.texts:
            KnowledgeSource.objects.create(
                entry=entry,
                type=KnowledgeSource.SourceType.TEXT,
                content=text,
                status=KnowledgeSource.Status.DONE,
                position=position,
            )
            position += 1

        for audio in self.audios:
            KnowledgeSource.objects.create(
                entry=entry,
                type=KnowledgeSource.SourceType.AUDIO,
                audio_file=audio,
                status=KnowledgeSource.Status.PENDING,
                position=position,
            )
            position += 1

        entry.save(update_fields=["updated_at"])
        return entry
