"""Password hashing and token generation. Stdlib only -- no extra dependencies."""
import hashlib
import hmac
import secrets

_ITERATIONS = 200_000


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), bytes.fromhex(salt), _ITERATIONS
    ).hex()
    return f"{salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt, digest = stored.split("$")
        candidate = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), bytes.fromhex(salt), _ITERATIONS
        ).hex()
    except ValueError:
        # Malformed or empty hash (e.g. an account created before passwords existed).
        return False
    return hmac.compare_digest(candidate, digest)


def new_token() -> str:
    return secrets.token_urlsafe(32)
