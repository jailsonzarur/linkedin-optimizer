import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("knowledge", "0003_chunk_points_at_entry"),
    ]

    operations = [
        migrations.DeleteModel(name="KnowledgeChunk"),
        migrations.DeleteModel(name="KnowledgeSource"),
        migrations.DeleteModel(name="KnowledgeEntry"),
        migrations.CreateModel(
            name="ProfileImport",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("source", models.CharField(choices=[("linkedin_url", "LinkedIn URL"), ("linkedin_pdf", "LinkedIn PDF export"), ("resume", "Résumé")], max_length=20)),
                ("source_url", models.URLField(blank=True)),
                ("file", models.FileField(blank=True, null=True, upload_to="imports/%Y/%m/")),
                ("raw_text", models.TextField(blank=True)),
                ("judgment", models.JSONField(blank=True, default=dict)),
                ("status", models.CharField(choices=[("pending", "Pending"), ("fetching", "Fetching"), ("judging", "Judging"), ("ready", "Ready"), ("failed", "Failed")], default="pending", max_length=20)),
                ("error", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="profile_imports", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="Conversation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("record", models.JSONField(blank=True, default=dict)),
                ("status", models.CharField(choices=[("active", "Active"), ("completed", "Completed"), ("abandoned", "Abandoned")], default="active", max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("profile_import", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="conversations", to="knowledge.profileimport")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="conversations", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="Message",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("role", models.CharField(choices=[("assistant", "Assistant"), ("user", "User")], max_length=20)),
                ("content", models.TextField(blank=True)),
                ("audio_file", models.FileField(blank=True, null=True, upload_to="answers/%Y/%m/")),
                ("status", models.CharField(choices=[("pending", "Pending"), ("transcribing", "Transcribing"), ("done", "Done"), ("failed", "Failed")], default="done", max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("conversation", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="messages", to="knowledge.conversation")),
            ],
            options={"ordering": ["created_at"]},
        ),
    ]
