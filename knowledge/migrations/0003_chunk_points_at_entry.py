import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("knowledge", "0002_knowledgeentry"),
    ]

    operations = [
        migrations.RemoveField(model_name="knowledgechunk", name="source"),
        migrations.AddField(
            model_name="knowledgechunk",
            name="entry",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="chunks",
                to="knowledge.knowledgeentry",
            ),
            preserve_default=False,
        ),
    ]
