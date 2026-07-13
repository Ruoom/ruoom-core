import pytest
from django.test import Client
from django.urls import reverse

from tests.factories import create_business, create_mailerlite_settings, create_profile


pytestmark = pytest.mark.django_db


def test_mailerlite_settings_page_renders_for_staff_user():
    business = create_business()
    staff_user = create_profile(
        business_id=business.business_id,
        email="staff@example.com",
        user_type="staff",
        is_staff=True,
        is_superuser=True,
    )
    client = Client()
    client.force_login(staff_user)

    response = client.get(reverse("mailerlite:settings"), HTTP_HOST="localhost")

    assert response.status_code == 200
    assert b"MailerLite Integration" in response.content


def test_mailerlite_settings_page_does_not_render_saved_api_key():
    business = create_business()
    settings_obj = create_mailerlite_settings(business=business)
    settings_obj.set_api_key("super-secret-mailerlite-key")
    settings_obj.save()
    create_profile(
        business_id=business.business_id,
        email="admin-secret@example.com",
        is_staff=True,
        is_superuser=True,
    )
    staff_user = create_profile(
        business_id=business.business_id,
        email="staff-secret@example.com",
        user_type="staff",
        is_staff=True,
    )
    client = Client()
    client.force_login(staff_user)

    response = client.get(reverse("mailerlite:settings"), HTTP_HOST="localhost")

    assert response.status_code == 200
    assert b"super-secret-mailerlite-key" not in response.content


def test_mailerlite_api_rejects_customer_ajax_access():
    business = create_business()
    customer = create_profile(
        business_id=business.business_id,
        email="customer-mailerlite@example.com",
        user_type="customer",
    )
    client = Client()
    client.force_login(customer)

    response = client.get(
        reverse("mailerlite:fetch-groups"),
        HTTP_HOST="localhost",
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
    )

    assert response.status_code == 404
