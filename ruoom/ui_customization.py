from dataclasses import dataclass

from django.conf import settings


@dataclass(frozen=True)
class BookingUIFeatures:
    show_service_types: bool
    show_service_providers: bool
    show_virtual_events: bool
    show_checkin: bool


@dataclass(frozen=True)
class BookingUILabels:
    item_singular: str
    item_plural: str
    item_type_singular: str
    item_type_plural: str
    location_singular: str
    location_plural: str


@dataclass(frozen=True)
class BookingUIText:
    add_item: str
    edit_item: str
    cancel_item: str
    item_details: str
    item_name: str
    item_type_singular: str
    item_type_plural: str
    create_new_item_type: str
    create_new_type_of_item: str
    edit_type_of_item: str
    multiday_item: str
    multiday_item_help: str
    virtual_item: str
    link_to_virtual_item: str
    registered_for_item: str
    choose_location: str


@dataclass(frozen=True)
class BookingUICustomization:
    features: BookingUIFeatures
    labels: BookingUILabels
    text: BookingUIText


def _project_ui_customization():
    return getattr(settings, "PROJECT_UI_CUSTOMIZATION", {})


def _booking_customization():
    return _project_ui_customization().get("booking", {})


def _booking_features():
    raw = _booking_customization().get("features", {})
    return BookingUIFeatures(
        show_service_types=raw.get("show_service_types", True),
        show_service_providers=raw.get("show_service_providers", True),
        show_virtual_events=raw.get("show_virtual_events", True),
        show_checkin=raw.get("show_checkin", True),
    )


def _booking_labels():
    raw = _booking_customization().get("labels", {})
    return BookingUILabels(
        item_singular=raw.get("item_singular", "Service"),
        item_plural=raw.get("item_plural", "Services"),
        item_type_singular=raw.get("item_type_singular", "Service Type"),
        item_type_plural=raw.get("item_type_plural", "Service Types"),
        location_singular=raw.get("location_singular", "Location"),
        location_plural=raw.get("location_plural", "Locations"),
    )


def _booking_text(labels):
    lower_item_singular = labels.item_singular.lower()
    lower_item_plural = labels.item_plural.lower()
    return BookingUIText(
        add_item=f"Add {labels.item_singular}",
        edit_item=f"Edit {labels.item_singular}",
        cancel_item=f"Cancel {labels.item_singular}",
        item_details=f"{labels.item_singular} Details",
        item_name=f"{labels.item_singular} Name",
        item_type_singular=labels.item_type_singular,
        item_type_plural=labels.item_type_plural,
        create_new_item_type=f"Create New {labels.item_type_singular}",
        create_new_type_of_item=f"Create a new type of {lower_item_singular}",
        edit_type_of_item=f"Edit type of {lower_item_singular}",
        multiday_item=f"Multiday {labels.item_singular}",
        multiday_item_help=(
            f"A multiday {lower_item_singular} will have a duration of days, "
            f"and be shown as an all-day event for each day. There is no start "
            f"time for multiday {lower_item_plural}."
        ),
        virtual_item=f"Virtual {labels.item_singular}",
        link_to_virtual_item=f"Link to Virtual {labels.item_singular}",
        registered_for_item=f"Registered for {lower_item_singular}",
        choose_location=f"Choose {labels.location_singular}",
    )


def get_booking_ui_customization():
    labels = _booking_labels()
    return BookingUICustomization(
        features=_booking_features(),
        labels=labels,
        text=_booking_text(labels),
    )


def context_processor(request):
    return {
        "booking_ui": get_booking_ui_customization(),
    }
