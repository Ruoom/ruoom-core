from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("registration", "0005_profile_google_sync_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="personal_data_erased",
            field=models.BooleanField(default=False, verbose_name="Personal Data Erased"),
        ),
        migrations.AddField(
            model_name="profile",
            name="personal_data_erased_at",
            field=models.DateTimeField(blank=True, null=True, verbose_name="Personal Data Erased At"),
        ),
    ]
