from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("administration", "0005_alter_location_time_zone_string"),
    ]

    operations = [
        migrations.AddField(
            model_name="business",
            name="secondary_accent_color",
            field=models.CharField(
                blank=True,
                max_length=20,
                null=True,
                verbose_name="Secondary Accent Color",
            ),
        ),
        migrations.AddField(
            model_name="business",
            name="highlight_color",
            field=models.CharField(
                blank=True,
                max_length=20,
                null=True,
                verbose_name="Highlight Color",
            ),
        ),
        migrations.AddField(
            model_name="business",
            name="font_header",
            field=models.CharField(
                blank=True,
                max_length=200,
                null=True,
                verbose_name="Header Font",
            ),
        ),
        migrations.AddField(
            model_name="business",
            name="font_body",
            field=models.CharField(
                blank=True,
                max_length=200,
                null=True,
                verbose_name="Body Font",
            ),
        ),
    ]
