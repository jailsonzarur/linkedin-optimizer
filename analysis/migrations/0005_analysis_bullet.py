import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("analysis", "0004_section_source_ref")]

    operations = [
        migrations.CreateModel(
            name="AnalysisBullet",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("kind", models.CharField(choices=[("original", "Original"), ("suggested", "Suggested")], max_length=20)),
                ("position", models.PositiveSmallIntegerField(default=0)),
                ("text", models.TextField()),
                ("section", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                              related_name="bullets", to="analysis.analysissection")),
            ],
            options={"ordering": ["section", "kind", "position"]},
        ),
    ]
