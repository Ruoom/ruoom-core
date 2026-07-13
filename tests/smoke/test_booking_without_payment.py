import pytest
from django.test import Client

from ruoom.plugin_metadata import is_plugin_enabled
from tests.factories import create_business, create_location, create_service


@pytest.mark.django_db
def test_booking_calendar_view_renders_with_payment_not_installed(settings):
    settings.INSTALLED_APPS = [
        app_name for app_name in settings.INSTALLED_APPS if not app_name.startswith("plugins.payment")
    ]
    create_business(name="Booking Only Business")
    location = create_location()
    service = create_service(location=location)
    client = Client()

    response = client.get("/booking/calendar/", HTTP_HOST="localhost")

    assert is_plugin_enabled("payment") is False
    assert response.status_code == 200
    assert service.class_name()
