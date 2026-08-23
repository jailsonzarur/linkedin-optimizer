from django.conf import settings
from django.db import models


class ProfileImport(models.Model):

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        EXTRACTING = "extracting", "Extracting"
        JUDGING = "judging", "Judging"
        READY = "ready", "Ready"
        FAILED = "failed", "Failed"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile_imports")
    linkedin_pdf = models.FileField(upload_to="imports/%Y/%m/")
    resume = models.FileField(upload_to="imports/%Y/%m/", null=True, blank=True)
    linkedin_text = models.TextField(blank=True)
    resume_text = models.TextField(blank=True)
    judgment = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Import #{self.pk} — {self.user}"


class Conversation(models.Model):

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"
        ABANDONED = "abandoned", "Abandoned"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="conversations")
    profile_import = models.ForeignKey(ProfileImport, on_delete=models.CASCADE, related_name="conversations")
    record = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Conversation #{self.pk} — {self.user}"


class Message(models.Model):
    class Role(models.TextChoices):
        ASSISTANT = "assistant", "Assistant"
        USER = "user", "User"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        TRANSCRIBING = "transcribing", "Transcribing"
        DONE = "done", "Done"
        FAILED = "failed", "Failed"

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=20, choices=Role.choices)
    content = models.TextField(blank=True)
    audio_file = models.FileField(upload_to="answers/%Y/%m/", null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DONE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.get_role_display()}: {self.content[:50]}"
