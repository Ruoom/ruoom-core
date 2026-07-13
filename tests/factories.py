from datetime import timedelta

from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

from administration.models import Business, DomainToBusinessMapping, Location, Room
from plugins.booking.models import Service, ServiceType
from plugins.appointments.models import AppointmentType
from plugins.customforms.models import (
    AppointmentTypeCustomForm,
    AppointmentTypeCustomFormField,
    CustomFormAssignment,
    GoogleFormOAuthToken,
)
from plugins.mailerlite.models import MailerLiteSettings
from plugins.payment.models import Cart, PaymentSettings
from plugins.single_sign_on.models import DisposableAuthenticationToken
from registration.models import Profile


def create_business(**overrides):
    data = {
        "name": "Test Business",
        "business_id": 1,
        "default_country_code": Business.COUNTRY_CODE_US,
        "late_cancel_hours": 2,
        "time_zone_string": "UTC",
    }
    data.update(overrides)
    return Business.objects.create(**data)


def create_location(**overrides):
    business_id = overrides.pop("business_id", 1)
    data = {
        "name": "Main Location",
        "business_id": business_id,
        "country_code": Location.COUNTRY_CODE_US,
        "time_zone_string": "UTC",
        "currency": Location.CURRENCY_DOLLAR,
    }
    data.update(overrides)
    return Location.objects.create(**data)


def create_domain_mapping(**overrides):
    business = overrides.pop("business", None) or create_business()
    data = {
        "domain": "example.com",
        "business": business,
    }
    data.update(overrides)
    return DomainToBusinessMapping.objects.create(**data)


def create_room(**overrides):
    location = overrides.pop("location", None) or create_location()
    business_id = overrides.pop("business_id", location.business_id)
    data = {
        "name": "Studio A",
        "location": location,
        "business_id": business_id,
    }
    data.update(overrides)
    return Room.objects.create(**data)


def create_profile(**overrides):
    business_id = overrides.pop("business_id", 1)
    email = overrides.pop("email", f"user{Profile.objects.count() + 1}@example.com")
    data = {
        "username": Profile.username_for_identity(email, business_id),
        "first_name": "Test",
        "last_name": "User",
        "email": email,
        "business_id": business_id,
    }
    data.update(overrides)
    return Profile.objects.create(**data)


def create_teacher(**overrides):
    return create_profile(is_teacher=True, user_type=Profile.USER_TYPE_STAFF, **overrides)


def create_service_type(**overrides):
    location = overrides.pop("location", None) or create_location()
    business_id = overrides.pop("business_id", location.business_id)
    data = {
        "name": "Yoga",
        "location": location,
        "business_id": business_id,
        "price": 25,
    }
    data.update(overrides)
    return ServiceType.objects.create(**data)


def create_service(**overrides):
    service_type = overrides.pop("class_type", None) or create_service_type()
    location = overrides.pop("location", None) or service_type.location
    room = overrides.pop("room", None) or create_room(location=location, business_id=location.business_id)
    teacher = overrides.pop("teacher", None) or create_teacher(
        business_id=service_type.business_id,
        default_location=location,
    )
    data = {
        "class_type": service_type,
        "teacher": teacher,
        "location": location,
        "room": room,
        "business_id": service_type.business_id,
        "scheduled_time": timezone.now(),
        "duration": timedelta(hours=1),
        "price": service_type.price,
        "capacity": 10,
    }
    data.update(overrides)
    return Service.objects.create(**data)


def create_custom_form(**overrides):
    data = {
        "business_id": 1,
        "name": "Intake Form",
    }
    data.update(overrides)
    return AppointmentTypeCustomForm.objects.create(**data)


def create_custom_form_field(**overrides):
    form = overrides.pop("form", None) or create_custom_form()
    data = {
        "form": form,
        "label": "Email",
        "field_type": "email",
        "required": True,
    }
    data.update(overrides)
    return AppointmentTypeCustomFormField.objects.create(**data)


def create_appointment_type(**overrides):
    location = overrides.pop("location", None) or create_location()
    business_id = overrides.pop("business_id", location.business_id)
    data = {
        "name": "Consultation",
        "business_id": business_id,
        "location": location,
        "price": 50,
        "duration": timedelta(minutes=30),
    }
    data.update(overrides)
    return AppointmentType.objects.create(**data)


def create_custom_form_assignment(**overrides):
    form = overrides.pop("form", None) or create_custom_form()
    content_object = overrides.pop("content_object", None) or create_appointment_type(
        business_id=form.business_id
    )
    content_type = overrides.pop(
        "content_type", ContentType.objects.get_for_model(content_object, for_concrete_model=False)
    )
    data = {
        "business_id": form.business_id,
        "form": form,
        "use_case": CustomFormAssignment.USE_CASE_APPOINTMENT_TYPE,
        "content_type": content_type,
        "object_id": content_object.pk,
        "is_required": True,
        "is_active": True,
    }
    data.update(overrides)
    return CustomFormAssignment.objects.create(**data)


def create_google_form_oauth_token(**overrides):
    form = overrides.pop("custom_form", None) or create_custom_form(is_google_synced=True)
    data = {
        "custom_form": form,
        "connected_email": "owner@example.com",
        "access_token": "token",
        "refresh_token": "refresh",
    }
    data.update(overrides)
    return GoogleFormOAuthToken.objects.create(**data)


def create_payment_settings(**overrides):
    business = overrides.pop("business", None) or create_business()
    data = {
        "business": business,
        "refund_policy": "Refunds allowed up to 24 hours before class.",
        "refund_popup": True,
    }
    data.update(overrides)
    return PaymentSettings.objects.create(**data)


def create_mailerlite_settings(**overrides):
    business = overrides.pop("business", None) or create_business()
    data = {
        "business": business,
        "group_id": "group-1",
        "group_name": "Main Group",
    }
    data.update(overrides)
    return MailerLiteSettings.objects.create(**data)


def create_disposable_authentication_token(**overrides):
    target_profile = overrides.pop("target_profile", None) or create_profile()
    data = {
        "target_profile": target_profile,
    }
    data.update(overrides)
    return DisposableAuthenticationToken.objects.create(**data)


def create_cart(**overrides):
    customer = overrides.pop("customer", None) or create_profile()
    service = overrides.pop("service", None) or create_service(business_id=customer.business_id)
    location = overrides.pop("location", None) or service.location
    data = {
        "customer": customer,
        "business_id": customer.business_id,
        "location": location,
        "item_type": "service_register",
        "product_id": service.id,
        "product_quantity": 1,
    }
    data.update(overrides)
    return Cart.objects.create(**data)
