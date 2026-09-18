"""Local checkout configuration and audit-key validation; no secret logging."""

import stat
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from dotenv import dotenv_values

HA_URL = "http://127.0.0.1:8123"
REQUEST_TIMEOUT = 10
# HA's unmodified demo integration: real API, simulated devices.
DEMO_ENTITIES = {
    "light.bed_light",
    "climate.ecobee",
    "cover.garage_door",
    "sensor.outside_temperature",
}


class LocalError(Exception):
    """An actionable message safe to print, without upstream details."""


def read_env(path: Path) -> dict[str, str]:
    if path.is_symlink() or (path.exists() and not path.is_file()):
        raise LocalError(".env must be a regular file, not a symlink.")
    if not path.exists():
        return {}
    if stat.S_IMODE(path.stat().st_mode) != 0o600:
        raise LocalError(".env must have mode 0600; run chmod 600 .env.")
    return {k: v for k, v in dotenv_values(path, interpolate=False).items() if v}


def signing_key(values: dict[str, str]) -> ec.EllipticCurvePrivateKey:
    pem = values.get("AUDIT_SIGNING_KEY")
    if not pem:
        raise LocalError("AUDIT_SIGNING_KEY is missing; run scripts/init_dev.py.")
    try:
        key = serialization.load_pem_private_key(pem.encode(), password=None)
        if not isinstance(key, ec.EllipticCurvePrivateKey) or not isinstance(
            key.curve, ec.SECP256R1
        ):
            raise ValueError
        probe = b"hirz doctor signing-key check"
        signature = key.sign(probe, ec.ECDSA(hashes.SHA256()))
        key.public_key().verify(signature, probe, ec.ECDSA(hashes.SHA256()))
    except Exception:
        raise LocalError(
            "AUDIT_SIGNING_KEY must be a working unencrypted P-256 private key; "
            "restore the original key, do not replace it."
        ) from None
    return key
