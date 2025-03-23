# Generated by Django 4.0.6 on 2025-03-21 20:58

from django.db import migrations, models
import registration.models


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='profile_image',
            field=models.ImageField(blank=True, default='Wall-E.jpg', upload_to=registration.models.user_profile_path, verbose_name='Profile Image'),
        ),
    ]
