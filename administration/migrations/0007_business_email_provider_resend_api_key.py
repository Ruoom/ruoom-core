from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("administration", "0006_business_branding_tokens"),
    ]

    operations = [
        migrations.AddField(
            model_name="business",
            name="email_provider",
            field=models.CharField(
                choices=[
                    ("smtp_server", "SMTP Server"),
                    ("resend", "Resend"),
                ],
                default="smtp_server",
                max_length=20,
                verbose_name="Email Provider",
            ),
        ),
        migrations.AddField(
            model_name="business",
            name="resend_api_key",
            field=models.CharField(
                blank=True,
                max_length=400,
                null=True,
                verbose_name="Resend API Key",
            ),
        ),
    ]
