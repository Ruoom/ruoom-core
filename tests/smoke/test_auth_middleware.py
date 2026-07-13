import pytest
from django.http import Http404, HttpResponse
from django.test import RequestFactory, override_settings
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth.models import Group

from registration.middleware.authentication import AuthenticationMiddleware
from tests.factories import create_profile


def middleware_response(request):
    return HttpResponse("ok")


@pytest.mark.django_db
@override_settings(FORCE_SUPERUSER_CREATION=False, ENABLE_PER_PAGE_PERMISSIONS=True)
def test_public_url_pattern_is_accessible_without_authentication():
    request = RequestFactory().get("/booking/calendar", HTTP_HOST="localhost")
    request.user = AnonymousUser()

    response = AuthenticationMiddleware(middleware_response)(request)

    assert response.status_code == 200


@pytest.mark.django_db
@override_settings(FORCE_SUPERUSER_CREATION=False, ENABLE_PER_PAGE_PERMISSIONS=True)
def test_password_login_fallback_remains_public():
    request = RequestFactory().get("/registration/signin/", HTTP_HOST="localhost")
    request.user = AnonymousUser()

    response = AuthenticationMiddleware(middleware_response)(request)

    assert response.status_code == 200


@pytest.mark.django_db
@override_settings(FORCE_SUPERUSER_CREATION=True, ENABLE_PER_PAGE_PERMISSIONS=True)
def test_health_is_accessible_during_superuser_bootstrap():
    request = RequestFactory().get("/health/", HTTP_HOST="localhost")
    request.user = AnonymousUser()

    response = AuthenticationMiddleware(middleware_response)(request)

    assert response.status_code == 200


@pytest.mark.django_db
@override_settings(FORCE_SUPERUSER_CREATION=True, ENABLE_PER_PAGE_PERMISSIONS=True)
def test_metrics_reaches_view_during_superuser_bootstrap():
    request = RequestFactory().get("/api/metrics/", HTTP_HOST="unregistered.example.com")
    request.user = AnonymousUser()

    response = AuthenticationMiddleware(middleware_response)(request)

    assert response.status_code == 200


@pytest.mark.django_db
@override_settings(FORCE_SUPERUSER_CREATION=False, ENABLE_PER_PAGE_PERMISSIONS=True)
def test_private_url_redirects_to_login_without_authentication():
    request = RequestFactory().get("/administration/dashboard/", HTTP_HOST="localhost")
    request.user = AnonymousUser()

    response = AuthenticationMiddleware(middleware_response)(request)

    assert response.status_code == 302
    assert response.url == "/otp/signin/"


@pytest.mark.django_db
@override_settings(FORCE_SUPERUSER_CREATION=False, ENABLE_PER_PAGE_PERMISSIONS=True)
def test_private_ajax_url_redirects_to_login_without_authentication():
    request = RequestFactory().get(
        "/booking/ajax/add_booking_cart/",
        HTTP_HOST="localhost",
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
    )
    request.user = AnonymousUser()

    response = AuthenticationMiddleware(middleware_response)(request)

    assert response.status_code == 302
    assert response.url == "/otp/signin/"


@pytest.mark.django_db
@override_settings(FORCE_SUPERUSER_CREATION=False, ENABLE_PER_PAGE_PERMISSIONS=True)
def test_checkout_without_guest_or_cart_redirects_to_login():
    request = RequestFactory().get("/payment/checkout", HTTP_HOST="localhost")
    request.user = AnonymousUser()

    response = AuthenticationMiddleware(middleware_response)(request)

    assert response.status_code == 302
    assert response.url == "/otp/signin/"


@pytest.mark.django_db
@override_settings(FORCE_SUPERUSER_CREATION=False, ENABLE_PER_PAGE_PERMISSIONS=True)
def test_checkout_with_cart_query_is_public():
    request = RequestFactory().get("/payment/checkout", {"cart": "1"}, HTTP_HOST="localhost")
    request.user = AnonymousUser()

    response = AuthenticationMiddleware(middleware_response)(request)

    assert response.status_code == 200


@pytest.mark.django_db
@override_settings(FORCE_SUPERUSER_CREATION=False, ENABLE_PER_PAGE_PERMISSIONS=True)
def test_checkout_guest_post_is_public():
    request = RequestFactory().post("/payment/checkout", {"new_customer_email": "guest@example.com"}, HTTP_HOST="localhost")
    request.user = AnonymousUser()

    response = AuthenticationMiddleware(middleware_response)(request)

    assert response.status_code == 200


@pytest.mark.django_db
@override_settings(FORCE_SUPERUSER_CREATION=False, ENABLE_PER_PAGE_PERMISSIONS=True)
def test_staff_only_url_raises_404_for_non_staff_user():
    request = RequestFactory().get("/admin/subscriptions", HTTP_HOST="localhost")
    request.user = AnonymousUser()

    with pytest.raises(Http404):
        AuthenticationMiddleware(middleware_response)(request)


@pytest.mark.django_db
@override_settings(FORCE_SUPERUSER_CREATION=False, ENABLE_PER_PAGE_PERMISSIONS=True)
def test_staff_only_ajax_url_raises_404_for_non_staff_user():
    request = RequestFactory().get(
        "/mailerlite/api/groups/",
        HTTP_HOST="localhost",
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
    )
    request.user = AnonymousUser()

    with pytest.raises(Http404):
        AuthenticationMiddleware(middleware_response)(request)


@pytest.mark.django_db
@override_settings(FORCE_SUPERUSER_CREATION=False, ENABLE_PER_PAGE_PERMISSIONS=True)
def test_plugin_staff_only_url_allows_ruoom_staff_profile():
    user = create_profile(email="ruoom-staff@example.com", user_type="staff", is_staff=False)
    request = RequestFactory().get("/booking/settings/", HTTP_HOST="localhost")
    request.user = user

    response = AuthenticationMiddleware(middleware_response)(request)

    assert response.status_code == 200


@pytest.mark.django_db
@override_settings(FORCE_SUPERUSER_CREATION=False, ENABLE_PER_PAGE_PERMISSIONS=True)
def test_admin_group_allows_permissions_page_without_superuser_flag():
    user = create_profile(email="admin-group@example.com", user_type="staff", is_superuser=False)
    admin_group, _created = Group.objects.get_or_create(name="admin")
    user.groups.add(admin_group)
    request = RequestFactory().get("/administration/permissions/", HTTP_HOST="localhost")
    request.user = user

    response = AuthenticationMiddleware(middleware_response)(request)

    assert response.status_code == 200


@pytest.mark.django_db
@override_settings(FORCE_SUPERUSER_CREATION=False, ENABLE_PER_PAGE_PERMISSIONS=True)
def test_public_ajax_url_is_accessible_without_authentication():
    request = RequestFactory().post(
        "/customforms/ajax/check-customform-singlesubmit",
        HTTP_HOST="localhost",
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
    )
    request.user = AnonymousUser()

    response = AuthenticationMiddleware(middleware_response)(request)

    assert response.status_code == 200
