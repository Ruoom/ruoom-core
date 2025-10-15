from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0003_remove_profile_balance'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='google_sync_enabled',
            field=models.BooleanField(default=False, verbose_name='Google Calendar Sync Enabled'),
        ),
        migrations.AddField(
            model_name='profile',
            name='google_credentials_json',
            field=models.TextField(blank=True, null=True, verbose_name='Google OAuth Credentials (JSON)'),
        ),
    ]
