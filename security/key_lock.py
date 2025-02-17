"""
This file contains logic for encryption and decryption
the logic and implementation applied here can be confirmed from

https://devqa.io/encrypt-decrypt-data-python/

"""

from cryptography.fernet import Fernet
from ruoom.settings import SECRET_FILE_NAME
import os

class RuoomSecurity:

    def __init__(self):
        """
        constructor consist of a protected attribute which
        will be set through protected method '_load_key'
        """
        self._key = ''

    def _generate_key(self):
        """
        Generates a key and save it into a file

        Note: You need to keep this key in a safe place.
        If you lose the key, you won't be able to decrypt
        the data that was encrypted with this key.
        """
        if not self._is_key_available():
            key = Fernet.generate_key()
            new_folder = os.path.abspath(os.path.join(SECRET_FILE_NAME, ".."))
            if not os.path.exists(new_folder):
                os.makedirs(new_folder)
            with open(SECRET_FILE_NAME, "wb") as key_file:
                key_file.write(key)

    def _is_key_available(self):
        """
        this methods check if the key was generated or not

        Returns:
            (type = bool): it will return False if data was
            not found or will return true if data was there
        """
        try:
            generated_key = open(SECRET_FILE_NAME, "rb").read()
            return bool(generated_key)
        except:
            return False

    def _load_key(self):
        """
        Loads the key from the file 'SECRET_FILE_NAME' which
        is in  the current directory and set to instance attribute 'key'
        """
        key = open(SECRET_FILE_NAME, "rb").read()
        self._key = key

    def decrypt_message(self, encrypted_message):
        """
        Decrypts an encrypted message
        """
        if self._is_key_available():
            encoded_message = encrypted_message.encode()
            self._load_key()
            key = self._key
            fernet = Fernet(key)
            decrypted_message = fernet.decrypt(encoded_message)

            return decrypted_message.decode()
        else:
            print("Stored key exists, but no hash file is found. Stored key cannot be decrypted.")
            return None

    def process_encryption(self, encryption_value):
        """
        this method is the primary method to be called when
        encryption is to be applied and it will then call
        all other methods within class which are marked as
        protected member,to make hashes against 'encryption_value'

        Args:
            encryption_value (type = str) : its the value which is
            required to be in hashes

        Returns:
            (type = str) : it will give the hash str which will be
            encrypted
        """

        self._generate_key()
        self._load_key()
        key = self._key
        fernet = Fernet(key)
        encrypted_message = fernet.encrypt(encryption_value.encode())
        return encrypted_message.decode("utf-8")
