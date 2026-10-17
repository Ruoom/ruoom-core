import pytest
from django.contrib.auth.models import AnonymousUser
from django.template.loader import render_to_string
from django.test import RequestFactory
from django.urls import reverse

from administration.models import Business
from registration.context_processors import signin_context
from registration.models import Profile


@pytest.mark.django_db
def test_embedded_password_signin_retains_checkout_on_failure_and_success(client, settings):
    settings.FORCE_SUPERUSER_CREATION = False
    Business.objects.create(business_id=1, name="Test", default_country_code="US")
    profile = Profile.objects.create(
        username="buyer", email="buyer@example.com", business_id=1,
    )
    profile.set_password("checkout-test-password")
    profile.save()
    next_url = "/payment/checkout/?cart=42&currency=krw"
    data = {"email": profile.email, "password": "wrong", "redirect_url": next_url}
    headers = {"HTTP_HOST": "localhost", "HTTP_X_RUOOM_EMBEDDED_SIGNIN": "1"}

    invalid = client.post(reverse("registration:signin"), data, **headers)
    assert invalid.status_code == 404
    assert b"data-embedded-signin-form" in invalid.content
    assert b"<body" not in invalid.content
    assert invalid.context["redirect_url"] == next_url
    assert "_auth_user_id" not in client.session

    data["password"] = "checkout-test-password"
    response = client.post(reverse("registration:signin"), data, **headers)
    assert response.json() == {"authenticated": True, "redirect_url": next_url}
    assert client.session["_auth_user_id"] == str(profile.id)


@pytest.mark.parametrize("url", ["https://evil.example/", "//evil.example/"])
def test_embedded_signin_rejects_external_return_urls(url):
    from registration.embedded_signin import safe_signin_redirect
    request = RequestFactory().get("/", HTTP_HOST="localhost")
    assert safe_signin_redirect(request, url) == ""


def test_modal_signin_loads_shared_controller():
    request = RequestFactory().get("/payment/checkout/?cart=42")
    request.user = AnonymousUser()
    html = render_to_string(
        "registration/partials/signin_form.html",
        {**signin_context(request), "embedded_signin": True}, request=request,
    )
    assert "data-embedded-signin data-error-message=" in html
    assert "registration/embedded-signin.js" in html
