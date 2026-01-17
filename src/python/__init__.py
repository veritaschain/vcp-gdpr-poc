"""
VCP v1.1 Crypto-Shredding Module
================================

Solves the GDPR-MiFID II Paradox through cryptographic key management.

Example:
    from vcp_crypto_shredding import VCPCryptoShredder, EventType
    
    shredder = VCPCryptoShredder()
    event = shredder.create_event(
        event_type=EventType.ORD,
        payload={"account_id": "ACC-123"},
        pii_fields=["account_id"],
        subject_id="TRADER-001"
    )
    certificate = shredder.execute_erasure("TRADER-001")

(C) 2025 VeritasChain Standards Organization
Licensed under Apache 2.0
"""

from .vcp_crypto_shredding import (
    VCPCryptoShredder,
    KeyManagementSystem,
    EventType,
    ClockSyncStatus,
    TimestampPrecision,
    VCPEvent,
    VCPEventHeader,
    ErasureCertificate,
    PIIEncryptionResult,
)

__version__ = "1.1.0"
__author__ = "VeritasChain Standards Organization"
__all__ = [
    "VCPCryptoShredder",
    "KeyManagementSystem",
    "EventType",
    "ClockSyncStatus",
    "TimestampPrecision",
    "VCPEvent",
    "VCPEventHeader",
    "ErasureCertificate",
    "PIIEncryptionResult",
]
