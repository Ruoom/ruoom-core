# Generated by Django 4.0.6 on 2025-04-24 22:31

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0002_alter_profile_profile_image'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='profile',
            name='balance',
        ),
    ]
