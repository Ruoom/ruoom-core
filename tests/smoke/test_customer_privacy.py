from datetime import timedelta

import pytest
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.utils import timezone

from plugins.booking.models import Service
from plugins.booking.services import create_or_update_checkin
from plugins.customforms.models import (
    CustomForm,
    CustomFormAssignment,
    CustomFormField,
    CustomFormFieldResponse,
    CustomFormResponse,
)
from registration.privacy import erase_profile_personal_data
from tests.factories import create_business, create_location, create_profile, create_service


@pytest.mark.django_db
def test_erase_profile_personal_data_anonymizes_profile_rsvp_and_custom_forms():
    business = create_business()
    location = create_location(business_id=business.business_id)
    profile = create_profile(
        business_id=business.business_id,
        email="person@example.com",
        first_name="Person",
        last_name="Example",
        phone="+15551234567",
        street_address="123 Main St",
        emgcy_cont_name="Friend",
    )
    service = create_service(
        location=location,
        business_id=business.business_id,
        price=0,
        scheduled_time=timezone.now() + timedelta(days=1),
    )
    checkin = create_or_update_checkin(
        service=service,
        guest_name="Person Example",
        guest_email="person@example.com",
        payment_required=False,
    )

    custom_form = CustomForm.objects.create(
        business_id=business.business_id,
        name="Privacy Form",
        is_active=True,
    )
    assignment = CustomFormAssignment.objects.create(
        business_id=business.business_id,
        form=custom_form,
        use_case=CustomFormAssignment.USE_CASE_EVENT_REGISTRATION,
        content_type=ContentType.objects.get_for_model(Service, for_concrete_model=False),
        object_id=service.id,
        is_required=False,
        is_active=True,
    )
    email_field = CustomFormField.objects.create(
        form=custom_form,
        label="Contact Email",
        field_type="email",
        required=False,
        order=0,
    )
    response = CustomFormResponse.objects.create(
        business_id=business.business_id,
        customer=profile,
        guest_email="person@example.com",
        custom_form=custom_form,
        assignment=assignment,
    )
    CustomFormFieldResponse.objects.create(
        business_id=business.business_id,
        customer=profile,
        form_response=response,
        field=email_field,
        value_email="person@example.com",
    )

    erase_profile_personal_data(profile)

    profile.refresh_from_db()
    checkin.refresh_from_db()
    response.refresh_from_db()
    field_response = CustomFormFieldResponse.objects.get(form_response=response, field=email_field)

    assert profile.personal_data_erased is True
    assert profile.personal_data_erased_at is not None
    assert profile.email.endswith("@deleted.invalid")
    assert profile.first_name == ""
    assert str(profile.phone) == ""
    assert profile.street_address == ""
    assert profile.emgcy_cont_name == ""
    assert profile.is_active is False
    assert checkin.guest_name == "Deleted User"
    assert checkin.guest_email == ""
    assert response.customer is None
    assert response.guest_email == ""
    assert field_response.customer is None
    assert field_response.value_email == ""


@pytest.mark.django_db
def test_superuser_can_trigger_erase_personal_data_from_account_settings(client):
    business = create_business()
    target = create_profile(
        business_id=business.business_id,
        email="target@example.com",
        first_name="Target",
        last_name="User",
    )
    superuser = create_profile(
        business_id=business.business_id,
        email="admin@example.com",
        is_superuser=True,
        is_staff=True,
        user_type="staff",
    )
    client.force_login(superuser)

    response = client.post(
        reverse("customer:customer-account-settings") + f"?customer={target.id}",
        {"erase_personal_data": "1"},
    )

    target.refresh_from_db()
    assert response.status_code == 200
    assert target.personal_data_erased is True
    assert target.email.endswith("@deleted.invalid")


@pytest.mark.django_db
def test_non_superuser_cannot_trigger_erase_personal_data(client):
    business = create_business()
    target = create_profile(
        business_id=business.business_id,
        email="target2@example.com",
    )
    staff = create_profile(
        business_id=business.business_id,
        email="staff@example.com",
        is_staff=True,
        user_type="staff",
    )
    client.force_login(staff)

    response = client.post(
        reverse("customer:customer-account-settings") + f"?customer={target.id}",
        {"erase_personal_data": "1"},
    )

    target.refresh_from_db()
    assert response.status_code == 302
    assert target.personal_data_erased is False
