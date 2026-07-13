import json
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from django.test import Client, override_settings

from plugins.customforms.models import CustomForm, CustomFormResponse, GoogleFormOAuthToken
from tests.factories import create_custom_form_field, create_profile


@pytest.mark.django_db
@override_settings(FORCE_SUPERUSER_CREATION=False)
def test_staff_can_link_google_form_from_url():
    staff = create_profile(email="google-sync-staff@example.com", user_type="staff")
    client = Client()
    client.force_login(staff)

    response = client.post(
        "/customforms/manage/google-sync/",
        {
            "google_form_id": "https://docs.google.com/forms/d/1AbCdEfGhIjKlMnOpQrStUvWxYz1234567890/edit",
        },
        HTTP_HOST="localhost",
    )

    assert response.status_code == 302
    custom_form = CustomForm.objects.get(is_google_synced=True)
    assert custom_form.google_form_id == "1AbCdEfGhIjKlMnOpQrStUvWxYz1234567890"
    assert custom_form.google_form_webhook_secret


@pytest.mark.django_db
@override_settings(FORCE_SUPERUSER_CREATION=False, PUBLIC_URL_PATTERNS=("/customforms/webhook/",))
def test_google_form_webhook_imports_fields_and_dedups_response():
    custom_form = CustomForm.objects.create(
        business_id=1,
        name="Google Form (abc)",
        google_form_id="abc",
        google_form_webhook_secret="secret-token",
        is_google_synced=True,
    )
    client = Client()
    payload = {
        "secret": "secret-token",
        "response_id": "resp-1",
        "form_title": "Volunteer Intake",
        "responses": [
            {"question_id": "q1", "label": "First Name", "value": "Ada"},
            {"question_id": "q2", "label": "Email", "value": "ada@example.com"},
        ],
    }

    first = client.post(
        f"/customforms/webhook/{custom_form.pk}/google/",
        data=json.dumps(payload),
        content_type="application/json",
        HTTP_HOST="localhost",
    )
    second = client.post(
        f"/customforms/webhook/{custom_form.pk}/google/",
        data=json.dumps(payload),
        content_type="application/json",
        HTTP_HOST="localhost",
    )

    assert first.status_code == 200
    assert second.status_code == 200
    custom_form.refresh_from_db()
    assert custom_form.name == "Volunteer Intake"
    assert custom_form.fields.count() == 2
    assert CustomFormResponse.objects.filter(
        custom_form=custom_form,
        source=CustomFormResponse.SOURCE_GOOGLE_FORMS,
        external_response_id="resp-1",
    ).count() == 1


@pytest.mark.django_db
@override_settings(FORCE_SUPERUSER_CREATION=False, PUBLIC_URL_PATTERNS=("/customforms/webhook/",))
def test_google_form_webhook_rejects_invalid_secret():
    custom_form = CustomForm.objects.create(
        business_id=1,
        name="Google Form (abc)",
        google_form_id="abc",
        google_form_webhook_secret="secret-token",
        is_google_synced=True,
    )
    client = Client()

    response = client.post(
        f"/customforms/webhook/{custom_form.pk}/google/",
        data=json.dumps(
            {
                "secret": "wrong",
                "responses": [{"question_id": "q1", "label": "Name", "value": "Ada"}],
            }
        ),
        content_type="application/json",
        HTTP_HOST="localhost",
    )

    assert response.status_code == 403


@pytest.mark.django_db
@override_settings(FORCE_SUPERUSER_CREATION=False)
def test_google_synced_form_rejects_duplicate_role_assignments():
    staff = create_profile(email="google-roles-staff@example.com", user_type="staff")
    custom_form = CustomForm.objects.create(
        business_id=staff.business_id,
        name="Volunteer Intake",
        google_form_id="abc",
        google_form_webhook_secret="secret-token",
        is_google_synced=True,
        is_registration_form=True,
    )
    first = create_custom_form_field(form=custom_form, field_type="text", label="First name")
    second = create_custom_form_field(form=custom_form, field_type="text", label="Backup email")
    client = Client()
    client.force_login(staff)

    response = client.post(
        f"/customforms/manage/{custom_form.pk}/google/",
        {
            "action": "update_roles",
            f"role_{first.id}": "email",
            f"role_{second.id}": "email",
        },
        HTTP_HOST="localhost",
    )

    assert response.status_code == 302
    first.refresh_from_db()
    second.refresh_from_db()
    assert first.google_role is None
    assert second.google_role is None


@pytest.mark.django_db
@override_settings(FORCE_SUPERUSER_CREATION=False)
def test_google_oauth_callback_saves_token_and_connected_email():
    staff = create_profile(email="google-oauth-staff@example.com", user_type="staff")
    custom_form = CustomForm.objects.create(
        business_id=staff.business_id,
        name="Volunteer Intake",
        google_form_id="abc",
        google_form_webhook_secret="secret-token",
        is_google_synced=True,
    )
    client = Client()
    client.force_login(staff)
    session = client.session
    session["gforms_oauth_state"] = f"{custom_form.pk}:state-token"
    session.save()

    with (
        patch("plugins.customforms.views.requests.post") as token_post,
        patch("plugins.customforms.views.requests.get") as userinfo_get,
        patch.dict(
            "os.environ",
            {"GOOGLE_OAUTH2_KEY": "client-id", "GOOGLE_OAUTH2_SECRET": "client-secret"},
            clear=False,
        ),
    ):
        token_post.return_value = SimpleNamespace(
            status_code=200,
            json=lambda: {
                "access_token": "access-token",
                "refresh_token": "refresh-token",
                "expires_in": 1800,
            },
            text="ok",
        )
        userinfo_get.return_value = SimpleNamespace(
            status_code=200,
            json=lambda: {"email": "owner@example.com"},
        )

        response = client.get(
            "/customforms/oauth/callback/",
            {"state": f"{custom_form.pk}:state-token", "code": "auth-code"},
            HTTP_HOST="localhost",
        )

    assert response.status_code == 302
    assert response.url == f"/customforms/manage/{custom_form.pk}/google/"
    token = GoogleFormOAuthToken.objects.get(custom_form=custom_form)
    assert token.access_token == "access-token"
    assert token.refresh_token == "refresh-token"
    assert token.connected_email == "owner@example.com"


@pytest.mark.django_db
@override_settings(FORCE_SUPERUSER_CREATION=False)
def test_google_fetch_now_redirects_back_to_responses_when_started_there():
    staff = create_profile(email="google-fetch-staff@example.com", user_type="staff")
    custom_form = CustomForm.objects.create(
        business_id=staff.business_id,
        name="Volunteer Intake",
        google_form_id="abc",
        google_form_webhook_secret="secret-token",
        is_google_synced=True,
    )
    client = Client()
    client.force_login(staff)

    with patch("plugins.customforms.google_forms_poller.poll_form", return_value=(2, None)) as poll_form:
        response = client.post(
            f"/customforms/manage/{custom_form.pk}/google/fetch/",
            HTTP_HOST="localhost",
            HTTP_REFERER=f"http://localhost/customforms/manage/{custom_form.pk}/responses/",
        )

    assert response.status_code == 302
    assert response.url == f"/customforms/manage/{custom_form.pk}/responses/"
    poll_form.assert_called_once()
