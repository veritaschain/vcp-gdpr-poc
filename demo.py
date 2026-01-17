#!/usr/bin/env python3
"""
VCP v1.1 Quick Demo
===================

Run this script to see the GDPR-MiFID II Paradox resolution in action.

Usage:
    python demo.py

(C) 2025 VeritasChain Standards Organization
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'python'))

from vcp_crypto_shredding import (
    VCPCryptoShredder,
    EventType,
    ClockSyncStatus
)


def main():
    """Run the interactive demo"""
    
    print()
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║           VCP v1.1 Crypto-Shredding Quick Demo                   ║")
    print("║           'The Erasable Immutable Log'                           ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    print()
    
    # Initialize
    shredder = VCPCryptoShredder()
    subject_id = "TRADER-DE-12345"
    
    print("┌──────────────────────────────────────────────────────────────────┐")
    print("│  Scenario: German trader uses algorithmic trading system        │")
    print("│  Subject ID: TRADER-DE-12345                                    │")
    print("└──────────────────────────────────────────────────────────────────┘")
    print()
    
    input("Press Enter to create trading events...")
    print()
    
    # ═══════════════════════════════════════════════════════════════════════
    # PHASE 1: CREATE EVENTS
    # ═══════════════════════════════════════════════════════════════════════
    print("━" * 70)
    print("  PHASE 1: RECORD - Creating events with encrypted PII")
    print("━" * 70)
    
    # Order event
    order_event = shredder.create_event(
        event_type=EventType.ORD,
        payload={
            "account_id": "ACC-12345-DE",
            "email": "trader@beispiel.de",
            "ip_address": "192.168.1.100",
            "symbol": "EURUSD",
            "side": "BUY",
            "quantity": 100000,
            "price": 1.0850,
            "algorithm_id": "ALG-MOMENTUM-001",
            "decision_factors": "RSI_OVERSOLD,MACD_BULLISH"
        },
        pii_fields=["account_id", "email", "ip_address"],
        subject_id=subject_id,
        clock_sync_status=ClockSyncStatus.NTP_SYNCED
    )
    print(f"  ✓ Created ORD event")
    print(f"    ID: {order_event.header.event_id}")
    print(f"    Hash: {order_event.header.event_hash[:40]}...")
    print(f"    PII encrypted: account_id, email, ip_address")
    print()
    
    # ACK event
    ack_event = shredder.create_event(
        event_type=EventType.ACK,
        payload={
            "account_id": "ACC-12345-DE",
            "order_id": "ORD-XEUR-2025-001",
            "venue": "XEUR",
            "status": "ACCEPTED"
        },
        pii_fields=["account_id"],
        subject_id=subject_id
    )
    print(f"  ✓ Created ACK event")
    print(f"    ID: {ack_event.header.event_id}")
    print()
    
    # EXE event
    exe_event = shredder.create_event(
        event_type=EventType.EXE,
        payload={
            "account_id": "ACC-12345-DE",
            "order_id": "ORD-XEUR-2025-001",
            "execution_id": "EXE-XEUR-2025-001-001",
            "fill_price": 1.0851,
            "fill_quantity": 100000
        },
        pii_fields=["account_id"],
        subject_id=subject_id
    )
    print(f"  ✓ Created EXE event")
    print(f"    ID: {exe_event.header.event_id}")
    print(f"    Fill: 100,000 @ 1.0851")
    print()
    
    input("Press Enter to verify chain integrity...")
    print()
    
    # ═══════════════════════════════════════════════════════════════════════
    # PHASE 2: VERIFY CHAIN
    # ═══════════════════════════════════════════════════════════════════════
    print("━" * 70)
    print("  PHASE 2: RETAIN - Verify hash chain integrity")
    print("━" * 70)
    
    result = shredder.verify_chain_integrity()
    print(f"  Chain Verified: {'✓ YES' if result['verified'] else '✗ NO'}")
    print(f"  Events Checked: {result['events_checked']}")
    print()
    
    # Check PII status
    pii_status = shredder.can_recover_pii(order_event)
    print("  PII Recovery Status (before erasure):")
    for field, recoverable in pii_status.items():
        status = "🔓 Recoverable" if recoverable else "🔒 Not recoverable"
        print(f"    {field}: {status}")
    print()
    
    input("Press Enter to execute GDPR erasure...")
    print()
    
    # ═══════════════════════════════════════════════════════════════════════
    # PHASE 3: GDPR ERASURE
    # ═══════════════════════════════════════════════════════════════════════
    print("━" * 70)
    print("  PHASE 3: ERASE - GDPR Article 17 erasure request")
    print("━" * 70)
    print()
    print("  📩 Data subject TRADER-DE-12345 exercises 'Right to Erasure'")
    print()
    
    certificate = shredder.execute_erasure(subject_id)
    
    print(f"  🗑️  CRYPTO-SHREDDING EXECUTED")
    print(f"     Keys destroyed: {certificate.keys_destroyed}")
    print(f"     Method: {certificate.method}")
    print()
    print(f"  📜 ERASURE CERTIFICATE GENERATED")
    print(f"     Certificate ID: {certificate.certificate_id}")
    print(f"     Timestamp: {certificate.erasure_timestamp}")
    print()
    
    input("Press Enter to verify paradox resolution...")
    print()
    
    # ═══════════════════════════════════════════════════════════════════════
    # PHASE 4: VERIFY POST-ERASURE
    # ═══════════════════════════════════════════════════════════════════════
    print("━" * 70)
    print("  PHASE 4: VERIFY - Post-erasure state")
    print("━" * 70)
    
    # Verify chain again
    result_after = shredder.verify_chain_integrity()
    print(f"  Hash Chain Verified: {'✓ YES' if result_after['verified'] else '✗ NO'}")
    print(f"  Events in Chain: {result_after['events_checked']}")
    print()
    
    # Check PII status after erasure
    pii_status_after = shredder.can_recover_pii(order_event)
    print("  PII Recovery Status (after erasure):")
    for field, recoverable in pii_status_after.items():
        status = "🔓 Recoverable" if recoverable else "🔒 SHREDDED"
        print(f"    {field}: {status}")
    print()
    
    # ═══════════════════════════════════════════════════════════════════════
    # RESULT
    # ═══════════════════════════════════════════════════════════════════════
    print()
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║                   🎉 PARADOX RESOLVED! 🎉                        ║")
    print("╠══════════════════════════════════════════════════════════════════╣")
    print("║                                                                  ║")
    print("║  ✓ GDPR Article 17: PII cryptographically unrecoverable         ║")
    print("║  ✓ MiFID II Article 16(7): Hash chain intact, audit preserved   ║")
    print("║  ✓ EDPB 02/2025: Compliant architecture                         ║")
    print("║  ✓ EU AI Act Article 12: Decision trail preserved               ║")
    print("║                                                                  ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    print()
    print("  Erasure Certificate (for DPO/regulator evidence):")
    print("  " + "─" * 66)
    print(certificate.to_json())
    print()
    print("  Learn more: https://veritaschain.org")
    print("  GitHub: https://github.com/veritaschain/vcp-spec")
    print()


if __name__ == "__main__":
    main()
