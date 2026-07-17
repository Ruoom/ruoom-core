from pathlib import Path

from django.test import override_settings

from security.key_lock import RuoomSecurity


def test_derived_fernet_key_is_deterministic():
    with override_settings(SECRET_KEY="stable-deployment-secret"):
        security = RuoomSecurity()
        assert security._get_key() == security._get_key()


def test_different_django_secret_keys_derive_different_fernet_keys():
    security = RuoomSecurity()
    with override_settings(SECRET_KEY="first-deployment-secret"):
        first_key = security._get_key()
    with override_settings(SECRET_KEY="second-deployment-secret"):
        second_key = security._get_key()

    assert first_key != second_key


def test_encrypt_and_decrypt_roundtrip_uses_django_secret_key():
    with override_settings(SECRET_KEY="stable-deployment-secret"):
        security = RuoomSecurity()
        encrypted = security.process_encryption("sensitive-api-key")

        assert encrypted != "sensitive-api-key"
        assert security.decrypt_message(encrypted) == "sensitive-api-key"


def test_ciphertext_cannot_be_decrypted_after_secret_key_changes():
    security = RuoomSecurity()
    with override_settings(SECRET_KEY="original-deployment-secret"):
        encrypted = security.process_encryption("sensitive-api-key")
    with override_settings(SECRET_KEY="replacement-deployment-secret"):
        assert security.decrypt_message(encrypted) is None


def test_encryption_does_not_create_a_secret_key_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with override_settings(SECRET_KEY="stable-deployment-secret"):
        RuoomSecurity().process_encryption("sensitive-api-key")

    assert not Path("secret.key").exists()
