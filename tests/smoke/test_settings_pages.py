import pytest
from django.http import JsonResponse
from django.test import override_settings
from django.urls import reverse
from unittest.mock import patch

from tests.factories import create_business, create_profile


@pytest.mark.django_db
def test_settings_pages_render_first_party_tabs(client):
    business = create_business()
    user = create_profile(
        business_id=business.business_id,
        email="owner@example.com",
        is_staff=True,
        is_superuser=True,
    )
    client.force_login(user)

    urls = [
        reverse("administration:settings-contact"),
        reverse("administration:settings-branding"),
        reverse("administration:settings-communications"),
    ]

    for url in urls:
        response = client.get(url, HTTP_HOST="localhost")

        assert response.status_code == 200
        content = response.content.decode()
        assert "General" in content
        assert "Branding" in content
        assert "Communications" in content

    branding_response = client.get(reverse("administration:settings-branding"), HTTP_HOST="localhost")
    assert "Restore Default Colors" in branding_response.content.decode()

    communications_response = client.get(reverse("administration:settings-communications"), HTTP_HOST="localhost")
    communications_content = communications_response.content.decode()
    assert "Resend" in communications_content
    assert "Email Templates" in communications_content
    assert "Send test email" in communications_content

    booking_response = client.get(reverse("booking:settings-embed"), HTTP_HOST="localhost")
    booking_content = booking_response.content.decode()
    assert "Booking Plugin" in booking_content
    assert "Enable booking calendar view" in booking_content
    assert "Send RSVP confirmation emails" in booking_content


@pytest.mark.django_db
def test_branding_settings_save_core_brand_tokens(client):
    business = create_business()
    user = create_profile(
        business_id=business.business_id,
        email="branding-owner@example.com",
        is_staff=True,
        is_superuser=True,
    )
    client.force_login(user)

    response = client.post(
        reverse("administration:settings-branding"),
        {
            "setting_update": "branding_settings",
            "headerValue": "#90A2F4",
            "backgroundValue": "#F2EFEB",
            "textValue": "#111133",
            "accent2Value": "#DD449B",
            "buttonValue": "#90A2F4",
            "buttonTextColor": "#FFFFFF",
            "alertValue": "#CFCF5A",
            "fontHeader": "'Poppins', sans-serif",
            "fontBody": "'Inter', sans-serif",
        },
        HTTP_HOST="localhost",
    )

    assert response.status_code == 302
    assert response.url == reverse("administration:settings-branding")

    business.refresh_from_db()
    assert business.header_color == "#90A2F4"
    assert business.background_color == "#F2EFEB"
    assert business.text_color == "#111133"
    assert business.secondary_accent_color == "#DD449B"
    assert business.button_color == "#90A2F4"
    assert business.button_text_color == "#FFFFFF"
    assert business.highlight_color == "#CFCF5A"
    assert business.font_header == "'Poppins', sans-serif"
    assert business.font_body == "'Inter', sans-serif"


@pytest.mark.django_db
def test_communications_settings_save_resend_provider(client):
    business = create_business()
    user = create_profile(
        business_id=business.business_id,
        email="communications-owner@example.com",
        is_staff=True,
        is_superuser=True,
    )
    client.force_login(user)

    response = client.post(
        reverse("administration:settings-communications"),
        {
            "setting_update": "email_settings",
            "email_provider": "resend",
            "email_address": "hello@example.com",
            "resend_api_key": "re_123",
        },
        HTTP_HOST="localhost",
    )

    assert response.status_code == 302
    business.refresh_from_db()
    assert business.email_provider == business.EMAIL_PROVIDER_RESEND
    assert business.email_address == "hello@example.com"
    assert business.resend_api_key
    assert business.resend_api_key != "re_123"


@pytest.mark.django_db
def test_booking_settings_save_public_page_flags(client):
    business = create_business()
    user = create_profile(
        business_id=business.business_id,
        email="booking-owner@example.com",
        is_staff=True,
        is_superuser=True,
    )
    client.force_login(user)

    response = client.post(
        reverse("booking:settings-embed"),
        {
            "setting_update": "booking_settings",
            "booking_calendar_enabled": "on",
        },
        HTTP_HOST="localhost",
    )

    assert response.status_code == 302
    business.refresh_from_db()
    assert business.booking_calendar_enabled is True
    assert business.booking_event_cards_enabled is False
    assert business.event_registration_confirmation_email_enabled is False


@pytest.mark.django_db
@override_settings(FORCE_SUPERUSER_CREATION=False)
def test_booking_settings_page_allows_ruoom_staff_profile(client):
    business = create_business()
    user = create_profile(
        business_id=business.business_id,
        email="booking-staff@example.com",
        user_type="staff",
        is_staff=False,
        is_superuser=False,
    )
    client.force_login(user)

    response = client.get(reverse("booking:settings-embed"), HTTP_HOST="localhost")

    assert response.status_code == 200
    assert "Booking Plugin" in response.content.decode()


@pytest.mark.django_db
def test_communications_send_test_email_uses_configured_business(client):
    business = create_business()
    user = create_profile(
        business_id=business.business_id,
        email="test-send@example.com",
        is_staff=True,
        is_superuser=True,
    )
    client.force_login(user)

    with patch(
        "administration.views.automated_email_send",
        return_value=JsonResponse({"message": "success"}),
    ) as send_mock:
        response = client.post(
            reverse("administration:settings-communications"),
            {"setting_update": "send_test_email"},
            HTTP_HOST="localhost",
        )

    assert response.status_code == 302
    send_mock.assert_called_once()
    assert send_mock.call_args.kwargs["business_id"] == business.business_id


@pytest.mark.django_db
def test_email_preview_endpoints_render_for_superuser(client):
    business = create_business()
    user = create_profile(
        business_id=business.business_id,
        email="preview-owner@example.com",
        is_staff=True,
        is_superuser=True,
    )
    client.force_login(user)

    render_response = client.get(
        reverse("administration:email_preview_render", args=["create_password"]),
        HTTP_HOST="localhost",
    )
    html_response = client.get(
        reverse("administration:email_preview_html", args=["create_password"]),
        HTTP_HOST="localhost",
    )

    assert render_response.status_code == 200
    assert "Create Password" in render_response.content.decode()
    assert html_response.status_code == 200
    assert html_response.json()["html"]
    assert html_response.json()["subject"]
