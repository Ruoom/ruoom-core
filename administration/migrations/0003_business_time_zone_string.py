# Generated by Django 4.0.6 on 2025-03-22 20:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('administration', '0002_rename_studiosettings_business_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='business',
            name='time_zone_string',
            field=models.CharField(blank=True, max_length=400, null=True, verbose_name='Time Zone'),
        ),
    ]
