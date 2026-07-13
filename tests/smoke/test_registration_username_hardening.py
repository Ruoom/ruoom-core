import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from registration.models import Profile


pytestmark = pytest.mark.django_db


def test_builtin_username_field_remains_unique():
    username_field = get_user_model()._meta.get_field("username")

    assert username_field.unique is True


def test_profile_save_derives_username_from_email_and_business():
    first = Profile.objects.create(
        email="shared@example.com",
        business_id=1,
        first_name="One",
    )
    second = Profile.objects.create(
        email="shared@example.com",
        business_id=2,
        first_name="Two",
    )

    assert first.username == "shared@example.com+1"
    assert second.username == "shared@example.com+2"


def test_generated_username_matches_django_username_validators():
    username = Profile.username_for_identity("shared@example.com", 1)
    username_field = get_user_model()._meta.get_field("username")

    for validator in username_field.validators:
        try:
            validator(username)
        except ValidationError as exc:
            raise AssertionError(f"Generated username failed validator {validator}: {exc}") from exc


def test_generated_username_strips_surrounding_email_whitespace_without_changing_case():
    assert Profile.username_for_identity(" Shared@Example.COM ", 1) == "Shared@Example.COM+1"


def test_same_email_and_business_still_conflict_on_generated_username():
    Profile.objects.create(
        email="duplicate@example.com",
        business_id=7,
        first_name="Original",
    )

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Profile.objects.create(
                email="duplicate@example.com",
                business_id=7,
                first_name="Duplicate",
            )
