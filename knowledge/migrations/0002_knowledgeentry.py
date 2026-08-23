import django.db.models.deletion
import pgvector.django.vector
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("knowledge", "0001_initial"),
    ]

    operations = [
        migrations.DeleteModel(name="KnowledgeChunk"),
        migrations.DeleteModel(name="KnowledgeSource"),
        migrations.CreateModel(
            name="KnowledgeEntry",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(blank=True, max_length=120)),
                ("status", models.CharField(choices=[("pending", "Pending"), ("processing", "Processing"), ("ready", "Ready"), ("failed", "Failed")], default="pending", max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="knowledge_entries", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"], "verbose_name_plural": "knowledge entries"},
        ),
        migrations.CreateModel(
            name="KnowledgeSource",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("type", models.CharField(choices=[("audio", "Audio"), ("text", "Text"), ("resume_pdf", "Resume PDF"), ("linkedin_export", "LinkedIn export")], max_length=20)),
                ("content", models.TextField(blank=True)),
                ("audio_file", models.FileField(blank=True, null=True, upload_to="knowledge/audio/%Y/%m/")),
                ("status", models.CharField(choices=[("pending", "Pending"), ("transcribing", "Transcribing"), ("processing", "Processing"), ("done", "Done"), ("failed", "Failed")], default="pending", max_length=20)),
                ("position", models.PositiveSmallIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("entry", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="sources", to="knowledge.knowledgeentry")),
            ],
            options={"ordering": ["entry", "position", "created_at"]},
        ),
        migrations.CreateModel(
            name="KnowledgeChunk",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("content", models.TextField()),
                ("category", models.CharField(choices=[("experience", "Experience"), ("skill", "Skill"), ("achievement", "Achievement"), ("education", "Education"), ("other", "Other")], max_length=20)),
                ("embedding", pgvector.django.vector.VectorField(dimensions=1536)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("source", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="chunks", to="knowledge.knowledgesource")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="knowledge_chunks", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
