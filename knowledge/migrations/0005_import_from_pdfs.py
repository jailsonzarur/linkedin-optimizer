from django.db import migrations, models


def clear_imports(apps, schema_editor):
    """The scraped imports have no PDF to point at, and there is no honest way to
    invent one."""
    apps.get_model("analysis", "AnalysisSection").objects.all().delete()
    apps.get_model("analysis", "Analysis").objects.all().delete()
    apps.get_model("knowledge", "Message").objects.all().delete()
    apps.get_model("knowledge", "Conversation").objects.all().delete()
    apps.get_model("knowledge", "ProfileImport").objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("knowledge", "0004_conversation_model"),
        ("analysis", "0003_drop_profile_snapshot"),
    ]

    operations = [
        migrations.RunPython(clear_imports, migrations.RunPython.noop),
        migrations.RunSQL("SET CONSTRAINTS ALL IMMEDIATE", migrations.RunSQL.noop),
        migrations.RemoveField(model_name="profileimport", name="source"),
        migrations.RemoveField(model_name="profileimport", name="source_url"),
        migrations.RemoveField(model_name="profileimport", name="file"),
        migrations.RemoveField(model_name="profileimport", name="raw_text"),
        migrations.AddField(
            model_name="profileimport",
            name="linkedin_pdf",
            field=models.FileField(default="", upload_to="imports/%Y/%m/"),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="profileimport",
            name="resume",
            field=models.FileField(blank=True, null=True, upload_to="imports/%Y/%m/"),
        ),
        migrations.AddField(
            model_name="profileimport",
            name="linkedin_text",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="profileimport",
            name="resume_text",
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name="profileimport",
            name="status",
            field=models.CharField(
                choices=[("pending", "Pending"), ("extracting", "Extracting"),
                         ("judging", "Judging"), ("ready", "Ready"), ("failed", "Failed")],
                default="pending", max_length=20),
        ),
    ]
