from unittest.mock import patch

import pytest
from django.contrib.auth.models import Group
from django.http import Http404, HttpResponse
from django.test import RequestFactory, override_settings

from administration.auth_backend import CustomAuthBackend
from administration.context_processors import language_list, studio_image
from administration.location_management import (
    get_default_location_for_business,
    is_location_management_enabled,
)
from administration.models import DaysOfOperation, DomainToBusinessMapping, Location
from registration.controller import return_business_id_for_domain
from registration.utils.authentication import (
    anonymous_required,
    authenticate_with_email,
    can_access,
    get_permission_group_choices,
    get_permission_group_names,
    verify_no_superuser_exists,
)
from ruoom.storages import MediaStore
from ruoom.utils import load_plugin_statics, load_plugin_urls
from tests.factories import create_business, create_location, create_profile


pytestmark = pytest.mark.django_db


@override_settings(ENABLE_LOCATION_MANAGEMENT=False)
def test_location_management_flag_reads_setting():
    assert is_location_management_enabled() is False


def test_get_default_location_for_business_returns_existing_location():
    existing = create_location(name="Existing Location", business_id=77)

    location = get_default_location_for_business(77)

    assert location.pk == existing.pk


def test_get_default_location_for_business_can_skip_creation():
    assert get_default_location_for_business(404, create_if_missing=False) is None


def test_get_default_location_for_business_creates_location_and_days():
    business = create_business(
        business_id=88,
        default_country_code="kr",
        time_zone_string="Asia/Seoul",
    )

    location = get_default_location_for_business(business.business_id)

    assert location.business_id == business.business_id
    assert location.name == "Default Location"
    assert location.country_code == Location.COUNTRY_CODE_KR
    assert location.time_zone_string == "Asia/Seoul"
    assert location.currency == Location.CURRENCY_WON
    assert DaysOfOperation.objects.filter(location=location, is_checked=True).count() == len(DaysOfOperation.days)


def test_return_business_id_for_domain_matches_local_urls(settings):
    settings.LOCAL_URLS = ["http://localhost:8000", "http://127.0.0.1:8000"]
    create_business(business_id=1)

    assert return_business_id_for_domain("localhost") == 1


def test_return_business_id_for_domain_uses_domain_mapping(settings):
    settings.LOCAL_URLS = []
    create_business(business_id=1)
    mapped_business = create_business(business_id=22, name="Mapped Business")
    DomainToBusinessMapping.objects.create(domain="events.example.com", business=mapped_business)

    assert return_business_id_for_domain("events.example.com") == 22
    assert return_business_id_for_domain("unknown.example.com") == 1


def test_custom_auth_backend_authenticates_matching_user_password():
    user = create_profile(
        email="backend@example.com",
        business_id=1,
        username="backend-user",
    )
    user.set_password("secret123")
    user.save(update_fields=["password"])
    request = RequestFactory().post("/", HTTP_HOST="localhost")

    backend = CustomAuthBackend()

    authenticated = backend.authenticate(request, username="backend-user", password="secret123")

    assert authenticated.pk == user.pk
    assert backend.authenticate(request, username="backend-user", password="wrong") is None
    assert backend.get_user(user.pk).pk == user.pk
    assert backend.get_user(999999) is None


@override_settings(
    RESTRICTED_PATH_GROUPS=("checkin", "customforms"),
    SUPERUSER_ONLY_PATH_GROUPS=("admin",),
    DEFAULT_PATH_GROUPS=("staff", "customer"),
)
def test_permission_group_helpers_include_and_filter_defaults(monkeypatch):
    monkeypatch.setattr(
        "registration.utils.authentication.get_plugin_permission_groups",
        lambda: ("booking", "customforms"),
    )

    names = get_permission_group_names()
    no_defaults = get_permission_group_names(include_default=False)
    choices = dict(get_permission_group_choices())

    assert names == ("checkin", "customforms", "admin", "booking", "staff", "customer")
    assert no_defaults == ("checkin", "customforms", "admin", "booking")
    assert choices["customforms"] == "Customforms Page"


def test_verify_no_superuser_exists_blocks_when_superuser_present():
    create_profile(email="owner@example.com", is_superuser=True, user_type="staff")
    request = RequestFactory().get("/")

    @verify_no_superuser_exists
    def protected(_request):
        return HttpResponse("ok")

    with pytest.raises(Http404):
        protected(request)


def test_anonymous_required_redirects_authenticated_user():
    request = RequestFactory().get("/")
    request.user = create_profile(email="anon-required@example.com")

    @anonymous_required
    def public_view(_request):
        return HttpResponse("ok")

    response = public_view(request)

    assert response.status_code == 302


def test_authenticate_with_email_and_can_access_behave_as_expected():
    user = create_profile(email="grouped@example.com", user_type="staff")
    user.set_password("secret123")
    user.save(update_fields=["password"])
    group, _created = Group.objects.get_or_create(name="customforms")
    user.groups.add(group)

    assert authenticate_with_email("grouped@example.com", "secret123", user.business_id).pk == user.pk
    assert authenticate_with_email("grouped@example.com", "wrong", user.business_id) is None
    assert can_access(user, "customforms") is True
    assert can_access(user, "admin") is False
    user.is_superuser = True
    assert can_access(user, "anything") is True


@override_settings(
    FIRST_TIME_PASS="first-time-password",
    DEFAULT_FILE_STORAGE="django.core.files.storage.FileSystemStorage",
    MEDIA_URL="/media/",
    GOOGLE_PLACES_API_KEY="places-key",
)
def test_studio_image_returns_default_context_for_anonymous_user(monkeypatch):
    request = RequestFactory().get("/")
    request.user = type("AnonymousLike", (), {"is_authenticated": False})()
    monkeypatch.setattr("administration.context_processors.get_enabled_plugin_names", lambda: [])
    monkeypatch.setattr("administration.context_processors.get_plugin_navigation_items", lambda: [])
    monkeypatch.setattr("administration.context_processors.get_plugin_settings_tabs", lambda: [])

    context = studio_image(request)

    assert context == {"studio_setting_image": "img/ruoom_logo.png"}


@override_settings(
    FIRST_TIME_PASS="first-time-password",
    DEFAULT_FILE_STORAGE="django.core.files.storage.FileSystemStorage",
    MEDIA_URL="/media/",
    GOOGLE_PLACES_API_KEY="places-key",
)
def test_studio_image_builds_authenticated_branding_context(monkeypatch):
    business = create_business(business_id=31, default_country_code="kr")
    profile = create_profile(email="context@example.com", business_id=business.business_id)
    profile.password = "first-time-password"
    request = RequestFactory().get("/")
    request.user = type("AuthenticatedWrapper", (), {"is_authenticated": True, "profile": profile})()

    class DummyStudioImage:
        url = "/media/branding/logo.png"
        path = "C:\\missing\\logo.png"

    business.studio_image = DummyStudioImage()
    monkeypatch.setattr("administration.context_processors.Business.objects.filter", lambda **kwargs: type("QS", (), {"first": lambda self: business})())
    monkeypatch.setattr("administration.context_processors.get_enabled_plugin_names", lambda: ["digitalproducts"])
    monkeypatch.setattr("administration.context_processors.get_plugin_navigation_items", lambda: ["nav"])
    monkeypatch.setattr("administration.context_processors.get_plugin_settings_tabs", lambda: ["tab"])
    monkeypatch.setattr("administration.context_processors.is_staff_page_enabled", lambda: True)
    monkeypatch.setattr("administration.context_processors.is_location_management_enabled", lambda: True)
    monkeypatch.setattr("administration.context_processors.os.path.exists", lambda path: True)

    context = studio_image(request)

    assert context["first_time"] is True
    assert context["country_code"] == "kr"
    assert context["plugins"] == ["digitalproducts"]
    assert context["plugin_navigation_items"] == ["nav"]
    assert context["plugin_settings_tabs"] == ["tab"]
    assert context["staff_page_enabled"] is True
    assert context["location_management_enabled"] is True
    assert context["GOOGLE_PLACES_API_KEY"] == "places-key"
    assert context["store_plugins"] is True
    assert context["studio_setting_image"] == "branding/logo.png"


def test_language_list_exposes_profile_languages():
    assert language_list(None) == {"languages": create_profile().LANGUAGES}


def test_load_plugin_urls_handles_import_errors(monkeypatch):
    monkeypatch.setattr("ruoom.utils.get_enabled_plugin_names", lambda: ["broken"])
    monkeypatch.setattr("ruoom.utils.load_plugin_metadata", lambda _name: None)
    monkeypatch.setattr("ruoom.utils.include", lambda *args, **kwargs: (_ for _ in ()).throw(ImportError("boom")))

    assert load_plugin_urls() == []


def test_load_plugin_statics_collects_existing_static_dirs(monkeypatch):
    monkeypatch.setattr("ruoom.utils.get_enabled_plugin_names", lambda: ["booking", "customforms"])
    monkeypatch.setattr("ruoom.utils.get_plugins_dir", lambda: "C:\\plugins")
    monkeypatch.setattr(
        "ruoom.utils.os.path.isdir",
        lambda path: path.endswith("booking\\static"),
    )

    static_dirs = load_plugin_statics("C:\\repo")

    assert static_dirs == ["C:\\plugins\\booking\\static"]


def test_media_store_configuration_is_stable():
    assert MediaStore.location == "media"
    assert MediaStore.file_overwrite is False
