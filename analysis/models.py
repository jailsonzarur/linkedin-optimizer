from django.conf import settings
from django.db import models


class Analysis(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        RUNNING = "running", "Running"
        DONE = "done", "Done"
        FAILED = "failed", "Failed"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="analyses")
    profile_import = models.ForeignKey("knowledge.ProfileImport", on_delete=models.CASCADE, related_name="analyses")
    overall_score = models.PositiveSmallIntegerField(null=True, blank=True)
    overall_score_per_section = models.JSONField(default=dict)
    keyword_gap = models.JSONField(default=list)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "analyses"

    def __str__(self):
        return f"Analysis #{self.pk} — {self.user}"


class AnalysisSection(models.Model):
    class Section(models.TextChoices):
        HEADLINE = "headline", "Headline"
        ABOUT = "about", "About"
        EXPERIENCE_BULLET = "experience_bullet", "Experience bullet"

    analysis = models.ForeignKey(Analysis, on_delete=models.CASCADE, related_name="sections")
    section = models.CharField(max_length=30, choices=Section.choices)
    original_text = models.TextField()
    suggested_text = models.TextField()
    variant_index = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["analysis", "section", "variant_index"]

    def __str__(self):
        return f"{self.get_section_display()} (variant {self.variant_index})"
