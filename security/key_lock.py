"""Fernet encryption for credentials stored in the database."""

import base64
import hashlib
import logging

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings


logger = logging.getLogger(__name__)

_KDF_SALT = b"ruoom-credential-encryption-v1"
_KDF_ITERATIONS = 100_000


class RuoomSecurity:
    """Encrypt and decrypt values with a key derived from Django's secret key."""

    def _derive_key_from_secret(self):
        secret = getattr(settings, "SECRET_KEY", "")
        if not secret:
            raise RuntimeError(
                "SECRET_KEY is not configured; cannot derive the Fernet key."
            )

        derived_key = hashlib.pbkdf2_hmac(
            "sha256",
            str(secret).encode("utf-8"),
            _KDF_SALT,
            _KDF_ITERATIONS,
            dklen=32,
        )
        return base64.urlsafe_b64encode(derived_key)

    def _get_key(self):
        return self._derive_key_from_secret()

    def decrypt_message(self, encrypted_message):
        if not encrypted_message:
            return None

        try:
            fernet = Fernet(self._get_key())
            return fernet.decrypt(encrypted_message.encode("utf-8")).decode("utf-8")
        except (InvalidToken, AttributeError, TypeError, ValueError):
            logger.warning(
                "Credential decryption failed because the value is invalid or "
                "SECRET_KEY has changed."
            )
            return None

    def process_encryption(self, encryption_value):
        fernet = Fernet(self._get_key())
        return fernet.encrypt(str(encryption_value).encode("utf-8")).decode("utf-8")
