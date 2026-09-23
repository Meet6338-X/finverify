import json
import os
import hashlib
from typing import Dict, Tuple, Optional
import nacl.signing
import nacl.encoding
import qrcode
from datetime import datetime, timezone

class CertificateSigner:
    def __init__(self, signing_key_path: Optional[str] = None):
        self.signing_key_path = signing_key_path
        self.signing_key = None
        
        # 1. Try to load from specified path if exists and valid
        if signing_key_path and os.path.exists(signing_key_path):
            try:
                with open(signing_key_path, "rb") as f:
                    key_bytes = f.read()
                    if len(key_bytes) == 32:
                        self.signing_key = nacl.signing.SigningKey(key_bytes)
            except Exception:
                self.signing_key = None

        # 2. Derive deterministically from environment secret to ensure all containers share the identical keypair
        if self.signing_key is None:
            jwt_secret = os.getenv("JWT_SECRET", "changeme-jwt-secret")
            # Deterministic 32-byte seed derived via SHA-256
            seed = hashlib.sha256(f"finverify-signing-seed:{jwt_secret}".encode('utf-8')).digest()
            self.signing_key = nacl.signing.SigningKey(seed)
            
            # Save key to path if path was provided
            if signing_key_path:
                try:
                    os.makedirs(os.path.dirname(os.path.abspath(signing_key_path)), exist_ok=True)
                    with open(signing_key_path, "wb") as f:
                        f.write(self.signing_key.encode())
                except Exception:
                    pass
                    
        self.verify_key = self.signing_key.verify_key

    def canonicalize(self, payload: dict) -> bytes:
        return json.dumps(payload, sort_keys=True, separators=(',', ':')).encode('utf-8')

    def sign(self, payload: dict) -> Tuple[bytes, bytes]:
        canonical_bytes = self.canonicalize(payload)
        signed = self.signing_key.sign(canonical_bytes)
        return signed.signature, canonical_bytes

    def verify(self, payload: dict, signature: bytes) -> bool:
        canonical_bytes = self.canonicalize(payload)
        try:
            self.verify_key.verify(canonical_bytes, signature)
            return True
        except Exception:
            return False

    def get_public_key_hex(self) -> str:
        return self.verify_key.encode(encoder=nacl.encoding.HexEncoder).decode('utf-8')

    def get_verify_key_bytes(self) -> bytes:
        return self.verify_key.encode()

def generate_qr_code(data: str, output_path: str) -> str:
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    img.save(output_path)
    return output_path

def build_certificate_payload(
    claim_id: str,
    status: str,
    expected_value: float,
    computed_value: Optional[float],
    relative_error: Optional[float],
    discrepancy_trace: list,
    source_refs: list,
    timestamp: Optional[str] = None
) -> dict:
    if timestamp is None:
        timestamp = datetime.now(timezone.utc).isoformat()
        
    return {
        "claim_id": claim_id,
        "status": status,
        "expected_value": expected_value,
        "computed_value": computed_value,
        "relative_error": relative_error,
        "discrepancy_trace": discrepancy_trace,
        "source_refs": source_refs,
        "timestamp": timestamp
    }
