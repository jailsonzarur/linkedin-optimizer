from django.conf import settings
from django.db import models
from pgvector.django import VectorField


class KnowledgeSource(models.Model):
    class SourceType(models.TextChoices):
        AUDIO = "audio", "Audio"
        TEXT = "text", "Text"
        RESUME_PDF = "resume_pdf", "Resume PDF"
        LINKEDIN_EXPORT = "linkedin_export", "LinkedIn export"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        TRANSCRIBING = "transcribing", "Transcribing"
        PROCESSING = "processing", "Processing"
        DONE = "done", "Done"
        FAILED = "failed", "Failed"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="knowledge_sources")
    type = models.CharField(max_length=20, choices=SourceType.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_type_display()} — {self.user}"


class KnowledgeChunk(models.Model):
    class Category(models.TextChoices):
        EXPERIENCE = "experience", "Experience"
        SKILL = "skill", "Skill"
        ACHIEVEMENT = "achievement", "Achievement"
        EDUCATION = "education", "Education"
        OTHER = "other", "Other"

    source = models.ForeignKey(KnowledgeSource, on_delete=models.CASCADE, related_name="chunks")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="knowledge_chunks")
    content = models.TextField()
    category = models.CharField(max_length=20, choices=Category.choices)
    embedding = VectorField(dimensions=1536)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.content[:50]
