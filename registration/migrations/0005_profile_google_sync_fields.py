from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("registration", "0004_username_plus_business_id"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                        ALTER TABLE registration_profile
                        ADD COLUMN IF NOT EXISTS google_sync_enabled boolean NOT NULL DEFAULT false;
                        ALTER TABLE registration_profile
                        ALTER COLUMN google_sync_enabled SET DEFAULT false;
                        ALTER TABLE registration_profile
                        ADD COLUMN IF NOT EXISTS google_credentials_json text;
                    """,
                    reverse_sql=migrations.RunSQL.noop,
                )
            ],
            state_operations=[
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
            ],
        ),
    ]
