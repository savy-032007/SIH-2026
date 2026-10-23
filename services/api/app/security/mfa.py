"""TOTP multi-factor authentication (SPEC section 8).

Mandatory for every AICTE_* role and for INST_ADMIN. The shared secret is stored
encrypted (`app_user.totp_secret_enc`), never in plaintext.
"""

import pyotp

from app.security.crypto import decrypt_field, encrypt_field

_TOTP_CONTEXT = "totp_secret"
_ISSUER = "AICTE APAAR"

#: Accept the adjacent 30s steps, which covers normal clock drift between the
#: authenticator app and the server. Wider windows trade security for comfort.
_VALID_WINDOW = 1


def generate_secret() -> str:
    """A fresh base32 TOTP secret."""
    return pyotp.random_base32()


def encrypt_secret(secret: str) -> bytes:
    blob = encrypt_field(secret, _TOTP_CONTEXT)
    assert blob is not None  # secret is never None here
    return blob


def decrypt_secret(blob: bytes) -> str:
    secret = decrypt_field(blob, _TOTP_CONTEXT)
    if secret is None:
        raise ValueError("stored TOTP secret is empty")
    return secret


def provisioning_uri(secret: str, email: str) -> str:
    """`otpauth://` URI for an authenticator app (or a QR code)."""
    return pyotp.TOTP(secret).provisioning_uri(name=email, issuer_name=_ISSUER)


def verify_code(secret: str, code: str) -> bool:
    """Check a 6-digit code against the secret.

    Note the known limitation: a code stays valid for the whole step window, so a
    code observed in transit could be replayed within ~90s. Closing that needs a
    last-used-counter column, which SPEC section 5 does not define on `user`;
    revisit alongside the Phase 5 hardening pass.
    """
    cleaned = code.strip().replace(" ", "")
    if not cleaned.isdigit():
        return False
    return pyotp.TOTP(secret).verify(cleaned, valid_window=_VALID_WINDOW)


def current_code(secret: str) -> str:
    """The code valid right now — used by tests and the seeded demo output."""
    return pyotp.TOTP(secret).now()
