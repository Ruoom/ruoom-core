from django.conf import settings
from django.db import migrations, models


def fill_missing_business_timezones(apps, schema_editor):
    Business = apps.get_model("administration", "Business")
    fallback = getattr(settings, "TIME_ZONE", "UTC") or "UTC"
    Business.objects.filter(time_zone_string__isnull=True).update(time_zone_string=fallback)
    Business.objects.filter(time_zone_string="").update(time_zone_string=fallback)


class Migration(migrations.Migration):

    dependencies = [
        ("administration", "0008_business_booking_page_flags"),
    ]

    operations = [
        migrations.AlterField(
            model_name="business",
            name="time_zone_string",
            field=models.CharField(
                blank=True,
                default="UTC",
                max_length=400,
                null=True,
                verbose_name="Time Zone",
            ),
        ),
        migrations.RunPython(fill_missing_business_timezones, migrations.RunPython.noop),
    ]
