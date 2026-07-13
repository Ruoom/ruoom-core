import pytest
from django.conf import settings
from django.http import QueryDict
from django.urls import reverse
from unittest.mock import patch

from administration.forms import CreateUserForm
from registration.models import Profile
from tests.factories import create_business, create_location, create_profile


pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def disable_superuser_bootstrap(settings):
    settings.FORCE_SUPERUSER_CREATION = False


def build_user_form_data(**overrides):
    data = QueryDict("", mutable=True)
    data.update(
        {
            "first_name": "Staff",
            "last_name": "Member",
            "email": "staff-member@example.com",
            "message_consent": "on",
            "staff_is_active": "on",
        }
    )
    permissions = overrides.pop("Permissions", [])
    locations = overrides.pop("locations", [])
    for key, value in overrides.items():
        data[key] = value
    data.setlist("Permissions", permissions)
    data.setlist("locations", [str(location) for location in locations])
    return data


def test_dashboard_renders_for_staff_with_default_location(client):
    create_business()
    location = create_location(business_id=1, time_zone_string="UTC")
    staff = create_profile(
        email="dashboard-staff@example.com",
        business_id=1,
        user_type=Profile.USER_TYPE_STAFF,
        default_location=location,
    )
    client.force_login(staff)

    response = client.get(reverse("administration:dashboard"), HTTP_HOST="localhost")

    assert response.status_code == 200
    assert response.context["location"] == location
    assert list(response.context["location_list"]) == [location]


def test_dashboard_redirects_customers_to_customer_home(client):
    create_business()
    customer = create_profile(
        email="dashboard-customer@example.com",
        business_id=1,
        user_type=Profile.USER_TYPE_CUSTOMER,
    )
    client.force_login(customer)

    response = client.get(reverse("administration:dashboard"), HTTP_HOST="localhost")

    assert response.status_code == 302
    assert response.url == settings.CUSTOMER_LOGIN_REDIRECT_URL


def test_customer_page_duplicate_email_reopens_modal(client):
    create_business()
    admin_user = create_profile(
        email="admin@example.com",
        business_id=1,
        user_type=Profile.USER_TYPE_STAFF,
        is_superuser=True,
    )
    create_profile(
        email="duplicate-customer@example.com",
        business_id=1,
        user_type=Profile.USER_TYPE_CUSTOMER,
    )
    client.force_login(admin_user)

    response = client.post(
        reverse("administration:customers"),
        {
            "new_customer": "1",
            "first_name": "New",
            "last_name": "Customer",
            "email": "duplicate-customer@example.com",
            "phone_with_code": "+12125552368",
            "password": "secret123",
        },
        HTTP_HOST="localhost",
    )

    assert response.status_code == 200
    assert response.context["open_customer_modal"] == "true"
    assert "A user with this email already exists" in response.context["customer_form"].errors["email"]
    assert Profile.objects.filter(email="duplicate-customer@example.com", business_id=1).count() == 1


def test_customer_page_get_lists_existing_profiles(client):
    business = create_business(default_country_code="kr")
    admin_user = create_profile(
        email="admin@example.com",
        business_id=1,
        user_type=Profile.USER_TYPE_STAFF,
        is_superuser=True,
    )
    existing_customer = create_profile(
        email="existing-customer@example.com",
        business_id=1,
        user_type=Profile.USER_TYPE_CUSTOMER,
    )
    client.force_login(admin_user)

    response = client.get(reverse("administration:customers"), HTTP_HOST="localhost")

    assert response.status_code == 200
    assert response.context["default_country_code"] == business.default_country_code
    assert existing_customer in response.context["customers"]


def test_customer_page_download_csv_redirects_to_export(client):
    create_business()
    admin_user = create_profile(
        email="admin@example.com",
        business_id=1,
        user_type=Profile.USER_TYPE_STAFF,
        is_superuser=True,
    )
    client.force_login(admin_user)

    response = client.post(
        reverse("administration:customers"),
        {"download_csv": "1"},
        HTTP_HOST="localhost",
    )

    assert response.status_code == 302
    assert response.url == reverse("administration:export_profile")


def test_customer_import_sample_csv_downloads(client):
    create_business()
    admin_user = create_profile(
        email="admin@example.com",
        business_id=1,
        user_type=Profile.USER_TYPE_STAFF,
        is_superuser=True,
    )
    client.force_login(admin_user)

    response = client.get(
        reverse("administration:download_media", args=["sample.csv"]),
        HTTP_HOST="localhost",
    )

    assert response.status_code == 200
    assert response.content.startswith(b"Email,First Name,Last Name")


def test_admin_delete_user_downgrades_staff_to_customer(client):
    create_business()
    admin_user = create_profile(
        email="owner@example.com",
        business_id=1,
        user_type=Profile.USER_TYPE_STAFF,
        is_superuser=True,
    )
    staff_user = create_profile(
        email="team@example.com",
        business_id=1,
        user_type=Profile.USER_TYPE_STAFF,
    )
    client.force_login(admin_user)

    response = client.post(
        reverse("administration:admin"),
        {"delete_user": "1", "staff_id": str(staff_user.id)},
        HTTP_HOST="localhost",
    )

    staff_user.refresh_from_db()
    assert response.status_code == 302
    assert response.url == reverse("administration:admin")
    assert staff_user.user_type == Profile.USER_TYPE_CUSTOMER


def test_admin_get_renders_staff_list_and_forms(client):
    create_business()
    admin_user = create_profile(
        email="owner@example.com",
        business_id=1,
        user_type=Profile.USER_TYPE_STAFF,
        is_superuser=True,
    )
    staff_user = create_profile(
        email="team@example.com",
        business_id=1,
        user_type=Profile.USER_TYPE_STAFF,
    )
    client.force_login(admin_user)

    response = client.get(reverse("administration:admin"), HTTP_HOST="localhost")

    assert response.status_code == 200
    assert staff_user in response.context["staffs"]
    assert response.context["username"] == admin_user.email


def test_admin_get_staff_data_returns_prefilled_form_markup(client):
    create_business()
    admin_user = create_profile(
        email="owner@example.com",
        business_id=1,
        user_type=Profile.USER_TYPE_STAFF,
        is_superuser=True,
    )
    staff_user = create_profile(
        email="team@example.com",
        business_id=1,
        user_type=Profile.USER_TYPE_STAFF,
        first_name="Team",
    )
    client.force_login(admin_user)

    response = client.get(
        reverse("administration:admin"),
        {"TYPE": "get_staff_data", "staff_id": str(staff_user.id)},
        HTTP_HOST="localhost",
    )

    content = response.content.decode("utf-8")
    assert response.status_code == 200
    assert 'name="email"' in content
    assert staff_user.email in content


def test_admin_post_creates_user_and_sends_reset_email(client):
    create_business()
    admin_user = create_profile(
        email="owner@example.com",
        business_id=1,
        user_type=Profile.USER_TYPE_STAFF,
        is_superuser=True,
    )
    client.force_login(admin_user)

    with patch("administration.views.reset_password_email_send") as email_mock:
        response = client.post(
            reverse("administration:admin"),
            {
                "new_user": "1",
                "first_name": "New",
                "last_name": "Teammate",
                "email": "new-teammate@example.com",
                "staff_is_active": "on",
            },
            HTTP_HOST="localhost",
        )

    created_user = Profile.objects.get(email="new-teammate@example.com", business_id=1)
    assert response.status_code == 302
    assert response.url == reverse("administration:admin")
    assert created_user.user_type == Profile.USER_TYPE_STAFF
    email_mock.assert_called_once()


def test_create_user_form_rejects_duplicate_email_within_business():
    create_business()
    acting_user = create_profile(
        email="acting@example.com",
        business_id=1,
        user_type=Profile.USER_TYPE_STAFF,
        is_superuser=True,
    )
    create_profile(
        email="duplicate-staff@example.com",
        business_id=1,
        user_type=Profile.USER_TYPE_STAFF,
    )

    form = CreateUserForm(
        build_user_form_data(email="duplicate-staff@example.com"),
        user=acting_user,
        business_id=1,
    )

    assert not form.is_valid()
    assert "A user with this email already exists" in form.errors["email"]


def test_create_user_form_rejects_locations_from_other_business():
    create_business()
    create_business(business_id=2, name="Second Business")
    acting_user = create_profile(
        email="acting@example.com",
        business_id=1,
        user_type=Profile.USER_TYPE_STAFF,
        is_superuser=True,
    )
    other_location = create_location(business_id=2, name="Other Location")

    form = CreateUserForm(
        build_user_form_data(locations=[other_location.id]),
        user=acting_user,
        business_id=1,
    )

    assert not form.is_valid()
    assert "does not belong to business 1" in form.errors["locations"][0]


def test_create_user_form_save_assigns_staff_location_and_permissions():
    create_business()
    acting_user = create_profile(
        email="acting@example.com",
        business_id=1,
        user_type=Profile.USER_TYPE_STAFF,
        is_superuser=True,
    )
    location = create_location(business_id=1)
    permission = CreateUserForm(user=acting_user).fields["permissions"].choices[0][0]
    form = CreateUserForm(
        build_user_form_data(
            email="created-staff@example.com",
            Permissions=[permission],
            locations=[location.id],
        ),
        user=acting_user,
        business_id=1,
    )

    assert form.is_valid(), form.errors

    saved_user = form.save()

    assert saved_user.user_type == Profile.USER_TYPE_STAFF
    assert saved_user.staff_at_locations.filter(id=location.id).exists()
    assert saved_user.groups.filter(name=permission).exists()


def test_staff_page_get_renders_current_staff_and_locations(client):
    create_business()
    location = create_location(business_id=1)
    admin_user = create_profile(
        email="owner@example.com",
        business_id=1,
        user_type=Profile.USER_TYPE_STAFF,
        is_superuser=True,
    )
    staff_user = create_profile(
        email="teacher@example.com",
        business_id=1,
        user_type=Profile.USER_TYPE_STAFF,
    )
    client.force_login(admin_user)

    response = client.get(reverse("administration:staff"), HTTP_HOST="localhost")

    assert response.status_code == 200
    assert staff_user in response.context["staff_member"]
    assert location in response.context["locations"]
