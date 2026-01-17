#!/usr/bin/env python3
"""
VCP v1.1 Crypto-Shredding Test Suite
====================================

Comprehensive tests for the GDPR-MiFID II Paradox resolver.

Run with: pytest tests/test_crypto_shredding.py -v

(C) 2025 VeritasChain Standards Organization
Licensed under Apache 2.0
"""

import pytest
import sys
import os
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'python'))

from vcp_crypto_shredding import (
    VCPCryptoShredder,
    KeyManagementSystem,
    EventType,
    ClockSyncStatus,
    TimestampPrecision,
    VCPEvent,
    ErasureCertificate,
    PIIEncryptionResult
)


class TestKeyManagementSystem:
    """Tests for the Key Management System"""
    
    def test_generate_key(self):
        """Test key generation"""
        kms = KeyManagementSystem()
        key_id = kms.generate_key("SUBJECT-001")
        
        assert key_id is not None
        assert key_id.startswith("KEY-SUBJECT-001-")
        assert kms.get_key(key_id) is not None
    
    def test_destroy_key(self):
        """Test key destruction (crypto-shredding)"""
        kms = KeyManagementSystem()
        key_id = kms.generate_key("SUBJECT-001")
        
        # Key should exist
        assert kms.get_key(key_id) is not None
        
        # Destroy key
        result = kms.destroy_key(key_id)
        assert result is True
        
        # Key should no longer exist
        assert kms.get_key(key_id) is None
    
    def test_get_keys_for_subject(self):
        """Test retrieving keys for a specific subject"""
        kms = KeyManagementSystem()
        
        # Create keys for different subjects
        key1 = kms.generate_key("SUBJECT-001")
        key2 = kms.generate_key("SUBJECT-001")
        key3 = kms.generate_key("SUBJECT-002")
        
        # Get keys for subject 1
        keys = kms.get_keys_for_subject("SUBJECT-001")
        assert len(keys) == 2
        assert key1 in keys
        assert key2 in keys
        assert key3 not in keys
    
    def test_destruction_log(self):
        """Test that key destruction is logged"""
        kms = KeyManagementSystem()
        key_id = kms.generate_key("SUBJECT-001")
        kms.destroy_key(key_id)
        
        log = kms.get_destruction_log()
        assert len(log) == 1
        assert log[0]["key_id"] == key_id
        assert "destroyed_at" in log[0]


class TestVCPCryptoShredder:
    """Tests for the main crypto-shredding implementation"""
    
    @pytest.fixture
    def shredder(self):
        """Create a fresh shredder instance for each test"""
        return VCPCryptoShredder()
    
    def test_create_event_basic(self, shredder):
        """Test basic event creation"""
        event = shredder.create_event(
            event_type=EventType.ORD,
            payload={"symbol": "EURUSD", "price": 1.0850},
            pii_fields=[],
            subject_id="TRADER-001"
        )
        
        assert event is not None
        assert event.header.event_type == "ORD"
        assert event.header.event_hash is not None
        assert len(event.header.event_hash) == 64  # SHA-256 hex
    
    def test_create_event_with_pii_encryption(self, shredder):
        """Test event creation with PII encryption"""
        event = shredder.create_event(
            event_type=EventType.ORD,
            payload={
                "account_id": "ACC-12345",
                "email": "trader@example.com",
                "symbol": "EURUSD"
            },
            pii_fields=["account_id", "email"],
            subject_id="TRADER-001"
        )
        
        # PII fields should be encrypted
        assert isinstance(event.payload["account_id"], dict)
        assert "ciphertext" in event.payload["account_id"]
        assert "key_id" in event.payload["account_id"]
        
        # Non-PII fields should be plaintext
        assert event.payload["symbol"] == "EURUSD"
    
    def test_hash_chain_integrity(self, shredder):
        """Test hash chain creation"""
        # Create multiple events
        for i in range(5):
            shredder.create_event(
                event_type=EventType.ORD,
                payload={"order_num": i},
                pii_fields=[],
                subject_id="TRADER-001"
            )
        
        chain = shredder.get_chain()
        assert len(chain) == 5
        
        # Verify chain linkage
        for i in range(1, len(chain)):
            assert chain[i].header.prev_hash == chain[i-1].header.event_hash
    
    def test_verify_chain_integrity(self, shredder):
        """Test chain verification"""
        # Create events
        for i in range(3):
            shredder.create_event(
                event_type=EventType.ORD,
                payload={"order_num": i, "account_id": f"ACC-{i}"},
                pii_fields=["account_id"],
                subject_id="TRADER-001"
            )
        
        # Verify chain
        result = shredder.verify_chain_integrity()
        assert result["verified"] is True
        assert result["events_checked"] == 3
        assert len(result["errors"]) == 0
    
    def test_execute_erasure(self, shredder):
        """Test GDPR erasure via crypto-shredding"""
        # Create events
        shredder.create_event(
            event_type=EventType.ORD,
            payload={"account_id": "ACC-12345"},
            pii_fields=["account_id"],
            subject_id="TRADER-001"
        )
        
        # Execute erasure
        certificate = shredder.execute_erasure("TRADER-001")
        
        assert certificate is not None
        assert certificate.type == "VCP_ERASURE_CERTIFICATE"
        assert certificate.keys_destroyed > 0
        assert certificate.verification["hash_chain_intact"] is True
        assert certificate.verification["pii_recoverable"] is False
    
    def test_chain_integrity_after_erasure(self, shredder):
        """Test that chain integrity is preserved after erasure"""
        # Create events
        for i in range(5):
            shredder.create_event(
                event_type=EventType.ORD,
                payload={"account_id": f"ACC-{i}"},
                pii_fields=["account_id"],
                subject_id="TRADER-001"
            )
        
        # Verify before erasure
        before = shredder.verify_chain_integrity()
        assert before["verified"] is True
        
        # Execute erasure
        shredder.execute_erasure("TRADER-001")
        
        # Verify after erasure - chain should still be intact!
        after = shredder.verify_chain_integrity()
        assert after["verified"] is True
        assert after["events_checked"] == 6  # 5 original + 1 erasure event
    
    def test_pii_unrecoverable_after_erasure(self, shredder):
        """Test that PII cannot be recovered after erasure"""
        # Create event with PII
        event = shredder.create_event(
            event_type=EventType.ORD,
            payload={"account_id": "ACC-SECRET-12345"},
            pii_fields=["account_id"],
            subject_id="TRADER-001"
        )
        
        # Check PII is recoverable before erasure
        pii_status_before = shredder.can_recover_pii(event)
        assert pii_status_before.get("account_id", False) is True
        
        # Execute erasure
        shredder.execute_erasure("TRADER-001")
        
        # Check PII is NOT recoverable after erasure
        pii_status_after = shredder.can_recover_pii(event)
        assert pii_status_after.get("account_id", True) is False
    
    def test_decrypt_pii_before_erasure(self, shredder):
        """Test PII decryption works before erasure"""
        original_value = "SECRET-ACCOUNT-12345"
        
        event = shredder.create_event(
            event_type=EventType.ORD,
            payload={"account_id": original_value},
            pii_fields=["account_id"],
            subject_id="TRADER-001"
        )
        
        # Get encrypted result
        encrypted = PIIEncryptionResult(**event.payload["account_id"])
        
        # Decrypt
        decrypted = shredder.decrypt_pii(encrypted)
        assert decrypted == original_value
    
    def test_decrypt_pii_returns_none_after_erasure(self, shredder):
        """Test PII decryption returns None after erasure"""
        event = shredder.create_event(
            event_type=EventType.ORD,
            payload={"account_id": "SECRET-VALUE"},
            pii_fields=["account_id"],
            subject_id="TRADER-001"
        )
        
        encrypted = PIIEncryptionResult(**event.payload["account_id"])
        
        # Erasure
        shredder.execute_erasure("TRADER-001")
        
        # Attempt decryption - should return None
        decrypted = shredder.decrypt_pii(encrypted)
        assert decrypted is None


class TestErasureCertificate:
    """Tests for erasure certificate generation"""
    
    def test_certificate_structure(self):
        """Test certificate has required fields"""
        shredder = VCPCryptoShredder()
        
        shredder.create_event(
            event_type=EventType.ORD,
            payload={"account_id": "ACC-123"},
            pii_fields=["account_id"],
            subject_id="TRADER-001"
        )
        
        cert = shredder.execute_erasure("TRADER-001")
        
        # Required fields
        assert cert.certificate_id is not None
        assert cert.type == "VCP_ERASURE_CERTIFICATE"
        assert cert.version == "1.0"
        assert cert.subject_id_hash is not None
        assert cert.erasure_timestamp is not None
        assert cert.method == "CRYPTOGRAPHIC_KEY_DESTRUCTION"
        assert cert.certificate_hash is not None
        
        # Compliance references
        assert "GDPR Article 17(1)" in cert.compliance_references
        assert "EDPB Guidelines 02/2025" in cert.compliance_references
    
    def test_certificate_serialization(self):
        """Test certificate can be serialized to JSON"""
        shredder = VCPCryptoShredder()
        
        shredder.create_event(
            event_type=EventType.ORD,
            payload={"account_id": "ACC-123"},
            pii_fields=["account_id"],
            subject_id="TRADER-001"
        )
        
        cert = shredder.execute_erasure("TRADER-001")
        json_str = cert.to_json()
        
        # Should be valid JSON
        parsed = json.loads(json_str)
        assert parsed["type"] == "VCP_ERASURE_CERTIFICATE"


class TestGDPRMiFIDParadox:
    """Integration tests for the GDPR-MiFID II Paradox resolution"""
    
    def test_full_paradox_resolution_scenario(self):
        """
        Complete scenario testing the paradox resolution:
        1. Create trading events with PII
        2. Verify chain integrity
        3. Execute GDPR erasure
        4. Verify chain is still intact
        5. Verify PII is unrecoverable
        """
        shredder = VCPCryptoShredder()
        
        # Phase 1: Record trading activity
        events = []
        for i in range(3):
            event = shredder.create_event(
                event_type=EventType.ORD if i == 0 else EventType.EXE,
                payload={
                    "account_id": "ACC-DE-12345",
                    "email": "trader@example.de",
                    "symbol": "EURUSD",
                    "quantity": 100000 + i * 10000
                },
                pii_fields=["account_id", "email"],
                subject_id="TRADER-DE-12345"
            )
            events.append(event)
        
        # Phase 2: Verify chain before erasure
        verification_before = shredder.verify_chain_integrity()
        assert verification_before["verified"] is True
        
        # Phase 3: Check PII is accessible
        for event in events:
            pii_status = shredder.can_recover_pii(event)
            assert pii_status["account_id"] is True
            assert pii_status["email"] is True
        
        # Phase 4: Execute GDPR erasure (5 years later simulation)
        certificate = shredder.execute_erasure("TRADER-DE-12345")
        
        # Phase 5: Verify chain STILL intact (MiFID II compliance)
        verification_after = shredder.verify_chain_integrity()
        assert verification_after["verified"] is True
        
        # Phase 6: Verify PII is unrecoverable (GDPR compliance)
        for event in events:
            pii_status = shredder.can_recover_pii(event)
            assert pii_status["account_id"] is False
            assert pii_status["email"] is False
        
        # Phase 7: Verify certificate is valid evidence
        assert certificate.verification["hash_chain_intact"] is True
        assert certificate.verification["pii_recoverable"] is False
        assert certificate.verification["audit_trail_preserved"] is True
        
        print("\n" + "=" * 60)
        print("GDPR-MiFID II PARADOX RESOLUTION TEST: PASSED")
        print("=" * 60)
        print(f"  Chain integrity: PRESERVED ({verification_after['events_checked']} events)")
        print(f"  PII data: CRYPTO-SHREDDED ({certificate.keys_destroyed} keys destroyed)")
        print(f"  Audit trail: INTACT")
        print(f"  Certificate: GENERATED ({certificate.certificate_id[:20]}...)")
        print("=" * 60)


class TestEventTypes:
    """Test different event types"""
    
    @pytest.fixture
    def shredder(self):
        return VCPCryptoShredder()
    
    @pytest.mark.parametrize("event_type", [
        EventType.SIG,
        EventType.ORD,
        EventType.ACK,
        EventType.EXE,
        EventType.REJ,
        EventType.CXL,
        EventType.GOV,
    ])
    def test_all_event_types(self, shredder, event_type):
        """Test all event types can be created"""
        event = shredder.create_event(
            event_type=event_type,
            payload={"test": "data"},
            pii_fields=[],
            subject_id="TRADER-001"
        )
        
        assert event.header.event_type == event_type.value


class TestClockSyncStatus:
    """Test clock synchronization status handling"""
    
    @pytest.mark.parametrize("sync_status", [
        ClockSyncStatus.NTP_SYNCED,
        ClockSyncStatus.PTP_LOCKED,
        ClockSyncStatus.GPS_SYNCED,
        ClockSyncStatus.UNSYNCHRONIZED,
    ])
    def test_clock_sync_statuses(self, sync_status):
        """Test all clock sync statuses"""
        shredder = VCPCryptoShredder()
        
        event = shredder.create_event(
            event_type=EventType.ORD,
            payload={"test": "data"},
            pii_fields=[],
            subject_id="TRADER-001",
            clock_sync_status=sync_status
        )
        
        assert event.header.clock_sync_status == sync_status.value


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
