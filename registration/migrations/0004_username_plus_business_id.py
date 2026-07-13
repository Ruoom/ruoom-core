from django.db import migrations


def forward_username_plus(apps, schema_editor):
    Profile = apps.get_model("registration", "Profile")
    User = apps.get_model("auth", "User")
    for profile in Profile.objects.exclude(email="").iterator():
        old_username = f"{profile.email},{profile.business_id}"
        if profile.user_ptr.username == old_username:
            User.objects.filter(pk=profile.pk, username=old_username).update(
                username=f"{profile.email}+{profile.business_id}"
            )


def reverse_username_comma(apps, schema_editor):
    Profile = apps.get_model("registration", "Profile")
    User = apps.get_model("auth", "User")
    for profile in Profile.objects.exclude(email="").iterator():
        plus_username = f"{profile.email}+{profile.business_id}"
        if profile.user_ptr.username == plus_username:
            User.objects.filter(pk=profile.pk, username=plus_username).update(
                username=f"{profile.email},{profile.business_id}"
            )


class Migration(migrations.Migration):

    dependencies = [
        ("registration", "0003_remove_profile_balance"),
    ]

    operations = [
        migrations.RunPython(forward_username_plus, reverse_username_comma),
    ]
