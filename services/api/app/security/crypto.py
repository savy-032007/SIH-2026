"""Field-level encryption and deterministic lookup hashes (SPEC section 8).

Two separate jobs, deliberately kept apart:

* **Encryption** (`encrypt_field` / `decrypt_field`) — AES-256-GCM, randomised, so
  the same APAAR ID encrypts to different ciphertext every time. Good for
  confidentiality, useless for lookups.
* **Hashing** (`hmac_hash`) — HMAC-SHA256 under a pepper, deterministic, so rows
  can be found and uniqueness enforced without ever decrypting. Keyed rather than
  plain SHA-256 because a 12-digit APAAR space is trivially brute-forced.

Key derivation: a per-context subkey is derived from the master key with HKDF, so
the phone subkey cannot decrypt an APAAR ciphertext. SPEC section 8 describes an
envelope scheme with a KMS-held data key; a per-record wrapped-DEK design would
need a key table SPEC section 5 does not define, so the swap point lives in
`KeyProvider` instead and the cloud path replaces `LocalKeyProvider` with
`KmsKeyProvider`.

Aadhaar is never collected, hashed or stored anywhere in this module.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import re
import unicodedata
from abc import ABC, abstractmethod
from functools import lru_cache

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from app.config import get_settings

#: Ciphertext layout version. Stored as the first byte so the scheme can change
#: without a data migration guessing game.
_VERSION = 1
_NONCE_BYTES = 12


class CryptoError(Exception):
    """Raised when ciphertext cannot be authenticated or is malformed."""


# --------------------------------------------------------------------------- #
# Key providers
# --------------------------------------------------------------------------- #


class KeyProvider(ABC):
    """Source of the master key that context subkeys are derived from."""

    @property
    @abstractmethod
    def key_id(self) -> str:
        """Identifier recorded alongside anything this key protects."""

    @abstractmethod
    def master_key(self) -> bytes:
        """32 raw bytes."""


class LocalKeyProvider(KeyProvider):
    """Development provider: master key straight from the environment."""

    def __init__(self, b64_key: str, key_id: str) -> None:
        raw = base64.b64decode(b64_key, validate=True)
        if len(raw) != 32:
            raise CryptoError(f"master key must be 32 bytes, got {len(raw)}")
        self._raw = raw
        self._key_id = key_id

    @property
    def key_id(self) -> str:
        return self._key_id

    def master_key(self) -> bytes:
        return self._raw


class KmsKeyProvider(KeyProvider):
    """Production provider — intentionally unimplemented.

    The cloud design (SPEC section 3) is AWS KMS holding the master key and
    issuing data keys. Filling this in is the only change encryption needs to
    move off a local key: call `kms:GenerateDataKey`, cache the plaintext data
    key in memory for a short TTL, and keep the wrapped copy with the record.
    """

    def __init__(self, key_arn: str) -> None:
        self._key_arn = key_arn

    @property
    def key_id(self) -> str:
        return self._key_arn

    def master_key(self) -> bytes:
        raise NotImplementedError(
            "KmsKeyProvider is a documented stub. Set KEY_PROVIDER=local for "
            "development, or implement AWS KMS GenerateDataKey here before "
            "deploying with KEY_PROVIDER=kms."
        )


@lru_cache
def get_key_provider() -> KeyProvider:
    settings = get_settings()
    if settings.key_provider == "kms":
        return KmsKeyProvider(settings.key_id)
    return LocalKeyProvider(settings.field_master_key, settings.key_id)


@lru_cache(maxsize=32)
def _subkey(context: str) -> bytes:
    """Derive the AES key for one field context."""
    return HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=f"apaar:field:{context}".encode(),
    ).derive(get_key_provider().master_key())


# --------------------------------------------------------------------------- #
# Encryption
# --------------------------------------------------------------------------- #


def encrypt_field(plaintext: str | None, context: str) -> bytes | None:
    """Encrypt one field value. `context` binds the ciphertext to its column.

    Returns ``version || nonce || ciphertext+tag``. The context is also fed in as
    AES-GCM associated data, so a phone ciphertext moved into the email column
    fails to authenticate instead of decrypting to a plausible value.
    """
    if plaintext is None:
        return None
    nonce = os.urandom(_NONCE_BYTES)
    sealed = AESGCM(_subkey(context)).encrypt(
        nonce, plaintext.encode("utf-8"), context.encode("utf-8")
    )
    return bytes([_VERSION]) + nonce + sealed


def decrypt_field(blob: bytes | None, context: str) -> str | None:
    """Reverse `encrypt_field`. Raises `CryptoError` on any tampering."""
    if blob is None:
        return None
    if len(blob) < 1 + _NONCE_BYTES + 16:
        raise CryptoError("ciphertext too short")
    version = blob[0]
    if version != _VERSION:
        raise CryptoError(f"unsupported ciphertext version {version}")
    nonce = blob[1 : 1 + _NONCE_BYTES]
    sealed = blob[1 + _NONCE_BYTES :]
    try:
        opened = AESGCM(_subkey(context)).decrypt(nonce, sealed, context.encode("utf-8"))
    except Exception as exc:
        raise CryptoError(f"could not authenticate {context} ciphertext") from exc
    return opened.decode("utf-8")


# --------------------------------------------------------------------------- #
# Deterministic hashes
# --------------------------------------------------------------------------- #


def hmac_hash(value: str | None, context: str) -> str | None:
    """Keyed, deterministic hash for lookups and uniqueness.

    Input is normalised first so `+91 98765 43210` and `9876543210` collide on
    purpose — that is what makes the shared-contact ghost graph (SPEC 6.2) work.
    """
    if value is None:
        return None
    normalised = normalize_for_context(value, context)
    if not normalised:
        return None
    settings = get_settings()
    return hmac.new(
        key=settings.hash_pepper.encode("utf-8"),
        msg=f"{context}:{normalised}".encode(),
        digestmod=hashlib.sha256,
    ).hexdigest()


def normalize_for_context(value: str, context: str) -> str:
    """Dispatch to the normaliser for a field context."""
    match context:
        case "apaar":
            return normalize_digits(value)
        case "phone":
            return normalize_phone(value)
        case "email":
            return normalize_email(value)
        case "address":
            return normalize_address(value)
        case "name" | "guardian_name":
            return normalize_name(value)
        case _:
            return value.strip().casefold()


def normalize_digits(value: str) -> str:
    return re.sub(r"\D", "", value)


def normalize_phone(value: str) -> str:
    """Digits only, with the Indian country code stripped to the 10-digit number."""
    digits = normalize_digits(value)
    if len(digits) > 10 and digits.startswith("91"):
        digits = digits[-10:]
    elif len(digits) == 11 and digits.startswith("0"):
        digits = digits[1:]
    return digits


def normalize_email(value: str) -> str:
    return value.strip().casefold()


_HONORIFICS = (
    "mr",
    "mrs",
    "ms",
    "miss",
    "dr",
    "shri",
    "shrimati",
    "smt",
    "kum",
    "md",
    "mohd",
    "sri",
)


def normalize_name(value: str) -> str:
    """Fold a person's name to a comparable form.

    Strips accents, honorifics and punctuation, collapses whitespace. Deliberately
    does *not* apply the transliteration folds (`ee->i` and friends) — those belong
    to the V2.NAME_MISMATCH fuzzy comparison in Phase 2, where a similarity score
    is wanted. Folding them here would make two genuinely different names hash
    alike and silently merge students.
    """
    decomposed = unicodedata.normalize("NFKD", value)
    ascii_only = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    cleaned = re.sub(r"[^\w\s]", " ", ascii_only, flags=re.UNICODE).casefold()
    tokens = [tok for tok in cleaned.split() if tok and tok not in _HONORIFICS]
    return " ".join(tokens)


_ADDRESS_NOISE = {
    "near",
    "opp",
    "opposite",
    "behind",
    "beside",
    "no",
    "number",
    "flat",
    "plot",
    "house",
    "building",
    "bldg",
    "road",
    "rd",
    "street",
    "st",
    "lane",
    "ln",
    "nagar",
    "colony",
    "sector",
    "phase",
    "block",
}

_ADDRESS_ABBREVIATIONS = {
    "apt": "apartment",
    "apts": "apartment",
    "mg": "mahatma gandhi",
    "dist": "district",
    "tal": "taluka",
    "po": "post office",
    "ps": "police station",
}


def normalize_address(value: str) -> str:
    """Fold an address to a stable key for the ghost-student graph.

    Two students at the same address should produce the same hash despite typing
    it differently, so this drops punctuation and filler words, expands common
    abbreviations and sorts the remaining tokens — word order in Indian addresses
    varies far too much to rely on.
    """
    decomposed = unicodedata.normalize("NFKD", value)
    ascii_only = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    cleaned = re.sub(r"[^\w\s]", " ", ascii_only, flags=re.UNICODE).casefold()
    tokens = []
    for raw in cleaned.split():
        token = _ADDRESS_ABBREVIATIONS.get(raw, raw)
        if token in _ADDRESS_NOISE:
            continue
        tokens.extend(token.split())
    return " ".join(sorted(tokens))


# --------------------------------------------------------------------------- #
# Masking
# --------------------------------------------------------------------------- #


def mask_apaar(apaar_id: str | None) -> str:
    """`XXXX-XXXX-1234` — the only form the UI shows by default (SPEC section 8)."""
    if not apaar_id:
        return "XXXX-XXXX-XXXX"
    digits = normalize_digits(apaar_id)
    return f"XXXX-XXXX-{digits[-4:]}" if len(digits) >= 4 else "XXXX-XXXX-XXXX"


def mask_name(name: str) -> str:
    """Keep the first letter of each word: `Aarav Sharma` -> `A**** S*****`."""
    parts = []
    for word in name.split():
        parts.append(word[0] + "*" * (len(word) - 1) if len(word) > 1 else word)
    return " ".join(parts)


def mask_phone(phone: str | None) -> str:
    if not phone:
        return "XXXXXXXXXX"
    digits = normalize_phone(phone)
    return f"XXXXXX{digits[-4:]}" if len(digits) >= 4 else "XXXXXXXXXX"


def mask_email(email: str | None) -> str:
    if not email or "@" not in email:
        return "***@***"
    local, _, domain = email.partition("@")
    shown = local[0] if local else "*"
    return f"{shown}{'*' * max(len(local) - 1, 1)}@{domain}"


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def last4(value: str | None) -> str | None:
    if not value:
        return None
    digits = normalize_digits(value)
    return digits[-4:] if len(digits) >= 4 else None
