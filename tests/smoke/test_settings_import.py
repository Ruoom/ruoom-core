import os
import subprocess
import sys

from django.conf import settings


def test_test_settings_imports_core_apps():
    assert settings.ROOT_URLCONF == "ruoom.urls"
    assert "administration.apps.AdminConfig" in settings.INSTALLED_APPS
    assert "plugins.booking.apps.BookingConfig" in settings.INSTALLED_APPS
    assert "plugins.customforms.apps.CustomFormsConfig" in settings.INSTALLED_APPS


def test_test_settings_use_sqlite_and_filesystem_storage():
    assert settings.DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3"
    assert settings.DEFAULT_FILE_STORAGE == "django.core.files.storage.FileSystemStorage"


def test_ruoom_settings_enable_s3_storage_from_environment():
    env = os.environ.copy()
    env.update(
        {
            "DEBUG": "true",
            "STORAGE": "S3",
            "AWS_BUCKET_NAME": "ruoom-test-bucket",
            "AWS_DEFAULT_REGION": "us-east-1",
        }
    )
    command = [
        sys.executable,
        "-c",
        (
            "import ruoom.settings as s; "
            "assert s.DEFAULT_FILE_STORAGE == 'ruoom.storages.MediaStore'; "
            "assert s.STATICFILES_STORAGE == 'storages.backends.s3boto3.S3Boto3Storage'; "
            "assert s.AWS_STORAGE_BUCKET_NAME == 'ruoom-test-bucket'; "
            "assert s.STATIC_URL == 'https://ruoom-test-bucket.s3.amazonaws.com/static/'; "
            "assert s.STORAGES['default']['BACKEND'] == 'ruoom.storages.MediaStore'"
        ),
    ]

    result = subprocess.run(command, env=env, capture_output=True, text=True, check=False)

    assert result.returncode == 0, result.stderr


def test_ruoom_settings_support_railway_bucket_endpoint_from_environment():
    env = os.environ.copy()
    env.update(
        {
            "DEBUG": "true",
            "STORAGE": "S3",
            "AWS_S3_BUCKET_NAME": "ruoom-railway-bucket",
            "AWS_ENDPOINT_URL": "https://storage.railway.app",
            "AWS_S3_URL_STYLE": "virtual",
            "AWS_DEFAULT_REGION": "auto",
        }
    )
    command = [
        sys.executable,
        "-c",
        (
            "import ruoom.settings as s; "
            "assert s.AWS_STORAGE_BUCKET_NAME == 'ruoom-railway-bucket'; "
            "assert s.AWS_S3_ENDPOINT_URL == 'https://storage.railway.app'; "
            "assert s.AWS_S3_REGION_NAME == 'auto'; "
            "assert s.AWS_S3_ADDRESSING_STYLE == 'virtual'; "
            "assert s.STATIC_URL == '/static/'; "
            "assert s.STATICFILES_STORAGE == 'storages.backends.s3boto3.S3Boto3Storage'"
        ),
    ]

    result = subprocess.run(command, env=env, capture_output=True, text=True, check=False)

    assert result.returncode == 0, result.stderr


def test_ruoom_settings_default_debug_true_when_environment_missing():
    env = os.environ.copy()
    env.pop("DEBUG", None)
    command = [
        sys.executable,
        "-c",
        "import ruoom.settings as s; assert s.DEBUG is True",
    ]

    result = subprocess.run(command, env=env, capture_output=True, text=True, check=False)

    assert result.returncode == 0, result.stderr


def test_ruoom_settings_use_debug_from_environment():
    env = os.environ.copy()
    env["DEBUG"] = "false"
    env["SECRET_KEY"] = "test-secret-from-env"
    command = [
        sys.executable,
        "-c",
        "import ruoom.settings as s; assert s.DEBUG is False",
    ]

    result = subprocess.run(command, env=env, capture_output=True, text=True, check=False)

    assert result.returncode == 0, result.stderr


def test_ruoom_settings_use_database_url_from_environment():
    env = os.environ.copy()
    env.update(
        {
            "DEBUG": "false",
            "SECRET_KEY": "test-secret-from-env",
            "DATABASE_URL": "postgresql://railway_user:railway_pass@containers-us-west.railway.app:7654/railway",
        }
    )
    command = [
        sys.executable,
        "-c",
        (
            "import ruoom.settings as s; "
            "db = s.DATABASES['default']; "
            "assert db['ENGINE'] == 'django.db.backends.postgresql'; "
            "assert db['NAME'] == 'railway'; "
            "assert db['USER'] == 'railway_user'; "
            "assert db['PASSWORD'] == 'railway_pass'; "
            "assert db['HOST'] == 'containers-us-west.railway.app'; "
            "assert db['PORT'] == '7654'"
        ),
    ]

    result = subprocess.run(command, env=env, capture_output=True, text=True, check=False)

    assert result.returncode == 0, result.stderr


def test_ruoom_settings_use_secret_key_from_environment():
    env = os.environ.copy()
    env["SECRET_KEY"] = "test-secret-from-env"
    command = [
        sys.executable,
        "-c",
        "import ruoom.settings as s; assert s.SECRET_KEY == 'test-secret-from-env'",
    ]

    result = subprocess.run(command, env=env, capture_output=True, text=True, check=False)

    assert result.returncode == 0, result.stderr


def test_ruoom_settings_require_secret_key_when_debug_false():
    env = os.environ.copy()
    env.pop("SECRET_KEY", None)
    env["DEBUG"] = "false"
    command = [
        sys.executable,
        "-c",
        "import ruoom.settings",
    ]

    result = subprocess.run(command, env=env, capture_output=True, text=True, check=False)

    assert result.returncode != 0
    assert "SECRET_KEY must be set when DEBUG is False" in result.stderr
