from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("analysis", "0003_drop_profile_snapshot")]

    operations = [
        migrations.AddField(
            model_name="analysissection",
            name="source_ref",
            field=models.CharField(blank=True, max_length=40),
        ),
        migrations.AlterModelOptions(
            name="analysissection",
            options={"ordering": ["analysis", "section", "source_ref", "variant_index"]},
        ),
    ]
