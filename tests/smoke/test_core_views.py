import base64
import tempfile
from io import BytesIO
from pathlib import Path

import pytest
from django.core import mail
from django.test import Client, RequestFactory, override_settings
from PIL import Image

from ruoom.views import SaveProfilePictureView
from tests.factories import create_business, create_profile


INVALID_IMAGE_DATA_URL = "data:image/png;base64,bm90IGFuIGltYWdl"
INVALID_BASE64_DATA_URL = "data:image/png;base64,@@@"


def make_image_data_url(image_format):
    buffer = BytesIO()
    image = Image.new("RGB", (1, 1), color=(255, 0, 0))
    image.save(buffer, format=image_format)
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    mime_type = "image/jpeg" if image_format == "JPEG" else "image/png"
    return "data:%s;base64,%s" % (mime_type, encoded)


@pytest.mark.django_db
def test_health_check_returns_ok_json():
    client = Client()

    response = client.get("/health/")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.django_db
def test_health_check_without_trailing_slash_returns_ok_json():
    client = Client()

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.django_db
@override_settings(METRICS_API_TOKEN="")
def test_api_metrics_requires_configuration():
    client = Client()

    response = client.get("/api/metrics/")

    assert response.status_code == 503
    assert response.json()["error"] == "Metrics endpoint not configured"


@pytest.mark.django_db
@override_settings(METRICS_API_TOKEN="secret-token")
def test_api_metrics_requires_token():
    client = Client()

    response = client.get("/api/metrics/")

    assert response.status_code == 401
    assert response.json()["error"] == "Unauthorized"


@pytest.mark.django_db
@override_settings(METRICS_API_TOKEN="secret-token")
def test_api_metrics_returns_resource_payload_for_valid_token():
    client = Client()

    response = client.get("/api/metrics/", HTTP_X_API_TOKEN="secret-token")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "OK"
    assert payload["database"]["status"] == "connected"
    assert "timestamp" in payload


@pytest.mark.django_db
@override_settings(FORCE_SUPERUSER_CREATION=False)
def test_password_reset_redirects_done_for_unknown_email_without_sending_mail():
    create_business()
    client = Client()

    response = client.post("/accounts/password_reset/", {"email": "missing@example.com"}, HTTP_HOST="localhost")

    assert response.status_code == 302
    assert response.url == "/accounts/password_reset/done/"
    assert len(mail.outbox) == 0


@pytest.mark.django_db
@override_settings(FORCE_SUPERUSER_CREATION=False)
def test_password_reset_sends_mail_for_matching_business_profile():
    create_business(contact_email="owner@example.com", business_website="https://example.com")
    profile = create_profile(email="member@example.com")
    client = Client()

    response = client.post("/accounts/password_reset/", {"email": profile.email}, HTTP_HOST="localhost")

    assert response.status_code == 302
    assert response.url == "/accounts/password_reset/done/"
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == [profile.email]


@pytest.mark.django_db
@override_settings(FORCE_SUPERUSER_CREATION=False)
def test_save_profile_picture_accepts_png_data_url():
    create_business()
    profile = create_profile(email="image@example.com")
    request = RequestFactory().post("/save_profile_picture/", {"file": make_image_data_url("PNG")})
    request.user = profile
    view = SaveProfilePictureView.as_view()

    with tempfile.TemporaryDirectory() as media_root:
        with override_settings(MEDIA_ROOT=media_root):
            response = view(request)

            assert response.status_code == 200
            profile.refresh_from_db()
            saved_name = profile.profile_image.name
            assert saved_name.endswith(".png")
            assert Path(media_root, saved_name).exists()


@pytest.mark.django_db
@override_settings(FORCE_SUPERUSER_CREATION=False)
def test_save_profile_picture_accepts_jpeg_data_url():
    create_business()
    profile = create_profile(email="jpeg@example.com")
    request = RequestFactory().post("/save_profile_picture/", {"file": make_image_data_url("JPEG")})
    request.user = profile
    view = SaveProfilePictureView.as_view()

    with tempfile.TemporaryDirectory() as media_root:
        with override_settings(MEDIA_ROOT=media_root):
            response = view(request)

            assert response.status_code == 200
            profile.refresh_from_db()
            saved_name = profile.profile_image.name
            assert saved_name.endswith(".jpg")
            assert Path(media_root, saved_name).exists()


@pytest.mark.django_db
@override_settings(FORCE_SUPERUSER_CREATION=False)
def test_save_profile_picture_rejects_non_image_payload():
    create_business()
    profile = create_profile(email="bad-image@example.com")
    request = RequestFactory().post("/save_profile_picture/", {"file": INVALID_IMAGE_DATA_URL})
    request.user = profile
    view = SaveProfilePictureView.as_view()

    response = view(request)

    assert response.status_code == 400


@pytest.mark.django_db
@override_settings(FORCE_SUPERUSER_CREATION=False)
def test_save_profile_picture_rejects_invalid_base64_payload():
    create_business()
    profile = create_profile(email="bad-base64@example.com")
    request = RequestFactory().post("/save_profile_picture/", {"file": INVALID_BASE64_DATA_URL})
    request.user = profile
    view = SaveProfilePictureView.as_view()

    response = view(request)

    assert response.status_code == 400
