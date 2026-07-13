import json

import pytest
from django.test import Client, override_settings

from plugins.appointments.models import BookedAppointment
from plugins.customforms.models import CustomFormResponse
from tests.factories import (
    create_appointment_type,
    create_business,
    create_custom_form,
    create_custom_form_assignment,
    create_custom_form_field,
    create_location,
    create_teacher,
)


@pytest.mark.django_db
@override_settings(FORCE_SUPERUSER_CREATION=False)
def test_appointment_calendar_uses_assignment_backed_custom_form_context():
    business = create_business()
    location = create_location(business_id=business.business_id)
    appointment_type = create_appointment_type(location=location, business_id=business.business_id)
    staff = create_teacher(business_id=business.business_id, default_location=location)
    form = create_custom_form(business_id=business.business_id, name="Appointment Intake")
    assignment = create_custom_form_assignment(form=form, content_object=appointment_type, business_id=business.business_id)
    create_custom_form_field(form=form, field_type="text", label="Question", required=True)
    client = Client()
    session = client.session
    session["customer_selected_appts"] = json.dumps(
        [{"appt_id": appointment_type.id, "sp_id": staff.id}]
    )
    session.save()

    response = client.get("/appointments/customer/appointment-calendar", HTTP_HOST="localhost")

    assert response.status_code == 200
    assert response.context["appt_info"][0]["custom_form_id"] == form.id
    assert response.context["appt_info"][0]["custom_form_assignment_id"] == assignment.id
    assert "Question" in response.context["appt_info"][0]["render_form"]


@pytest.mark.django_db
@override_settings(FORCE_SUPERUSER_CREATION=False)
def test_single_submit_endpoint_scopes_by_assignment():
    business = create_business()
    location = create_location(business_id=business.business_id)
    appointment_type = create_appointment_type(location=location, business_id=business.business_id)
    other_appointment_type = create_appointment_type(location=location, business_id=business.business_id, name="Other")
    form = create_custom_form(business_id=business.business_id, name="Scoped Appointment Form", single_submission=True)
    assignment = create_custom_form_assignment(form=form, content_object=appointment_type, business_id=business.business_id)
    other_assignment = create_custom_form_assignment(form=form, content_object=other_appointment_type, business_id=business.business_id)
    CustomFormResponse.objects.create(
        business_id=business.business_id,
        custom_form=form,
        assignment=assignment,
        guest_email="guest@example.com",
    )
    client = Client()

    matching = client.post(
        "/customforms/ajax/check-customform-singlesubmit",
        {
            "custom_form_id": form.id,
            "assignment_id": assignment.id,
            "guest_email": "guest@example.com",
        },
        HTTP_HOST="localhost",
    )
    other = client.post(
        "/customforms/ajax/check-customform-singlesubmit",
        {
            "custom_form_id": form.id,
            "assignment_id": other_assignment.id,
            "guest_email": "guest@example.com",
        },
        HTTP_HOST="localhost",
    )

    assert matching.status_code == 200
    assert matching.json() == {"already_submitted": True}
    assert other.status_code == 200
    assert other.json() == {"already_submitted": False}


@pytest.mark.django_db
@override_settings(FORCE_SUPERUSER_CREATION=False)
def test_single_submit_endpoint_does_not_leak_across_businesses():
    create_business(business_id=1)
    other_business = create_business(business_id=2, name="Other Business")
    location = create_location(business_id=other_business.business_id)
    appointment_type = create_appointment_type(location=location, business_id=other_business.business_id)
    form = create_custom_form(
        business_id=other_business.business_id,
        name="Other Business Form",
        single_submission=True,
    )
    assignment = create_custom_form_assignment(
        form=form,
        content_object=appointment_type,
        business_id=other_business.business_id,
    )
    CustomFormResponse.objects.create(
        business_id=other_business.business_id,
        custom_form=form,
        assignment=assignment,
        guest_email="guest@example.com",
    )
    client = Client()

    response = client.post(
        "/customforms/ajax/check-customform-singlesubmit",
        {
            "custom_form_id": form.id,
            "assignment_id": assignment.id,
            "guest_email": "guest@example.com",
        },
        HTTP_HOST="localhost",
    )

    assert response.status_code == 200
    assert response.json() == {"already_submitted": False}


@pytest.mark.django_db
@override_settings(FORCE_SUPERUSER_CREATION=False)
def test_appointment_calendar_post_processes_assignment_backed_custom_form():
    business = create_business()
    location = create_location(business_id=business.business_id)
    appointment_type = create_appointment_type(location=location, business_id=business.business_id)
    staff = create_teacher(business_id=business.business_id, default_location=location)
    form = create_custom_form(business_id=business.business_id, name="Guest Intake")
    assignment = create_custom_form_assignment(form=form, content_object=appointment_type, business_id=business.business_id)
    field = create_custom_form_field(form=form, field_type="text", label="Question", required=True)
    client = Client()
    selected_appts = json.dumps([{"appt_id": appointment_type.id, "sp_id": staff.id}])

    response = client.post(
        "/appointments/customer/appointment-calendar",
        {
            "selected_appt_ids": selected_appts,
            "selected_date": "2026-06-10",
            "selected_time": "10:00 AM",
            "customer_tz": "UTC",
            "guest_email": "guest@example.com",
            "guest_full_name": "Guest Example",
            "custom_form_id": form.id,
            "custom_form_assignment_id": assignment.id,
            f"custom_form-field-{field.id}": "Ada",
        },
        HTTP_HOST="localhost",
    )

    assert response.status_code == 302
    assert CustomFormResponse.objects.filter(
        custom_form=form,
        assignment=assignment,
        guest_email="guest@example.com",
    ).count() == 1
    assert BookedAppointment.objects.filter(
        appointment_type=appointment_type,
        service_provider=staff,
    ).count() == 1


@pytest.mark.django_db
@override_settings(FORCE_SUPERUSER_CREATION=False)
def test_appointment_calendar_post_requires_required_custom_form_submission():
    business = create_business()
    location = create_location(business_id=business.business_id)
    appointment_type = create_appointment_type(location=location, business_id=business.business_id)
    staff = create_teacher(business_id=business.business_id, default_location=location)
    form = create_custom_form(business_id=business.business_id, name="Required Intake")
    create_custom_form_assignment(
        form=form,
        content_object=appointment_type,
        business_id=business.business_id,
        is_required=True,
    )
    create_custom_form_field(form=form, field_type="text", label="Question", required=True)
    client = Client()
    selected_appts = json.dumps([{"appt_id": appointment_type.id, "sp_id": staff.id}])

    response = client.post(
        "/appointments/customer/appointment-calendar",
        {
            "selected_appt_ids": selected_appts,
            "selected_date": "2026-06-10",
            "selected_time": "10:00 AM",
            "customer_tz": "UTC",
            "guest_email": "guest@example.com",
            "guest_full_name": "Guest Example",
        },
        HTTP_HOST="localhost",
    )

    assert response.status_code == 302
    assert CustomFormResponse.objects.filter(custom_form=form).count() == 0
    assert BookedAppointment.objects.filter(
        appointment_type=appointment_type,
        service_provider=staff,
    ).count() == 0


@pytest.mark.django_db
@override_settings(FORCE_SUPERUSER_CREATION=False)
def test_appointment_calendar_post_allows_already_submitted_required_custom_form():
    business = create_business()
    location = create_location(business_id=business.business_id)
    appointment_type = create_appointment_type(location=location, business_id=business.business_id)
    staff = create_teacher(business_id=business.business_id, default_location=location)
    form = create_custom_form(
        business_id=business.business_id,
        name="Single Submit Intake",
        single_submission=True,
    )
    assignment = create_custom_form_assignment(
        form=form,
        content_object=appointment_type,
        business_id=business.business_id,
        is_required=True,
    )
    CustomFormResponse.objects.create(
        business_id=business.business_id,
        custom_form=form,
        assignment=assignment,
        guest_email="guest@example.com",
    )
    client = Client()
    selected_appts = json.dumps([{"appt_id": appointment_type.id, "sp_id": staff.id}])

    response = client.post(
        "/appointments/customer/appointment-calendar",
        {
            "selected_appt_ids": selected_appts,
            "selected_date": "2026-06-10",
            "selected_time": "10:00 AM",
            "customer_tz": "UTC",
            "guest_email": "guest@example.com",
            "guest_full_name": "Guest Example",
        },
        HTTP_HOST="localhost",
    )

    assert response.status_code == 302
    assert CustomFormResponse.objects.filter(custom_form=form).count() == 1
    assert BookedAppointment.objects.filter(
        appointment_type=appointment_type,
        service_provider=staff,
    ).count() == 1


@pytest.mark.django_db
@override_settings(FORCE_SUPERUSER_CREATION=False)
def test_appointment_calendar_post_allows_missing_optional_custom_form_submission():
    business = create_business()
    location = create_location(business_id=business.business_id)
    appointment_type = create_appointment_type(location=location, business_id=business.business_id)
    staff = create_teacher(business_id=business.business_id, default_location=location)
    form = create_custom_form(business_id=business.business_id, name="Optional Intake")
    create_custom_form_assignment(
        form=form,
        content_object=appointment_type,
        business_id=business.business_id,
        is_required=False,
    )
    create_custom_form_field(form=form, field_type="text", label="Question", required=True)
    client = Client()
    selected_appts = json.dumps([{"appt_id": appointment_type.id, "sp_id": staff.id}])

    response = client.post(
        "/appointments/customer/appointment-calendar",
        {
            "selected_appt_ids": selected_appts,
            "selected_date": "2026-06-10",
            "selected_time": "10:00 AM",
            "customer_tz": "UTC",
            "guest_email": "guest@example.com",
            "guest_full_name": "Guest Example",
        },
        HTTP_HOST="localhost",
    )

    assert response.status_code == 302
    assert CustomFormResponse.objects.filter(custom_form=form).count() == 0
    assert BookedAppointment.objects.filter(
        appointment_type=appointment_type,
        service_provider=staff,
    ).count() == 1


@pytest.mark.django_db
@override_settings(FORCE_SUPERUSER_CREATION=False)
def test_appointment_calendar_post_requires_all_required_custom_forms():
    business = create_business()
    location = create_location(business_id=business.business_id)
    first_appointment_type = create_appointment_type(
        location=location,
        business_id=business.business_id,
        name="First Appointment",
    )
    second_appointment_type = create_appointment_type(
        location=location,
        business_id=business.business_id,
        name="Second Appointment",
    )
    staff = create_teacher(business_id=business.business_id, default_location=location)
    first_form = create_custom_form(business_id=business.business_id, name="First Intake")
    second_form = create_custom_form(business_id=business.business_id, name="Second Intake")
    first_assignment = create_custom_form_assignment(
        form=first_form,
        content_object=first_appointment_type,
        business_id=business.business_id,
        is_required=True,
    )
    create_custom_form_assignment(
        form=second_form,
        content_object=second_appointment_type,
        business_id=business.business_id,
        is_required=True,
    )
    first_field = create_custom_form_field(
        form=first_form,
        field_type="text",
        label="First Question",
        required=True,
    )
    client = Client()
    selected_appts = json.dumps(
        [
            {"appt_id": first_appointment_type.id, "sp_id": staff.id},
            {"appt_id": second_appointment_type.id, "sp_id": staff.id},
        ]
    )

    response = client.post(
        "/appointments/customer/appointment-calendar",
        {
            "selected_appt_ids": selected_appts,
            "selected_date": "2026-06-10",
            "selected_time": "10:00 AM",
            "customer_tz": "UTC",
            "guest_email": "guest@example.com",
            "guest_full_name": "Guest Example",
            "custom_form_id": first_form.id,
            "custom_form_assignment_id": first_assignment.id,
            f"custom_form-field-{first_field.id}": "Ada",
        },
        HTTP_HOST="localhost",
    )

    assert response.status_code == 302
    assert CustomFormResponse.objects.filter(custom_form__in=[first_form, second_form]).count() == 0
    assert BookedAppointment.objects.filter(
        appointment_type__in=[first_appointment_type, second_appointment_type],
        service_provider=staff,
    ).count() == 0


@pytest.mark.django_db
@override_settings(FORCE_SUPERUSER_CREATION=False)
def test_appointment_calendar_post_allows_all_required_custom_forms_when_previous_one_exists():
    business = create_business()
    location = create_location(business_id=business.business_id)
    first_appointment_type = create_appointment_type(
        location=location,
        business_id=business.business_id,
        name="First Appointment",
    )
    second_appointment_type = create_appointment_type(
        location=location,
        business_id=business.business_id,
        name="Second Appointment",
    )
    staff = create_teacher(business_id=business.business_id, default_location=location)
    first_form = create_custom_form(business_id=business.business_id, name="First Intake")
    second_form = create_custom_form(business_id=business.business_id, name="Second Intake")
    first_assignment = create_custom_form_assignment(
        form=first_form,
        content_object=first_appointment_type,
        business_id=business.business_id,
        is_required=True,
    )
    second_assignment = create_custom_form_assignment(
        form=second_form,
        content_object=second_appointment_type,
        business_id=business.business_id,
        is_required=True,
    )
    second_field = create_custom_form_field(
        form=second_form,
        field_type="text",
        label="Second Question",
        required=True,
    )
    CustomFormResponse.objects.create(
        business_id=business.business_id,
        custom_form=first_form,
        assignment=first_assignment,
        guest_email="guest@example.com",
    )
    client = Client()
    selected_appts = json.dumps(
        [
            {"appt_id": first_appointment_type.id, "sp_id": staff.id},
            {"appt_id": second_appointment_type.id, "sp_id": staff.id},
        ]
    )

    response = client.post(
        "/appointments/customer/appointment-calendar",
        {
            "selected_appt_ids": selected_appts,
            "selected_date": "2026-06-10",
            "selected_time": "10:00 AM",
            "customer_tz": "UTC",
            "guest_email": "guest@example.com",
            "guest_full_name": "Guest Example",
            "custom_form_id": second_form.id,
            "custom_form_assignment_id": second_assignment.id,
            f"custom_form-field-{second_field.id}": "Ada",
        },
        HTTP_HOST="localhost",
    )

    assert response.status_code == 302
    assert CustomFormResponse.objects.filter(custom_form=first_form).count() == 1
    assert CustomFormResponse.objects.filter(custom_form=second_form).count() == 1
    assert BookedAppointment.objects.filter(
        appointment_type__in=[first_appointment_type, second_appointment_type],
        service_provider=staff,
    ).count() == 2


@pytest.mark.django_db
@override_settings(FORCE_SUPERUSER_CREATION=False)
def test_appointment_calendar_post_rejects_cross_business_custom_form_submission():
    business = create_business(business_id=1)
    other_business = create_business(business_id=2, name="Other Business")
    location = create_location(business_id=business.business_id)
    other_location = create_location(business_id=other_business.business_id, name="Other Location")
    appointment_type = create_appointment_type(location=location, business_id=business.business_id)
    other_appointment_type = create_appointment_type(
        location=other_location,
        business_id=other_business.business_id,
        name="Other Appointment",
    )
    staff = create_teacher(business_id=business.business_id, default_location=location)
    form = create_custom_form(business_id=other_business.business_id, name="Foreign Form")
    assignment = create_custom_form_assignment(
        form=form,
        content_object=other_appointment_type,
        business_id=other_business.business_id,
    )
    field = create_custom_form_field(form=form, field_type="text", label="Question", required=True)
    client = Client()
    selected_appts = json.dumps([{"appt_id": appointment_type.id, "sp_id": staff.id}])

    response = client.post(
        "/appointments/customer/appointment-calendar",
        {
            "selected_appt_ids": selected_appts,
            "selected_date": "2026-06-10",
            "selected_time": "10:00 AM",
            "customer_tz": "UTC",
            "guest_email": "guest@example.com",
            "guest_full_name": "Guest Example",
            "custom_form_id": form.id,
            "custom_form_assignment_id": assignment.id,
            f"custom_form-field-{field.id}": "Ada",
        },
        HTTP_HOST="localhost",
    )

    assert response.status_code == 302
    assert CustomFormResponse.objects.filter(custom_form=form).count() == 0
    assert BookedAppointment.objects.filter(
        appointment_type=appointment_type,
        service_provider=staff,
    ).count() == 0
