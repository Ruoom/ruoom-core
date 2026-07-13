import pytest
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.http import QueryDict

from administration.forms import UpdateUserForm
from registration.utils.authentication import (
    get_permission_group_names,
    set_user_groups,
)
from tests.factories import create_business, create_profile


def permission_form_data(**overrides):
    data = QueryDict("", mutable=True)
    data.update(
        {
            "first_name": "Kevin",
            "last_name": "Morrissey",
            "email": "kevin@ruoomsoftware.com",
            "is_superuser": "on",
            "is_teacher": "on",
            "message_consent": "on",
            "staff_is_active": "on",
        }
    )
    permissions = overrides.pop("Permissions", ["checkin"])
    data.setlist("Permissions", permissions)
    for key, value in overrides.items():
        data[key] = value
    return data


@pytest.mark.django_db
def test_permissions_form_includes_admin_and_plugin_groups():
    create_business()
    user = create_profile(business_id=1, user_type="staff", is_superuser=True)

    form = UpdateUserForm(user=user)
    choices = dict(form.fields["permissions"].choices)

    assert "admin" in choices
    assert "customforms" in choices


@pytest.mark.django_db
def test_superuser_save_grants_every_permission_group():
    create_business()
    acting_user = create_profile(business_id=1, email="owner@example.com", user_type="staff", is_superuser=True)
    staff_user = create_profile(business_id=1, email="staff@example.com", user_type="staff", is_superuser=False)
    form = UpdateUserForm(
        permission_form_data(email=staff_user.email),
        user=acting_user,
        instance=staff_user,
    )

    assert form.is_valid(), form.errors

    saved_user = form.save()
    saved_groups = set(saved_user.groups.values_list("name", flat=True))

    assert set(get_permission_group_names()).issubset(saved_groups)


@pytest.mark.django_db
def test_set_user_groups_creates_missing_plugin_group():
    user = create_profile(email="plugin-permission@example.com", user_type="staff")

    set_user_groups(user, ["customforms"])

    assert Group.objects.filter(name="customforms").exists()
    assert user.groups.filter(name="customforms").exists()


@pytest.mark.django_db
def test_create_view_groups_bootstraps_plugin_groups_for_superusers():
    superuser = create_profile(email="superuser@example.com", user_type="staff", is_superuser=True)

    call_command("create_view_groups")

    assert Group.objects.filter(name="customforms").exists()
    assert superuser.groups.filter(name="customforms").exists()
