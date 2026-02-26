from cryptography.fernet import Fernet
import base64
import json
from urllib.parse import quote, unquote
from portality.core import app

class Encryption:
    def __init__(self, key=None):
        # Use provided key or generate a new one
        if key is None:
            key = Fernet.generate_key()
        if isinstance(key, str):
            key = key.encode('utf-8')
        self.fernet = Fernet(key)

    def encrypt_params(self, params: dict) -> str:
        """
        Encrypt parameters
        :param params: Dictionary of parameters to encrypt
        :return: Encrypted string safe for URL
        """
        # Convert params to JSON string
        params_json = json.dumps(params)
        # Fernet.encrypt returns URL-safe base64 token bytes
        token_bytes = self.fernet.encrypt(params_json.encode('utf-8'))
        # Convert to plain string; Fernet output is already URL-safe base64
        return token_bytes.decode('utf-8')

    def decrypt_params(self, encrypted_str: str) -> dict:
        """
        Decrypt parameters
        :param encrypted_str: Encrypted string from URL or form
        :return: Dictionary of decrypted parameters
        """
        try:
            # Use the token string as-is (already URL-safe)
            token_str = encrypted_str
            # Convert back to bytes for Fernet
            token_bytes = token_str.encode('utf-8')
            # Decrypt
            decrypted = self.fernet.decrypt(token_bytes)
            # Parse JSON
            return json.loads(decrypted.decode('utf-8'))
        except Exception as e:
            app.logger.error(f"Failed to decrypt URL params: {str(e)}")
            return {}