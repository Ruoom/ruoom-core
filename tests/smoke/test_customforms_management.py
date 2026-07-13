import json
from types import SimpleNamespace

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import Client, RequestFactory, override_settings

from plugins.customforms.models import CustomForm, CustomFormAssignment, CustomFormResponse
from plugins.customforms.views import ajax_reorder_fields
from tests.factories import (
    create_custom_form,
    create_custom_form_assignment,
    create_custom_form_field,
    create_profile,
    create_service,
)


@pytest.mark.django_db
@override_settings(FORCE_SUPERUSER_CREATION=False)
def test_staff_can_create_edit_and_delete_custom_forms():
    staff = create_profile(
        email="staff-customforms@example.com",
        user_type="staff",
    )
    client = Client()
    client.force_login(staff)

    create_response = client.post(
        "/customforms/manage/new/",
        {
            "name": "Member Intake",
            "single_submission": "on",
            "is_active": "on",
            "save_form": "1",
        },
        HTTP_HOST="localhost",
    )

    assert create_response.status_code == 302
    custom_form = CustomForm.objects.get(name="Member Intake")

    edit_response = client.post(
        f"/customforms/manage/{custom_form.pk}/",
        {
            "label": "Favorite color",
            "field_type": "radio",
            "field_options": "Blue\nGreen",
            "required": "on",
            "help_text": "Pick one",
            "placeholder": "",
            "order": "",
            "is_active": "on",
            "add_field": "1",
        },
        HTTP_HOST="localhost",
    )

    assert edit_response.status_code == 302
    custom_form.refresh_from_db()
    assert custom_form.fields.count() == 1

    delete_response = client.post(
        f"/customforms/manage/{custom_form.pk}/delete/",
        HTTP_HOST="localhost",
    )

    assert delete_response.status_code == 302
    assert CustomForm.objects.filter(pk=custom_form.pk).exists() is False


@pytest.mark.django_db
@override_settings(FORCE_SUPERUSER_CREATION=False)
def test_staff_can_browse_custom_form_responses():
    staff = create_profile(
        email="staff-responses@example.com",
        user_type="staff",
    )
    custom_form = create_custom_form(name="Response Browser")
    field = create_custom_form_field(form=custom_form, field_type="text", label="Answer")
    request = SimpleNamespace(POST={f"custom_form-field-{field.id}": "Ada"})
    valid, response = custom_form.process_form_response(
        business_id=custom_form.business_id,
        customer_id=staff.id,
        request=request,
    )
    assert valid is True
    assert isinstance(response, CustomFormResponse)

    client = Client()
    client.force_login(staff)

    list_response = client.get("/customforms/manage/", HTTP_HOST="localhost")
    detail_response = client.get(
        f"/customforms/manage/{custom_form.pk}/responses/",
        HTTP_HOST="localhost",
    )

    assert list_response.status_code == 200
    assert "Response Browser" in list_response.content.decode()
    assert detail_response.status_code == 200
    body = detail_response.content.decode()
    assert "Ada" in body
    assert "Answer" in body


@pytest.mark.django_db
@override_settings(FORCE_SUPERUSER_CREATION=False)
def test_staff_can_render_compact_custom_form_editor():
    staff = create_profile(email="staff-editor@example.com", user_type="staff")
    custom_form = create_custom_form(name="Compact Editor", business_id=staff.business_id)
    create_custom_form_field(
        form=custom_form,
        field_type="radio",
        label="<p>Favorite color</p>",
        field_options="Blue\nGreen",
        required=True,
    )
    client = Client()
    client.force_login(staff)

    response = client.get(f"/customforms/manage/{custom_form.pk}/", HTTP_HOST="localhost")

    assert response.status_code == 200
    body = response.content.decode()
    assert 'tbody id="fields-sortable"' in body
    assert 'id="addFieldModal"' in body
    assert 'id="editFieldModal"' in body
    assert "addFieldOptionsContainer" in body
    assert "addFieldLabelEditor" in body


@pytest.mark.django_db
@override_settings(FORCE_SUPERUSER_CREATION=False)
def test_modal_field_edit_preserves_existing_active_state():
    staff = create_profile(email="staff-modal-edit@example.com", user_type="staff")
    custom_form = create_custom_form(business_id=staff.business_id)
    field = create_custom_form_field(
        form=custom_form,
        field_type="text",
        label="Name",
        is_active=True,
    )
    client = Client()
    client.force_login(staff)

    response = client.post(
        f"/customforms/manage/{custom_form.pk}/",
        {
            "field_id": str(field.id),
            "label": "Full name",
            "field_type": "text",
            "field_options": "",
            "required": "on",
            "edit_field": "1",
        },
        HTTP_HOST="localhost",
    )

    assert response.status_code == 302
    field.refresh_from_db()
    assert field.label == "Full name"
    assert field.required is True
    assert field.is_active is True


@pytest.mark.django_db
@override_settings(FORCE_SUPERUSER_CREATION=False)
def test_custom_form_toggle_registration_keeps_single_primary_form():
    staff = create_profile(email="staff-registration-toggle@example.com", user_type="staff")
    first_form = create_custom_form(
        business_id=staff.business_id,
        name="First Registration Form",
        is_registration_form=True,
    )
    second_form = create_custom_form(
        business_id=staff.business_id,
        name="Second Registration Form",
        is_registration_form=False,
    )
    client = Client()
    client.force_login(staff)

    response = client.post(
        f"/customforms/manage/{second_form.pk}/",
        {"action": "toggle_registration"},
        HTTP_HOST="localhost",
    )

    assert response.status_code == 302
    first_form.refresh_from_db()
    second_form.refresh_from_db()
    assert first_form.is_registration_form is False
    assert second_form.is_registration_form is True


@pytest.mark.django_db
@override_settings(FORCE_SUPERUSER_CREATION=False)
def test_duplicate_assignment_post_updates_existing_assignment():
    staff = create_profile(email="staff-assignment-update@example.com", user_type="staff")
    custom_form = create_custom_form(business_id=staff.business_id, name="Assignment Form")
    service = create_service(business_id=staff.business_id)
    assignment = create_custom_form_assignment(
        form=custom_form,
        content_object=service,
        business_id=staff.business_id,
        use_case=CustomFormAssignment.USE_CASE_EVENT_REGISTRATION,
        is_required=True,
        is_active=False,
    )
    client = Client()
    client.force_login(staff)

    response = client.post(
        f"/customforms/manage/{custom_form.pk}/",
        {
            "use_case": CustomFormAssignment.USE_CASE_EVENT_REGISTRATION,
            "target_ref": f"booking_service:{service.pk}",
            "is_active": "on",
            "add_assignment": "1",
        },
        HTTP_HOST="localhost",
    )

    assert response.status_code == 302
    assignment.refresh_from_db()
    assert custom_form.assignments.count() == 1
    assert assignment.is_required is False
    assert assignment.is_active is True


@pytest.mark.django_db
@override_settings(FORCE_SUPERUSER_CREATION=False)
def test_staff_can_reorder_custom_form_fields_with_ajax():
    staff = create_profile(email="field-sort@example.com", user_type="staff")
    custom_form = create_custom_form(business_id=staff.business_id)
    first = create_custom_form_field(form=custom_form, field_type="text", label="First")
    second = create_custom_form_field(form=custom_form, field_type="text", label="Second")
    factory = RequestFactory()
    request = factory.post(
        "/customforms/ajax/reorder-fields/",
        data=json.dumps({"order": [second.id, first.id]}),
        content_type="application/json",
    )
    request.user = staff

    response = ajax_reorder_fields(request)

    assert response.status_code == 200
    first.refresh_from_db()
    second.refresh_from_db()
    assert second.order == 0
    assert first.order == 1


@pytest.mark.django_db
def test_anonymous_user_cannot_reorder_custom_form_fields_with_ajax():
    custom_form = create_custom_form()
    first = create_custom_form_field(form=custom_form, field_type="text", label="First")
    factory = RequestFactory()
    request = factory.post(
        "/customforms/ajax/reorder-fields/",
        data=json.dumps({"order": [first.id]}),
        content_type="application/json",
    )
    request.user = AnonymousUser()

    response = ajax_reorder_fields(request)

    assert response.status_code == 403


@pytest.mark.django_db
@override_settings(FORCE_SUPERUSER_CREATION=False)
def test_customer_user_cannot_reorder_custom_form_fields_with_ajax():
    customer = create_profile(email="field-sort-customer@example.com")
    custom_form = create_custom_form(business_id=customer.business_id)
    first = create_custom_form_field(form=custom_form, field_type="text", label="First")
    factory = RequestFactory()
    request = factory.post(
        "/customforms/ajax/reorder-fields/",
        data=json.dumps({"order": [first.id]}),
        content_type="application/json",
    )
    request.user = customer

    response = ajax_reorder_fields(request)

    assert response.status_code == 403


@pytest.mark.django_db
@override_settings(FORCE_SUPERUSER_CREATION=False)
def test_reorder_custom_form_fields_rejects_invalid_payload():
    staff = create_profile(email="field-sort-invalid@example.com", user_type="staff")
    factory = RequestFactory()
    request = factory.post(
        "/customforms/ajax/reorder-fields/",
        data=json.dumps({"order": ["not-an-id"]}),
        content_type="application/json",
    )
    request.user = staff

    response = ajax_reorder_fields(request)

    assert response.status_code == 400


@pytest.mark.django_db
def test_ajax_single_submit_detects_existing_guest_submission_for_assignment():
    custom_form = create_custom_form(single_submission=True)
    service = create_service(business_id=custom_form.business_id)
    assignment = create_custom_form_assignment(
        form=custom_form,
        content_object=service,
        use_case=CustomFormAssignment.USE_CASE_EVENT_REGISTRATION,
    )
    CustomFormResponse.objects.create(
        business_id=custom_form.business_id,
        custom_form=custom_form,
        assignment=assignment,
        guest_email="guest@example.com",
    )
    client = Client()

    response = client.post(
        "/customforms/ajax/check-customform-singlesubmit",
        {
            "custom_form_id": str(custom_form.pk),
            "assignment_id": str(assignment.pk),
            "guest_email": "guest@example.com",
        },
        HTTP_HOST="localhost",
    )

    assert response.status_code == 200
    assert response.json() == {"already_submitted": True}


@pytest.mark.django_db
@override_settings(FORCE_SUPERUSER_CREATION=False)
def test_management_views_require_profile_backed_business_context():
    user_model = get_user_model()
    superuser = user_model.objects.create_superuser(
        username="bare-superuser",
        email="bare-superuser@example.com",
        password="password123",
    )
    client = Client()
    client.force_login(superuser)

    response = client.get("/customforms/manage/", HTTP_HOST="localhost")

    assert response.status_code == 404
