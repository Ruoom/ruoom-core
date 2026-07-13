from datetime import timedelta

import pytest
from django.test import override_settings
from django.utils import timezone

from plugins.booking.forms import CreateClassForm, CreateClassTypeForm
from plugins.booking.models import Service
from ruoom.ui_customization import get_booking_ui_customization
from tests.factories import create_business, create_location, create_service_type, create_teacher


def test_booking_ui_customization_defaults_preserve_service_wording():
    booking_ui = get_booking_ui_customization()

    assert booking_ui.labels.item_singular == "Service"
    assert booking_ui.labels.item_type_singular == "Service Type"
    assert booking_ui.text.add_item == "Add Service"
    assert booking_ui.features.show_service_types is True


@override_settings(
    PROJECT_UI_CUSTOMIZATION={
        "booking": {
            "labels": {
                "item_singular": "Event",
                "item_plural": "Events",
                "item_type_singular": "Event Type",
                "item_type_plural": "Event Types",
                "location_singular": "Venue",
                "location_plural": "Venues",
            },
            "features": {
                "show_service_types": False,
                "show_service_providers": False,
                "show_virtual_events": False,
                "show_checkin": False,
            },
        }
    }
)
def test_booking_ui_customization_resolves_project_overrides():
    booking_ui = get_booking_ui_customization()

    assert booking_ui.labels.item_singular == "Event"
    assert booking_ui.labels.item_plural == "Events"
    assert booking_ui.text.add_item == "Add Event"
    assert booking_ui.text.item_details == "Event Details"
    assert booking_ui.features.show_service_types is False
    assert booking_ui.features.show_service_providers is False
    assert booking_ui.features.show_virtual_events is False
    assert booking_ui.features.show_checkin is False


@pytest.mark.django_db
@override_settings(
    PROJECT_UI_CUSTOMIZATION={
        "booking": {
            "labels": {
                "item_singular": "Event",
                "item_type_singular": "Event Type",
            },
        }
    }
)
def test_booking_forms_use_customized_labels():
    business = create_business()
    location = create_location(business_id=business.business_id)
    create_service_type(business_id=business.business_id, location=location)

    service_form = CreateClassForm(business_id=business.business_id)
    type_form = CreateClassTypeForm(business_id=business.business_id)

    assert service_form.fields["name"].label == "Event Name"
    assert service_form.fields["class_type"].label == "Event Type"
    assert type_form.fields["name"].label == "Event Type"


@pytest.mark.django_db
def test_create_class_form_allows_blank_service_type():
    business = create_business()
    location = create_location(business_id=business.business_id)
    starts_at = timezone.now() + timedelta(days=5)

    form = CreateClassForm(
        business.business_id,
        data={
            "name": "Standalone RSVP",
            "scheduled_time": starts_at.strftime("%Y-%m-%d %H:%M:%S"),
            "duration": "0:01:00",
            "capacity": "10",
            "price": "0",
            "description": "",
        },
    )

    assert form.fields["class_type"].required is False
    assert form.is_valid(), form.errors
    service = form.save(commit=False)
    service.business_id = business.business_id
    service.location = location
    service.save()

    assert Service.objects.get(pk=service.pk).class_type is None


@pytest.mark.django_db
def test_create_class_form_accepts_register_by_before_service_start():
    business = create_business()
    location = create_location(business_id=business.business_id)
    service_type = create_service_type(business_id=business.business_id, location=location)
    teacher = create_teacher(business_id=business.business_id, default_location=location)
    starts_at = timezone.now() + timedelta(days=5)
    register_by = starts_at - timedelta(days=1)

    form = CreateClassForm(
        business.business_id,
        data={
            "class_type": service_type.pk,
            "name": "Workshop",
            "teacher": teacher.pk,
            "scheduled_time": starts_at.strftime("%Y-%m-%d %H:%M:%S"),
            "duration": "0:01:00",
            "capacity": "10",
            "register_by": register_by.strftime("%Y-%m-%d %H:%M:%S"),
            "price": "0",
            "description": "",
        },
    )

    assert form.is_valid(), form.errors
    service = form.save(commit=False)
    assert service.register_by is not None


@pytest.mark.django_db
def test_create_class_form_rejects_register_by_after_service_start():
    business = create_business()
    location = create_location(business_id=business.business_id)
    service_type = create_service_type(business_id=business.business_id, location=location)
    teacher = create_teacher(business_id=business.business_id, default_location=location)
    starts_at = timezone.now() + timedelta(days=5)
    register_by = starts_at + timedelta(hours=1)

    form = CreateClassForm(
        business.business_id,
        data={
            "class_type": service_type.pk,
            "name": "Workshop",
            "teacher": teacher.pk,
            "scheduled_time": starts_at.strftime("%Y-%m-%d %H:%M:%S"),
            "duration": "0:01:00",
            "capacity": "10",
            "register_by": register_by.strftime("%Y-%m-%d %H:%M:%S"),
            "price": "0",
            "description": "",
        },
    )

    assert form.is_valid() is False
    assert "register_by" in form.errors
