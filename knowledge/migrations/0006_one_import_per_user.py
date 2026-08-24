from django.db import migrations, models


def drop_extra_imports(apps, schema_editor):
    ProfileImport = apps.get_model("knowledge", "ProfileImport")
    seen = set()
    for row in ProfileImport.objects.order_by("user_id", "-created_at"):
        if row.user_id in seen:
            row.delete()
        else:
            seen.add(row.user_id)


class Migration(migrations.Migration):

    dependencies = [("knowledge", "0005_import_from_pdfs")]

    operations = [
        migrations.RunPython(drop_extra_imports, migrations.RunPython.noop),
        migrations.RunSQL("SET CONSTRAINTS ALL IMMEDIATE", migrations.RunSQL.noop),
        migrations.AddConstraint(
            model_name="profileimport",
            constraint=models.UniqueConstraint(fields=("user",), name="one_profile_import_per_user"),
        ),
    ]
