"""Generate a VAPID P-256 key pair for GeoShield Web Push.

Run:
    cd backend
    python ../tools/generate_vapid_keys.py

Store the private key only in your deployment secret manager / local .env.
Never commit the generated private key.
"""
from __future__ import annotations

import base64

from cryptography.hazmat.primitives.asymmetric import ec


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


private_key = ec.generate_private_key(ec.SECP256R1())
private_raw = private_key.private_numbers().private_value.to_bytes(32, "big")
public_numbers = private_key.public_key().public_numbers()
public_raw = (
    b"\x04"
    + public_numbers.x.to_bytes(32, "big")
    + public_numbers.y.to_bytes(32, "big")
)

print("WEB_PUSH_ENABLED=true")
print(f"VAPID_PUBLIC_KEY={b64url(public_raw)}")
print(f"VAPID_PRIVATE_KEY={b64url(private_raw)}")
print("VAPID_SUBJECT=mailto:YOUR_EMAIL@example.com")
