import pytest
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse, JsonResponse
from django.test import Client, RequestFactory, override_settings
from django.urls import reverse
from unittest.mock import patch

from plugins.email_otp.models import EmailOTP
from registration.middleware.authentication import AuthenticationMiddleware
from tests.factories import create_business, create_profile


pytestmark = pytest.mark.django_db


def middleware_response(request):
    return HttpResponse("ok")


@override_settings(FORCE_SUPERUSER_CREATION=False, ENABLE_PER_PAGE_PERMISSIONS=True)
def test_email_otp_paths_are_public_without_authentication():
    request = RequestFactory().get("/otp/signin/", HTTP_HOST="localhost")
    request.user = AnonymousUser()

    response = AuthenticationMiddleware(middleware_response)(request)

    assert response.status_code == 200


@override_settings(FORCE_SUPERUSER_CREATION=False, ENABLE_PER_PAGE_PERMISSIONS=True)
def test_email_otp_request_generates_code_and_sends_email():
    create_business()
    client = Client()

    with patch("plugins.email_otp.views.automated_email_send", return_value=JsonResponse({"message": "success"})) as send_mock:
        response = client.post(
            reverse("email_otp:request"),
            {"email": "Person@Example.com"},
            HTTP_HOST="localhost",
        )

    assert response.status_code == 302
    assert response.url == reverse("email_otp:verify")
    assert EmailOTP.objects.filter(email="person@example.com", business_id=1, is_used=False).exists()
    send_mock.assert_called_once()


@override_settings(FORCE_SUPERUSER_CREATION=False, ENABLE_PER_PAGE_PERMISSIONS=True)
def test_email_otp_request_does_not_leave_active_code_when_email_send_fails():
    create_business()
    client = Client()

    with patch("plugins.email_otp.views.automated_email_send", return_value=JsonResponse({"message": "No email configured"})):
        response = client.post(
            reverse("email_otp:request"),
            {"email": "person@example.com"},
            HTTP_HOST="localhost",
        )

    assert response.status_code == 503
    assert not EmailOTP.objects.filter(email="person@example.com", business_id=1, is_used=False).exists()


@override_settings(FORCE_SUPERUSER_CREATION=False, ENABLE_PER_PAGE_PERMISSIONS=True, EMAIL_OTP_REQUEST_COOLDOWN_SECONDS=60)
def test_email_otp_request_is_rate_limited_after_recent_code():
    create_business()
    EmailOTP.generate("person@example.com", business_id=1)
    client = Client()

    with patch("plugins.email_otp.views.automated_email_send") as send_mock:
        response = client.post(
            reverse("email_otp:request"),
            {"email": "person@example.com"},
            HTTP_HOST="localhost",
        )

    assert response.status_code == 429
    send_mock.assert_not_called()


@override_settings(FORCE_SUPERUSER_CREATION=False, ENABLE_PER_PAGE_PERMISSIONS=True)
def test_email_otp_verify_logs_existing_user_in_and_consumes_code():
    create_business()
    profile = create_profile(email="person@example.com", business_id=1)
    otp = EmailOTP.generate(profile.email, profile.business_id)
    client = Client()
    session = client.session
    session["email_otp_email"] = profile.email
    session["email_otp_business_id"] = profile.business_id
    session.save()

    response = client.post(
        reverse("email_otp:verify"),
        {"code": otp.raw_code},
        HTTP_HOST="localhost",
    )

    assert response.status_code == 302
    assert response.url == "/customer/account-settings/"
    assert str(profile.pk) == client.session["_auth_user_id"]
    otp.refresh_from_db()
    assert otp.is_used is True
    assert "email_otp_email" not in client.session
    assert "email_otp_business_id" not in client.session


@override_settings(FORCE_SUPERUSER_CREATION=False, ENABLE_PER_PAGE_PERMISSIONS=True)
def test_email_otp_verify_clears_next_when_verified_email_has_no_profile(settings):
    create_business()
    email = "newperson@example.com"
    otp = EmailOTP.generate(email, business_id=1)
    client = Client()
    session = client.session
    session["email_otp_email"] = email
    session["email_otp_business_id"] = 1
    session["email_otp_next"] = "/private/"
    session.save()

    response = client.post(
        reverse("email_otp:verify"),
        {"code": otp.raw_code},
        HTTP_HOST="localhost",
    )

    assert response.status_code == 302
    assert response.url == settings.SIGNUP_URL
    assert client.session["verified_email"] == email
    assert "email_otp_email" not in client.session
    assert "email_otp_business_id" not in client.session
    assert "email_otp_next" not in client.session


@override_settings(FORCE_SUPERUSER_CREATION=False, ENABLE_PER_PAGE_PERMISSIONS=True)
def test_email_otp_verify_rejects_invalid_code_without_login():
    create_business()
    profile = create_profile(email="person@example.com", business_id=1)
    EmailOTP.generate(profile.email, profile.business_id)
    client = Client()
    session = client.session
    session["email_otp_email"] = profile.email
    session["email_otp_business_id"] = profile.business_id
    session.save()

    response = client.post(
        reverse("email_otp:verify"),
        {"code": "000000"},
        HTTP_HOST="localhost",
    )

    assert response.status_code == 200
    assert "_auth_user_id" not in client.session
    assert b"Invalid or expired code" in response.content


@override_settings(
    FORCE_SUPERUSER_CREATION=False,
    ENABLE_PER_PAGE_PERMISSIONS=True,
    EMAIL_OTP_MAX_VERIFY_ATTEMPTS=2,
)
def test_email_otp_verify_locks_code_after_too_many_failures():
    create_business()
    profile = create_profile(email="person@example.com", business_id=1)
    otp = EmailOTP.generate(profile.email, profile.business_id)
    client = Client()
    session = client.session
    session["email_otp_email"] = profile.email
    session["email_otp_business_id"] = profile.business_id
    session.save()

    first = client.post(reverse("email_otp:verify"), {"code": "000000"}, HTTP_HOST="localhost")
    second = client.post(reverse("email_otp:verify"), {"code": "111111"}, HTTP_HOST="localhost")
    valid_after_lock = client.post(reverse("email_otp:verify"), {"code": otp.raw_code}, HTTP_HOST="localhost")

    assert first.status_code == 200
    assert second.status_code == 200
    assert valid_after_lock.status_code == 200
    assert "_auth_user_id" not in client.session
    otp.refresh_from_db()
    assert otp.is_used is True
    assert otp.verification_attempts == 2


@override_settings(FORCE_SUPERUSER_CREATION=False, ENABLE_PER_PAGE_PERMISSIONS=True)
def test_email_otp_verify_rejects_unsafe_next_url():
    create_business()
    profile = create_profile(email="person@example.com", business_id=1)
    client = Client()

    with patch("plugins.email_otp.views.automated_email_send", return_value=JsonResponse({"message": "success"})):
        response = client.post(
            reverse("email_otp:request"),
            {"email": profile.email, "next": "https://evil.example/path"},
            HTTP_HOST="localhost",
        )
    assert response.status_code == 302
    assert "email_otp_next" not in client.session
