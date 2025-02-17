# Generated by Django 5.0.3 on 2025-02-17 03:21

import administration.models
import django.contrib.auth.models
import django.db.models.deletion
import phonenumber_field.modelfields
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('administration', '0001_initial'),
        ('auth', '0013_alter_user_username'),
    ]

    operations = [
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('user_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to=settings.AUTH_USER_MODEL)),
                ('user_type', models.CharField(choices=[('customer', 'Customer'), ('staff', 'Staff')], default='customer', max_length=10, verbose_name='User Type')),
                ('staff_is_active', models.BooleanField(default=True, verbose_name='Staff is Active')),
                ('phone', phonenumber_field.modelfields.PhoneNumberField(blank=True, max_length=128, region=None, verbose_name='Phone Number')),
                ('notes', models.CharField(blank=True, max_length=5000, null=True, verbose_name='Notes')),
                ('gender', models.CharField(blank=True, choices=[('female', 'Female'), ('male', 'Male'), ('nonbinary', 'Gender variant/Non-conforming'), ('not listed', 'Not Listed'), ('prefer not to say', 'Prefer not to say')], max_length=50, null=True, verbose_name='Gender')),
                ('language', models.CharField(choices=[('en', 'English'), ('ko', 'Korean')], default='en', max_length=2, verbose_name='Language')),
                ('date_of_birth', models.DateField(blank=True, null=True, verbose_name='Date of Birth')),
                ('profile_image_url', models.TextField(blank=True, null=True, verbose_name='Profile Image URL')),
                ('profile_image', models.ImageField(blank=True, default='Wall-E.jpg', upload_to=administration.models.user_profile_path, verbose_name='Profile Image')),
                ('street_address', models.CharField(blank=True, max_length=200, null=True, verbose_name='Street Address')),
                ('city', models.CharField(blank=True, max_length=50, null=True, verbose_name='City')),
                ('state', models.CharField(blank=True, max_length=50, null=True, verbose_name='State')),
                ('country', models.CharField(blank=True, max_length=50, null=True, verbose_name='Country')),
                ('emgcy_cont_name', models.CharField(blank=True, max_length=400, null=True, verbose_name='Emergency Contact Name')),
                ('emgcy_cont_relation', models.CharField(blank=True, max_length=400, null=True, verbose_name='Emergency Contact Relationship')),
                ('emgcy_cont_num', phonenumber_field.modelfields.PhoneNumberField(blank=True, max_length=128, null=True, region=None, verbose_name='Emergency Contact Number')),
                ('is_teacher', models.BooleanField(default=False, verbose_name='Is This User a Service Provider?')),
                ('message_consent', models.BooleanField(default=False, verbose_name='May we communicate with you via mobile messages regarding your registrations?')),
                ('balance', models.DecimalField(decimal_places=2, default=0, max_digits=8, verbose_name='Account Balance')),
                ('business_id', models.PositiveIntegerField(default=1, verbose_name='Business ID')),
                ('msa_signed', models.BooleanField(default=False, verbose_name='Has this user signed the Master Service Agreement?')),
                ('default_location', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='administration.locations', verbose_name='Default Location')),
                ('staff_at_locations', models.ManyToManyField(blank=True, related_name='staff_at_locations', to='administration.locations', verbose_name='Staff At Locations')),
            ],
            options={
                'verbose_name': 'Profile',
            },
            bases=('auth.user',),
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
    ]
