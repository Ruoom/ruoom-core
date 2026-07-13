from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("administration", "0007_business_email_provider_resend_api_key"),
    ]

    operations = [
        migrations.AddField(
            model_name="business",
            name="booking_calendar_enabled",
            field=models.BooleanField(default=True, verbose_name="Booking Calendar Enabled"),
        ),
        migrations.AddField(
            model_name="business",
            name="booking_event_cards_enabled",
            field=models.BooleanField(default=True, verbose_name="Booking Event Cards Enabled"),
        ),
        migrations.AddField(
            model_name="business",
            name="event_registration_confirmation_email_enabled",
            field=models.BooleanField(default=True, verbose_name="Send RSVP Confirmation Email"),
        ),
        migrations.AddField(
            model_name="business",
            name="customer_page_org_name",
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name="Customer Page Org Name"),
        ),
        migrations.AddField(
            model_name="business",
            name="customer_page_full_name",
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name="Customer Page Full Name"),
        ),
        migrations.AddField(
            model_name="business",
            name="customer_page_tagline",
            field=models.CharField(blank=True, max_length=400, null=True, verbose_name="Customer Page Tagline"),
        ),
    ]
