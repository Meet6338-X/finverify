"""
Unit tests for Ed25519 cryptographic signing, canonicalization, and tamper detection.
"""
import os
import json
import pytest
from src.crypto.signer import CertificateSigner, build_certificate_payload


@pytest.fixture
def signer():
    return CertificateSigner()


def test_keypair_generation(signer):
    pub_hex = signer.get_public_key_hex()
    assert isinstance(pub_hex, str)
    assert len(pub_hex) == 64  # 32 bytes in hex = 64 chars


def test_canonicalize(signer):
    # Keys in payload must be alphabetically sorted and whitespace-free
    payload = {"z_key": 1, "a_key": "val", "m_key": [3, 2, 1]}
    canonical = signer.canonicalize(payload)
    assert canonical == b'{"a_key":"val","m_key":[3,2,1],"z_key":1}'


def test_signing_and_verification(signer):
    payload = build_certificate_payload(
        claim_id="c_12345",
        status="pass",
        expected_value=42.3,
        computed_value=42.3,
        relative_error=0.0,
        discrepancy_trace=[{"step": "gross_margin", "formula": "(rev-cogs)/rev", "computed_value": 0.423}],
        source_refs=["edgar://CIK0000320193/10-K/2025Q4#us-gaap:Revenues"],
    )

    signature, canonical_bytes = signer.sign(payload)
    assert len(signature) == 64  # Ed25519 signature is 64 bytes
    assert signer.verify(payload, signature) is True


def test_tamper_detection(signer):
    payload = build_certificate_payload(
        claim_id="c_12345",
        status="pass",
        expected_value=42.3,
        computed_value=42.3,
        relative_error=0.0,
        discrepancy_trace=[],
        source_refs=[],
    )
    signature, _ = signer.sign(payload)

    # Tampered payload (changed status or value)
    tampered_payload = dict(payload)
    tampered_payload["status"] = "fail"
    assert signer.verify(tampered_payload, signature) is False

    tampered_payload2 = dict(payload)
    tampered_payload2["computed_value"] = 999.0
    assert signer.verify(tampered_payload2, signature) is False
