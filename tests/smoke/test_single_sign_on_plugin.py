import pytest
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse
from django.test import Client, RequestFactory
from django.urls import reverse

from registration.middleware.authentication import AuthenticationMiddleware
from plugins.single_sign_on.models import DisposableAuthenticationToken
from registration.models import Profile
from tests.factories import (
    create_business,
    create_disposable_authentication_token,
    create_domain_mapping,
    create_profile,
)


pytestmark = pytest.mark.django_db


def test_sso_one_time_token_path_is_public_without_auth():
    request = RequestFactory().get("/sso/one-time/00000000-0000-0000-0000-000000000000/", HTTP_HOST="localhost")
    request.user = AnonymousUser()

    response = AuthenticationMiddleware(lambda req: HttpResponse("ok"))(request)

    assert response.status_code == 200


def test_sso_one_time_auth_logs_user_into_target_business():
    business = create_business()
    create_domain_mapping(business=business, domain="localhost")
    target_profile = create_profile(business_id=business.business_id, email="customer@example.com")
    token = create_disposable_authentication_token(target_profile=target_profile)
    client = Client()

    response = client.get(
        reverse("single_sign_on:one_time_token_auth", kwargs={"token": token.token}),
        HTTP_HOST="localhost",
    )

    assert response.status_code == 302
    assert response.url == "/customer/account-settings/"


def test_sso_redirect_requires_existing_target_profile_for_regular_users():
    source_business = create_business(business_id=1)
    target_business = create_business(business_id=2, name="Target Business")
    create_domain_mapping(business=source_business, domain="localhost")
    create_profile(
        business_id=source_business.business_id,
        email="admin-sso@example.com",
        is_staff=True,
        is_superuser=True,
    )
    source_profile = create_profile(
        business_id=source_business.business_id,
        email="person@example.com",
    )
    client = Client()
    client.force_login(source_profile)

    response = client.get(
        reverse("single_sign_on:sso_redirect", kwargs={"business_id": target_business.business_id}),
        HTTP_HOST="localhost",
    )

    assert response.status_code == 404
    assert not Profile.objects.filter(
        business_id=target_business.business_id,
        email=source_profile.email,
    ).exists()


def test_sso_redirect_allows_existing_target_profile():
    source_business = create_business(business_id=1)
    target_business = create_business(business_id=2, name="Target Business")
    create_domain_mapping(business=target_business, domain="localhost")
    create_profile(
        business_id=source_business.business_id,
        email="admin-existing@example.com",
        is_staff=True,
        is_superuser=True,
    )
    source_profile = create_profile(
        business_id=source_business.business_id,
        email="person-existing@example.com",
    )
    target_profile = create_profile(
        business_id=target_business.business_id,
        email="person-existing@example.com",
    )
    client = Client()
    client.force_login(source_profile)

    response = client.get(
        reverse("single_sign_on:sso_redirect", kwargs={"business_id": target_business.business_id}),
        HTTP_HOST="localhost",
    )

    assert response.status_code == 302
    assert "/sso/one-time/" in response.url
    assert DisposableAuthenticationToken.objects.filter(target_profile=target_profile).exists()


def test_sso_redirect_allows_superuser_to_provision_target_profile():
    source_business = create_business(business_id=1)
    target_business = create_business(business_id=2, name="Target Business")
    create_domain_mapping(business=target_business, domain="localhost")
    source_profile = create_profile(
        business_id=source_business.business_id,
        email="super-sso@example.com",
        is_staff=True,
        is_superuser=True,
    )
    client = Client()
    client.force_login(source_profile)

    response = client.get(
        reverse("single_sign_on:sso_redirect", kwargs={"business_id": target_business.business_id}),
        HTTP_HOST="localhost",
    )

    assert response.status_code == 302
    target_profile = Profile.objects.get(
        business_id=target_business.business_id,
        email=source_profile.email,
    )
    assert DisposableAuthenticationToken.objects.filter(target_profile=target_profile).exists()
