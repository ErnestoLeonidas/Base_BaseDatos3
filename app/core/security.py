"""Utilidades genéricas de seguridad: hash y verificación de contraseñas con Argon2."""

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

_password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    """Genera el hash Argon2 de una contraseña en texto plano."""
    return _password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Verifica una contraseña en texto plano contra su hash Argon2."""
    try:
        return _password_hasher.verify(password_hash, password)
    except VerifyMismatchError:
        return False
