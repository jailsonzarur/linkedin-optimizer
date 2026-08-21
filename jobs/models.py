from django.db import models
from pgvector.django import VectorField


class TargetRoleCatalog(models.Model):
    role_name = models.CharField(max_length=255, unique=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["role_name"]

    def __str__(self):
        return self.role_name


class JobPosting(models.Model):
    source_url = models.URLField(unique=True)
    target_role = models.CharField(max_length=255)
    raw_text = models.TextField()
    embedding = VectorField(dimensions=1536)
    collected_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-collected_at"]

    def __str__(self):
        return f"{self.target_role} — {self.source_url}"
