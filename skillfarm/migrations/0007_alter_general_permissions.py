# Django
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("skillfarm", "0006_alter_characterupdatestatus_character_and_more"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="general",
            options={
                "default_permissions": (),
                "managed": False,
                "permissions": [
                    ("basic_access", "Can access this app, Skillfarm."),
                    (
                        "corp_access",
                        "Has access to all characters in the corporation.",
                    ),
                    ("admin_access", "Has access to all characters."),
                ],
                "verbose_name": "AA-Skillfarm",
                "verbose_name_plural": "AA-Skillfarm",
            },
        ),
    ]
