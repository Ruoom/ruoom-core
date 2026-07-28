from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("registration", "0006_profile_personal_data_erased_fields"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="profile",
            name="msa_signed",
        ),
    ]
