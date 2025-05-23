# Generated by Django 4.2.20 on 2025-05-10 12:35

# Django
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("skillfarm", "0004_evetypeprice"),
    ]

    operations = [
        migrations.AlterField(
            model_name="characterskill",
            name="character",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="skillfarm_skills",
                to="skillfarm.skillfarmaudit",
            ),
        ),
        migrations.AlterField(
            model_name="characterskillqueueentry",
            name="character",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="skillfarm_skillqueue",
                to="skillfarm.skillfarmaudit",
            ),
        ),
        migrations.RemoveField(
            model_name="skillfarmaudit",
            name="last_update_skillqueue",
        ),
        migrations.RemoveField(
            model_name="skillfarmaudit",
            name="last_update_skills",
        ),
        migrations.CreateModel(
            name="CharacterUpdateStatus",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "section",
                    models.CharField(
                        choices=[("skills", "Skills"), ("skillqueue", "Skill Queue")],
                        db_index=True,
                        max_length=32,
                    ),
                ),
                (
                    "is_success",
                    models.BooleanField(db_index=True, default=None, null=True),
                ),
                ("error_message", models.TextField()),
                ("has_token_error", models.BooleanField(default=False)),
                (
                    "last_run_at",
                    models.DateTimeField(
                        db_index=True,
                        default=None,
                        help_text="Last run has been started at this time",
                        null=True,
                    ),
                ),
                (
                    "last_run_finished_at",
                    models.DateTimeField(
                        db_index=True,
                        default=None,
                        help_text="Last run has been successful finished at this time",
                        null=True,
                    ),
                ),
                (
                    "last_update_at",
                    models.DateTimeField(
                        db_index=True,
                        default=None,
                        help_text="Last update has been started at this time",
                        null=True,
                    ),
                ),
                (
                    "last_update_finished_at",
                    models.DateTimeField(
                        db_index=True,
                        default=None,
                        help_text="Last update has been successful finished at this time",
                        null=True,
                    ),
                ),
                (
                    "character",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="skillfarm_update_status",
                        to="skillfarm.skillfarmaudit",
                    ),
                ),
            ],
            options={
                "default_permissions": (),
            },
        ),
    ]
