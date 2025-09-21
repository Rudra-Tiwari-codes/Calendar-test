from __future__ import annotations

from cryptography.fernet import Fernet, InvalidToken

from .settings import settings


def get_fernet() -> Fernet:
    if not settings.fernet_key:
        raise RuntimeError("FERNET_KEY not configured")
    return Fernet(settings.fernet_key)


def encrypt_text(plaintext: str) -> str:
    f = get_fernet()
    return f.encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt_text(ciphertext: str) -> str:
    f = get_fernet()
    return f.decrypt(ciphertext.encode("utf-8")).decode("utf-8")


def encrypt_token(token_data: str) -> str:
    """Encrypt a token (JSON string) for storage."""
    return encrypt_text(token_data)


def decrypt_token(encrypted_token: str) -> str:
    """Decrypt a token for use."""
    return decrypt_text(encrypted_token)


