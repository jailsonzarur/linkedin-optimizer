import django.db.models.deletion
from django.db import migrations, models


def clear_analyses(apps, schema_editor):
    """The demo analyses point at snapshots that are going away, and there is no
    honest way to map them onto an import that never happened."""
    apps.get_model("analysis", "AnalysisSection").objects.all().delete()
    apps.get_model("analysis", "Analysis").objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("analysis", "0002_analysis_keyword_gap"),
        ("knowledge", "0004_conversation_model"),
    ]

    operations = [
        migrations.RunPython(clear_analyses, migrations.RunPython.noop),
        # Deleting rows leaves deferred FK triggers pending, and Postgres refuses
        # to ALTER the same table until they fire.
        migrations.RunSQL("SET CONSTRAINTS ALL IMMEDIATE", migrations.RunSQL.noop),
        migrations.RemoveField(model_name="analysis", name="profile_snapshot"),
        migrations.DeleteModel(name="ProfileSnapshot"),
        migrations.AddField(
            model_name="analysis",
            name="profile_import",
            field=models.ForeignKey(
                default=None,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="analyses",
                to="knowledge.profileimport",
            ),
            preserve_default=False,
        ),
    ]
