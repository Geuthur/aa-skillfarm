# Generated by Django 4.2.11 on 2024-09-23 07:28

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("memberaudit", "0019_alter_charactercontractitem_record_id"),
        ("skillfarm", "0001_initial"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="skillfarmsetup",
            options={"default_permissions": ()},
        ),
        migrations.AlterField(
            model_name="skillfarmaudit",
            name="active",
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name="skillfarmaudit",
            name="character",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="skillfarm_character",
                to="memberaudit.character",
            ),
        ),
        migrations.AlterField(
            model_name="skillfarmnotification",
            name="character",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="skillfarm_notification",
                to="skillfarm.skillfarmaudit",
            ),
        ),
        migrations.AlterField(
            model_name="skillfarmsetup",
            name="character",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="skillfarm_setup",
                to="skillfarm.skillfarmaudit",
            ),
        ),
    ]
