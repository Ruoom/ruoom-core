import pytest
from django.conf import settings
from django.urls import reverse

from registration.forms import SignupForm
from registration.models import Profile
from tests.factories import create_business, create_profile


pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def disable_superuser_bootstrap(settings):
    settings.FORCE_SUPERUSER_CREATION = False


def create_auth_profile(password="secret123", **overrides):
    profile = create_profile(**overrides)
    profile.set_password(password)
    profile.save()
    return profile


def test_signin_get_redirects_authenticated_users(client):
    create_business()
    user = create_profile(user_type=Profile.USER_TYPE_STAFF)
    client.force_login(user)

    response = client.get(reverse("registration:signin"), HTTP_HOST="localhost")

    assert response.status_code == 302
    assert response.url == settings.LOGIN_REDIRECT_URL


def test_signin_get_renders_business_context(client):
    business = create_business(default_country_code="kr")

    response = client.get(reverse("registration:signin"), HTTP_HOST="localhost")

    assert response.status_code == 200
    assert response.context["business_id"] == business.business_id
    assert response.context["country_code"] == business.default_country_code


def test_signin_post_returns_402_for_inactive_user(client):
    create_business()
    user = create_auth_profile(
        email="inactive@example.com",
        user_type=Profile.USER_TYPE_STAFF,
        is_active=False,
    )

    response = client.post(
        reverse("registration:signin"),
        {"email": user.email, "password": "secret123"},
        HTTP_HOST="localhost",
    )

    assert response.status_code == 402
    assert "User is not activated." in response.context["signin_form"].errors["password"]


def test_signin_post_redirects_customer_users_to_customer_home(client):
    create_business()
    user = create_auth_profile(
        email="customer@example.com",
        user_type=Profile.USER_TYPE_CUSTOMER,
    )

    response = client.post(
        reverse("registration:signin"),
        {"email": user.email, "password": "secret123"},
        HTTP_HOST="localhost",
    )

    assert response.status_code == 302
    assert response.url == settings.CUSTOMER_LOGIN_REDIRECT_URL


def test_signin_post_honors_redirect_url(client):
    create_business()
    user = create_auth_profile(
        email="staff@example.com",
        user_type=Profile.USER_TYPE_STAFF,
    )

    response = client.post(
        reverse("registration:signin"),
        {
            "email": user.email,
            "password": "secret123",
            "redirect_url": "/after-signin/",
        },
        HTTP_HOST="localhost",
    )

    assert response.status_code == 302
    assert response.url == "/after-signin/"


def test_customer_signin_redirects_staff_users_to_staff_home(client):
    create_business()
    user = create_auth_profile(
        email="staff-portal@example.com",
        user_type=Profile.USER_TYPE_STAFF,
    )

    response = client.post(
        reverse("registration:customer_signin"),
        {"email": user.email, "password": "secret123"},
        HTTP_HOST="localhost",
    )

    assert response.status_code == 302
    assert response.url == settings.LOGIN_REDIRECT_URL


def test_signup_post_bootstraps_first_superuser(client):
    create_business()

    response = client.post(
        reverse("registration:signup"),
        {
            "first_name": "First Owner",
            "email": "owner@example.com",
            "phone": "+12125552368",
            "password": "secret123",
            "password_2": "secret123",
            "message_consent": "on",
        },
        HTTP_HOST="localhost",
    )

    user = Profile.objects.get(email="owner@example.com", business_id=1)
    assert response.status_code == 302
    assert response.url == settings.LOGIN_REDIRECT_URL
    assert user.is_superuser is True
    assert user.is_staff is True
    assert user.is_active is True
    assert user.user_type == Profile.USER_TYPE_STAFF


def test_signup_form_uses_separate_first_and_last_name_fields():
    form = SignupForm()

    assert list(form.fields)[:2] == ["first_name", "last_name"]
    assert form.fields["first_name"].widget.attrs["placeholder"] == "First name"
    assert form.fields["last_name"].widget.attrs["placeholder"] == "Last name"


def test_signup_post_saves_separate_first_and_last_names(client):
    create_business()

    response = client.post(
        reverse("registration:signup"),
        {
            "first_name": "First",
            "last_name": "Owner",
            "email": "separate-owner@example.com",
            "phone": "+12125552368",
            "password": "secret123",
            "password_2": "secret123",
            "message_consent": "on",
        },
        HTTP_HOST="localhost",
    )

    user = Profile.objects.get(email="separate-owner@example.com", business_id=1)
    assert response.status_code == 302
    assert user.first_name == "First"
    assert user.last_name == "Owner"


def test_signup_post_duplicate_email_re_renders_form(client):
    create_business()
    create_profile(
        email="duplicate@example.com",
        business_id=1,
        user_type=Profile.USER_TYPE_CUSTOMER,
    )

    response = client.post(
        reverse("registration:signup"),
        {
            "first_name": "Duplicate User",
            "email": "duplicate@example.com",
            "phone": "+12125552368",
            "password": "secret123",
            "password_2": "secret123",
            "message_consent": "on",
        },
        HTTP_HOST="localhost",
    )

    assert response.status_code == 200
    assert "A user with this email already exists" in response.context["signup_form"].errors["email"]
    assert Profile.objects.filter(email="duplicate@example.com", business_id=1).count() == 1


def test_create_password_redirects_without_updating_on_mismatch(client):
    create_business()
    user = create_auth_profile(email="password-mismatch@example.com", password="oldpass123")
    client.force_login(user)

    response = client.post(
        reverse("registration:new-password"),
        {
            "new_password_form": "1",
            "password": "newpass123",
            "password_again": "different123",
        },
        HTTP_HOST="localhost",
        HTTP_REFERER="/back/",
    )

    user.refresh_from_db()
    assert response.status_code == 302
    assert response.url == "/back/"
    assert user.check_password("oldpass123")


def test_create_password_updates_password_and_redirects_back(client):
    create_business()
    user = create_auth_profile(email="password-update@example.com", password="oldpass123")
    client.force_login(user)

    response = client.post(
        reverse("registration:new-password"),
        {
            "new_password_form": "1",
            "password": "newpass123",
            "password_again": "newpass123",
        },
        HTTP_HOST="localhost",
        HTTP_REFERER="/back/",
    )

    user.refresh_from_db()
    assert response.status_code == 302
    assert response.url == "/back/"
    assert user.check_password("newpass123")
