"""Canonical secrets, envelope encryption, KMS, service identity, and audit integrity."""

from secrets_crypto.envelope import decrypt_envelope, encrypt_envelope, is_envelope_blob
from secrets_crypto.fips import fips_state
from secrets_crypto.production_policy import assert_production_crypto_policy, is_production_crypto_env

__all__ = [
    "assert_production_crypto_policy",
    "decrypt_envelope",
    "encrypt_envelope",
    "fips_state",
    "is_envelope_blob",
    "is_production_crypto_env",
]
