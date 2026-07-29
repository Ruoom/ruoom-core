from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("registration", "0004_username_plus_business_id"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="google_sync_enabled",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="profile",
            name="google_credentials_json",
            field=models.TextField(blank=True, null=True),
        ),
    ]
