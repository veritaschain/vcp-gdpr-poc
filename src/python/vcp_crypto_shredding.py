#!/usr/bin/env python3
"""
VCP v1.1 Crypto-Shredding Implementation
=========================================

Demonstrates field encryption, simulated key-store removal and local
hash-chain checks. Secure destruction and regulatory compliance are not established.

Compliance References:
- GDPR Article 17 (Right to Erasure)
- MiFID II Article 16(7) (5-7 year retention)
- EDPB Guidelines 02/2025 (Blockchain and GDPR)

(C) 2025 VeritasChain Standards Organization
Licensed under Apache 2.0
"""

import hashlib
import json
import os
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import base64

# Cryptography imports
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.backends import default_backend


class EventType(Enum):
    """VCP Event Types"""
    SIG = "SIG"  # Signal
    ORD = "ORD"  # Order
    ACK = "ACK"  # Acknowledgment
    EXE = "EXE"  # Execution
    REJ = "REJ"  # Rejection
    CXL = "CXL"  # Cancellation
    GOV = "GOV"  # Governance
    ERA = "ERA"  # Erasure


class ClockSyncStatus(Enum):
    """MiFID II RTS 25 Clock Synchronization Status"""
    UNKNOWN = "UNKNOWN"
    NTP_SYNCED = "NTP_SYNCED"
    PTP_LOCKED = "PTP_LOCKED"
    GPS_SYNCED = "GPS_SYNCED"
    UNSYNCHRONIZED = "UNSYNCHRONIZED"


class TimestampPrecision(Enum):
    """Timestamp precision levels"""
    SECOND = "SECOND"
    MILLISECOND = "MILLISECOND"
    MICROSECOND = "MICROSECOND"
    NANOSECOND = "NANOSECOND"


@dataclass
class PIIEncryptionResult:
    """Result of PII field encryption"""
    key_id: str
    nonce: str
    ciphertext: str
    algorithm: str = "AES-256-GCM"
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    def to_marker(self) -> str:
        """Return encrypted marker string for JSON serialization"""
        return f"ENC:{self.algorithm}:{self.key_id}"


@dataclass
class VCPEventHeader:
    """VCP Event Header (v1.1)"""
    event_id: str
    event_type: str
    timestamp: str
    timestamp_int: int  # Nanoseconds since epoch
    timestamp_precision: str
    clock_sync_status: str
    prev_hash: str
    event_hash: str = ""
    pii_key_ids: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class VCPEvent:
    """Complete VCP Event structure"""
    header: VCPEventHeader
    payload: Dict[str, Any]
    gdpr_metadata: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        result = {
            "header": self.header.to_dict(),
            "payload": self.payload
        }
        if self.gdpr_metadata:
            result["gdpr_metadata"] = self.gdpr_metadata
        return result
    
    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, default=str)


@dataclass
class ErasureCertificate:
    """
    Unsigned local report of simulated key-removal actions.
    Verification booleans are preset values, not measured verification results.
    """
    certificate_id: str
    version: str = "1.0"
    type: str = "VCP_ERASURE_CERTIFICATE"
    subject_id_hash: str = ""
    erasure_timestamp: str = ""
    keys_destroyed: int = 0
    key_ids_destroyed: List[str] = field(default_factory=list)
    method: str = "CRYPTOGRAPHIC_KEY_DESTRUCTION"
    compliance_references: List[str] = field(default_factory=lambda: [
        "GDPR Article 17(1)",
        "EDPB Guidelines 02/2025",
        "VCP-PRIVACY v1.1"
    ])
    verification: Dict[str, bool] = field(default_factory=lambda: {
        "hash_chain_intact": True,
        "pii_recoverable": False,
        "audit_trail_preserved": True
    })
    certificate_hash: str = ""
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)


class KeyManagementSystem:
    """
    Simulated in-memory key store for the local demonstration.
    Removing a stored reference does not prove destruction of retained copies
    or memory zeroization. Production key management is outside this PoC.
    """
    
    def __init__(self):
        self._keys: Dict[str, bytes] = {}
        self._key_metadata: Dict[str, Dict] = {}
        self._destruction_log: List[Dict] = []
    
    def generate_key(self, subject_id: str, purpose: str = "PII_ENCRYPTION") -> str:
        """Generate and store a new encryption key"""
        key = AESGCM.generate_key(bit_length=256)
        key_id = f"KEY-{subject_id}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(4)}"
        
        self._keys[key_id] = key
        self._key_metadata[key_id] = {
            "subject_id": subject_id,
            "created_at": datetime.now(timezone.utc).isoformat() + "Z",
            "purpose": purpose,
            "status": "ACTIVE"
        }
        
        return key_id
    
    def get_key(self, key_id: str) -> Optional[bytes]:
        """Retrieve a key by ID"""
        return self._keys.get(key_id)
    
    def destroy_key(self, key_id: str) -> bool:
        """
        Remove a key from the simulated store.
        Returns True if the stored entry was removed; retained copies are not checked.
        """
        if key_id not in self._keys:
            return False
        
        # Replace the stored reference; this does not zeroize retained key bytes.
        key_length = len(self._keys[key_id])
        self._keys[key_id] = os.urandom(key_length)
        
        # Delete the key
        del self._keys[key_id]
        
        # Update metadata
        if key_id in self._key_metadata:
            self._key_metadata[key_id]["status"] = "DESTROYED"
            self._key_metadata[key_id]["destroyed_at"] = datetime.now(timezone.utc).isoformat() + "Z"
        
        # Log destruction
        self._destruction_log.append({
            "key_id": key_id,
            "destroyed_at": datetime.now(timezone.utc).isoformat() + "Z",
            "method": "SECURE_OVERWRITE_AND_DELETE"
        })
        
        return True
    
    def get_keys_for_subject(self, subject_id: str) -> List[str]:
        """Get all key IDs associated with a subject"""
        return [
            key_id for key_id, metadata in self._key_metadata.items()
            if metadata.get("subject_id") == subject_id and metadata.get("status") == "ACTIVE"
        ]
    
    def get_destruction_log(self) -> List[Dict]:
        """Get the key destruction audit log"""
        return self._destruction_log.copy()


class VCPCryptoShredder:
    """
    VCP v1.1 Crypto-Shredding Implementation
    
    Demonstrates a possible erasure/retention design approach by:
    1. Encrypting PII with per-subject keys
    2. Maintaining hash chain integrity with encrypted data
    3. Removing keys from a simulated store
    4. Preserving audit trail integrity post-erasure
    
    Designed with EDPB Guidelines 02/2025 in mind (compliance not determined)
    """
    
    def __init__(self, kms: Optional[KeyManagementSystem] = None):
        """Initialize with optional KMS (defaults to simulated KMS)"""
        self.kms = kms or KeyManagementSystem()
        self._event_chain: List[VCPEvent] = []
        self._encrypted_data_store: Dict[str, PIIEncryptionResult] = {}
    
    def _generate_uuid7(self) -> str:
        """
        Generate UUIDv7 (time-ordered)
        Simplified implementation - use uuid6 library in production
        """
        timestamp_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        timestamp_hex = format(timestamp_ms, '012x')
        random_hex = secrets.token_hex(10)
        
        # UUIDv7 format: tttttttt-tttt-7xxx-yxxx-xxxxxxxxxxxx
        uuid_str = f"{timestamp_hex[:8]}-{timestamp_hex[8:12]}-7{random_hex[:3]}-{random_hex[3:7]}-{random_hex[7:19]}"
        return uuid_str
    
    def _get_timestamp(self) -> Tuple[str, int]:
        """Get ISO timestamp and nanosecond integer"""
        now = datetime.now(timezone.utc)
        iso_str = now.strftime('%Y-%m-%dT%H:%M:%S.%f') + "Z"
        # Nanoseconds since epoch (microseconds * 1000)
        ns_int = int(now.timestamp() * 1_000_000_000)
        return iso_str, ns_int
    
    def encrypt_pii(self, plaintext: str, key_id: str) -> PIIEncryptionResult:
        """
        Encrypt PII data with the specified key
        Uses AES-256-GCM for authenticated encryption
        """
        key = self.kms.get_key(key_id)
        if not key:
            raise ValueError(f"Key not found: {key_id}")
        
        nonce = os.urandom(12)  # 96-bit nonce for GCM
        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(nonce, plaintext.encode('utf-8'), None)
        
        result = PIIEncryptionResult(
            key_id=key_id,
            nonce=base64.b64encode(nonce).decode('ascii'),
            ciphertext=base64.b64encode(ciphertext).decode('ascii')
        )
        
        # Store for potential decryption
        store_key = f"{key_id}:{base64.b64encode(nonce).decode('ascii')}"
        self._encrypted_data_store[store_key] = result
        
        return result
    
    def decrypt_pii(self, encrypted: PIIEncryptionResult) -> Optional[str]:
        """
        Decrypt PII data (only possible if key still exists)
        Returns None if the key is absent from this store.
        """
        key = self.kms.get_key(encrypted.key_id)
        if not key:
            return None  # Key absent from this store; copies are not assessed.
        
        try:
            nonce = base64.b64decode(encrypted.nonce)
            ciphertext = base64.b64decode(encrypted.ciphertext)
            aesgcm = AESGCM(key)
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)
            return plaintext.decode('utf-8')
        except Exception:
            return None
    
    def _calculate_hash(self, prev_hash: str, content: str) -> str:
        """Calculate SHA-256 hash for chain integrity"""
        combined = prev_hash + content
        return hashlib.sha256(combined.encode('utf-8')).hexdigest()
    
    def create_event(
        self,
        event_type: EventType,
        payload: Dict[str, Any],
        pii_fields: List[str],
        subject_id: str,
        clock_sync_status: ClockSyncStatus = ClockSyncStatus.NTP_SYNCED,
        timestamp_precision: TimestampPrecision = TimestampPrecision.MICROSECOND
    ) -> VCPEvent:
        """
        Create a VCP event with encrypted PII fields
        
        Args:
            event_type: Type of event (ORD, EXE, etc.)
            payload: Event data
            pii_fields: List of field names containing PII to encrypt
            subject_id: Data subject identifier (for key management)
            clock_sync_status: MiFID II RTS 25 clock sync status
            timestamp_precision: Timestamp precision level
        
        Returns:
            VCPEvent with encrypted PII and hash chain linkage
        """
        # Get previous hash
        if self._event_chain:
            prev_hash = self._event_chain[-1].header.event_hash
        else:
            prev_hash = "0" * 64  # Genesis hash
        
        # Generate or get key for subject
        existing_keys = self.kms.get_keys_for_subject(subject_id)
        if existing_keys:
            key_id = existing_keys[0]
        else:
            key_id = self.kms.generate_key(subject_id)
        
        # Encrypt PII fields
        encrypted_payload = payload.copy()
        encrypted_pii_markers = {}
        
        for field_name in pii_fields:
            if field_name in encrypted_payload:
                original_value = str(encrypted_payload[field_name])
                encryption_result = self.encrypt_pii(original_value, key_id)
                encrypted_payload[field_name] = encryption_result.to_dict()
                encrypted_pii_markers[field_name] = encryption_result.to_marker()
        
        # Generate timestamps
        timestamp_str, timestamp_int = self._get_timestamp()
        
        # Create header
        header = VCPEventHeader(
            event_id=self._generate_uuid7(),
            event_type=event_type.value,
            timestamp=timestamp_str,
            timestamp_int=timestamp_int,
            timestamp_precision=timestamp_precision.value,
            clock_sync_status=clock_sync_status.value,
            prev_hash=prev_hash,
            pii_key_ids=[key_id]
        )
        
        # Calculate event hash
        content_for_hash = json.dumps(encrypted_payload, sort_keys=True, default=str)
        header.event_hash = self._calculate_hash(prev_hash, content_for_hash)
        
        # GDPR metadata
        gdpr_metadata = {
            "pii_fields_encrypted": pii_fields,
            "subject_id_hash": hashlib.sha256(subject_id.encode()).hexdigest(),
            "retention_until": (datetime.now(timezone.utc) + timedelta(days=5*365)).isoformat() + "Z",
            "erasure_eligible": False,
            "legal_basis": "MiFID II Article 16(7)"
        }
        
        # Create event
        event = VCPEvent(
            header=header,
            payload=encrypted_payload,
            gdpr_metadata=gdpr_metadata
        )
        
        # Add to chain
        self._event_chain.append(event)
        
        return event
    
    def execute_erasure(self, subject_id: str) -> ErasureCertificate:
        """
        Remove the subject's keys from the simulated store.
        
        Encrypted payloads remain in the chain. This action does not prove
        destruction of retained key or plaintext copies, memory zeroization,
        or legal compliance. Inspect chain integrity with the separate verifier.
        
        Args:
            subject_id: Data subject requesting erasure
        
        Returns:
            Unsigned local report with preset verification booleans.
        """
        # Get all keys for subject
        key_ids = self.kms.get_keys_for_subject(subject_id)
        
        if not key_ids:
            raise ValueError(f"No active keys found for subject")
        
        # Destroy all keys
        destroyed_keys = []
        for key_id in key_ids:
            if self.kms.destroy_key(key_id):
                destroyed_keys.append(key_id)
        
        # Create erasure event in chain
        erasure_payload = {
            "action": "GDPR_ERASURE",
            "subject_id_hash": hashlib.sha256(subject_id.encode()).hexdigest(),
            "keys_destroyed": len(destroyed_keys),
            "method": "CRYPTOGRAPHIC_KEY_DESTRUCTION"
        }
        
        erasure_event = self.create_event(
            event_type=EventType.ERA,
            payload=erasure_payload,
            pii_fields=[],
            subject_id="SYSTEM"
        )
        
        # Generate certificate
        certificate = ErasureCertificate(
            certificate_id=self._generate_uuid7(),
            subject_id_hash=hashlib.sha256(subject_id.encode()).hexdigest(),
            erasure_timestamp=datetime.now(timezone.utc).isoformat() + "Z",
            keys_destroyed=len(destroyed_keys),
            key_ids_destroyed=destroyed_keys
        )
        
        # Calculate certificate hash
        cert_content = json.dumps(certificate.to_dict(), sort_keys=True)
        certificate.certificate_hash = hashlib.sha256(cert_content.encode()).hexdigest()
        
        return certificate
    
    def verify_chain_integrity(self) -> Dict[str, Any]:
        """
        Verify the integrity of the entire event chain
        
        This verification works even after crypto-shredding because:
        1. Hash chain is computed over encrypted data
        2. Encrypted data remains in place (only keys are destroyed)
        3. Chain integrity is independent of data recoverability
        
        Returns:
            Verification result with details
        """
        if not self._event_chain:
            return {
                "verified": True,
                "events_checked": 0,
                "message": "Empty chain"
            }
        
        results = {
            "verified": True,
            "events_checked": len(self._event_chain),
            "errors": [],
            "verified_at": datetime.now(timezone.utc).isoformat() + "Z"
        }
        
        for i, event in enumerate(self._event_chain):
            # Check chain linkage
            if i == 0:
                expected_prev = "0" * 64
            else:
                expected_prev = self._event_chain[i-1].header.event_hash
            
            if event.header.prev_hash != expected_prev:
                results["verified"] = False
                results["errors"].append({
                    "event_index": i,
                    "event_id": event.header.event_id,
                    "error": "PREV_HASH_MISMATCH",
                    "expected": expected_prev,
                    "actual": event.header.prev_hash
                })
            
            # Verify event hash
            content_for_hash = json.dumps(event.payload, sort_keys=True, default=str)
            expected_hash = self._calculate_hash(event.header.prev_hash, content_for_hash)
            
            if event.header.event_hash != expected_hash:
                results["verified"] = False
                results["errors"].append({
                    "event_index": i,
                    "event_id": event.header.event_id,
                    "error": "EVENT_HASH_MISMATCH",
                    "expected": expected_hash,
                    "actual": event.header.event_hash
                })
        
        return results
    
    def can_recover_pii(self, event: VCPEvent) -> Dict[str, bool]:
        """
        Check whether encrypted fields' keys exist in this simulated store.
        This does not test decryption or destruction of retained copies.
        """
        result = {}
        
        for field_name, field_value in event.payload.items():
            if isinstance(field_value, dict) and "key_id" in field_value:
                key_exists = self.kms.get_key(field_value["key_id"]) is not None
                result[field_name] = key_exists
        
        return result
    
    def get_chain(self) -> List[VCPEvent]:
        """Get the full event chain"""
        return self._event_chain.copy()
    
    def get_chain_summary(self) -> Dict[str, Any]:
        """Get a summary of the event chain"""
        return {
            "total_events": len(self._event_chain),
            "event_types": [e.header.event_type for e in self._event_chain],
            "first_event": self._event_chain[0].header.timestamp if self._event_chain else None,
            "last_event": self._event_chain[-1].header.timestamp if self._event_chain else None,
            "chain_head_hash": self._event_chain[-1].header.event_hash if self._event_chain else None
        }


def demo_crypto_shredding():
    """
    Demonstration of local key-store removal and hash-chain checks.
    """
    print("=" * 70)
    print("VCP v1.1 Crypto-Shredding Demo")
    print("Local key-store removal and hash-chain checks")
    print("=" * 70)
    print()
    
    # Initialize
    shredder = VCPCryptoShredder()
    
    # Subject ID (e.g., trader account)
    subject_id = "TRADER-DE-12345"
    
    print("Phase 1: RECORD - Creating trading events with encrypted PII")
    print("-" * 70)
    
    # Create some trading events
    events_data = [
        {
            "event_type": EventType.ORD,
            "payload": {
                "account_id": "ACC-12345-DE",
                "email": "trader@example.de",
                "ip_address": "192.168.1.100",
                "symbol": "EURUSD",
                "side": "BUY",
                "quantity": 100000,
                "price": 1.0850,
                "algorithm_id": "ALG-MOMENTUM-001"
            },
            "pii_fields": ["account_id", "email", "ip_address"]
        },
        {
            "event_type": EventType.ACK,
            "payload": {
                "account_id": "ACC-12345-DE",
                "order_id": "ORD-2025-001",
                "venue": "XEUR",
                "status": "ACCEPTED"
            },
            "pii_fields": ["account_id"]
        },
        {
            "event_type": EventType.EXE,
            "payload": {
                "account_id": "ACC-12345-DE",
                "order_id": "ORD-2025-001",
                "execution_id": "EXE-2025-001",
                "fill_price": 1.0851,
                "fill_quantity": 100000,
                "venue": "XEUR"
            },
            "pii_fields": ["account_id"]
        }
    ]
    
    for data in events_data:
        event = shredder.create_event(
            event_type=data["event_type"],
            payload=data["payload"],
            pii_fields=data["pii_fields"],
            subject_id=subject_id
        )
        print(f"  Created {event.header.event_type} event: {event.header.event_id[:20]}...")
        print(f"    Hash: {event.header.event_hash[:32]}...")
        print(f"    PII fields encrypted: {data['pii_fields']}")
    
    print()
    print("Phase 2: VERIFY - Chain integrity before erasure")
    print("-" * 70)
    
    verification = shredder.verify_chain_integrity()
    print(f"  Chain verified: {verification['verified']}")
    print(f"  Events checked: {verification['events_checked']}")
    
    # Check PII recoverability
    first_event = shredder.get_chain()[0]
    pii_status = shredder.can_recover_pii(first_event)
    print(f"  PII keys available in simulated store: {pii_status}")
    
    print()
    print("Phase 3: ERASE - GDPR Article 17 erasure request")
    print("-" * 70)
    print(f"  Subject {subject_id} requests data erasure...")
    
    certificate = shredder.execute_erasure(subject_id)
    
    print(f"  Keys removed from simulated store: {certificate.keys_destroyed}")
    print(f"  Erasure timestamp: {certificate.erasure_timestamp}")
    print(f"  Certificate ID: {certificate.certificate_id}")
    print(f"  Certificate hash: {certificate.certificate_hash[:32]}...")
    
    print()
    print("Phase 4: VERIFY POST-ERASURE - Chain still intact!")
    print("-" * 70)
    
    verification_post = shredder.verify_chain_integrity()
    print(f"  Chain verified: {verification_post['verified']}")
    print(f"  Events checked: {verification_post['events_checked']}")
    
    # Check PII recoverability after erasure
    pii_status_post = shredder.can_recover_pii(first_event)
    print(f"  PII keys available in simulated store: {pii_status_post}")
    
    print()
    print("=" * 70)
    print("RESULT: Local demo checks complete")
    print("=" * 70)
    print("""
  - Hash chain: inspect the verifier result above.
  - PII keys: inspect availability in the simulated store above.
  - Erasure report: unsigned, with preset verification flags.
  - Retained copies and memory zeroization are not assessed.
  - GDPR, MiFID II, EU AI Act and EDPB compliance is not determined.
    """)
    
    print("Unsigned local erasure report (not proof of secure destruction):")
    print("-" * 70)
    print(certificate.to_json())
    
    return shredder, certificate


if __name__ == "__main__":
    demo_crypto_shredding()
