from django.conf import settings
from django.db import models
from pgvector.django import VectorField


class IdentityVariation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="identity_variations")
    text = models.TextField()
    embedding = VectorField(dimensions=1536)
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-generated_at"]

    def __str__(self):
        return self.text
