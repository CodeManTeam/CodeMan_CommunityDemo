from cryptography.fernet import Fernet
import os
import base64

# Use a consistent key derived from a secret or generated one.
# In production, this KEY should be in environment variables and never committed.
# For this internal tool, we will generate/load a key from a local file.

KEY_FILE = "credential_key.key"

def load_key():
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, "rb") as key_file:
            return key_file.read()
    else:
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as key_file:
            key_file.write(key)
        return key

cipher_suite = Fernet(load_key())

def encrypt_data(data: str) -> str:
    """Encrypts a string and returns a base64 encoded string."""
    if not data:
        return None
    return cipher_suite.encrypt(data.encode()).decode()

def decrypt_data(encrypted_data: str) -> str:
    """Decrypts a base64 encoded string and returns the original string."""
    if not encrypted_data:
        return None
    try:
        return cipher_suite.decrypt(encrypted_data.encode()).decode()
    except Exception as e:
        print(f"Decryption error: {e}")
        return None
