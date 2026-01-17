#!/usr/bin/env python3
"""
VCP v1.1 CI Demo (Non-Interactive)
==================================

Runs the full GDPR-MiFID II Paradox resolution demo without user input.
Suitable for CI/CD pipelines.

Usage:
    python demo_ci.py

Exit codes:
    0 = Success (paradox resolved)
    1 = Failure

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


def main() -> int:
    """Run the demo and return exit code"""
    
    print("VCP v1.1 Crypto-Shredding CI Demo")
    print("=" * 50)
    
    try:
        # Initialize
        shredder = VCPCryptoShredder()
        subject_id = "TRADER-DE-12345"
        
        # PHASE 1: Create events
        print("\n[PHASE 1] Creating events with encrypted PII...")
        
        order_event = shredder.create_event(
            event_type=EventType.ORD,
            payload={
                "account_id": "ACC-12345-DE",
                "email": "trader@beispiel.de",
                "symbol": "EURUSD",
                "quantity": 100000,
                "price": 1.0850
            },
            pii_fields=["account_id", "email"],
            subject_id=subject_id,
            clock_sync_status=ClockSyncStatus.NTP_SYNCED
        )
        print(f"  ✓ ORD event: {order_event.header.event_id[:30]}...")
        
        ack_event = shredder.create_event(
            event_type=EventType.ACK,
            payload={"account_id": "ACC-12345-DE", "status": "ACCEPTED"},
            pii_fields=["account_id"],
            subject_id=subject_id
        )
        print(f"  ✓ ACK event: {ack_event.header.event_id[:30]}...")
        
        exe_event = shredder.create_event(
            event_type=EventType.EXE,
            payload={"account_id": "ACC-12345-DE", "fill_price": 1.0851},
            pii_fields=["account_id"],
            subject_id=subject_id
        )
        print(f"  ✓ EXE event: {exe_event.header.event_id[:30]}...")
        
        # PHASE 2: Verify chain before erasure
        print("\n[PHASE 2] Verifying chain integrity...")
        
        result_before = shredder.verify_chain_integrity()
        if not result_before["verified"]:
            print("  ✗ Chain verification FAILED!")
            return 1
        print(f"  ✓ Chain verified: {result_before['events_checked']} events")
        
        # Check PII is recoverable
        pii_before = shredder.can_recover_pii(order_event)
        if not all(pii_before.values()):
            print("  ✗ PII should be recoverable before erasure!")
            return 1
        print("  ✓ PII recoverable: " + ", ".join(pii_before.keys()))
        
        # PHASE 3: Execute erasure
        print("\n[PHASE 3] Executing GDPR erasure...")
        
        certificate = shredder.execute_erasure(subject_id)
        print(f"  ✓ Keys destroyed: {certificate.keys_destroyed}")
        print(f"  ✓ Certificate: {certificate.certificate_id[:30]}...")
        
        # PHASE 4: Verify post-erasure
        print("\n[PHASE 4] Verifying post-erasure state...")
        
        # Chain should still be intact
        result_after = shredder.verify_chain_integrity()
        if not result_after["verified"]:
            print("  ✗ Chain verification FAILED after erasure!")
            return 1
        print(f"  ✓ Chain still verified: {result_after['events_checked']} events")
        
        # PII should NOT be recoverable
        pii_after = shredder.can_recover_pii(order_event)
        if any(pii_after.values()):
            print("  ✗ PII should NOT be recoverable after erasure!")
            return 1
        print("  ✓ PII unrecoverable (crypto-shredded)")
        
        # Certificate verification fields
        if not certificate.verification["hash_chain_intact"]:
            print("  ✗ Certificate claims chain is broken!")
            return 1
        if certificate.verification["pii_recoverable"]:
            print("  ✗ Certificate claims PII is recoverable!")
            return 1
        if not certificate.verification["audit_trail_preserved"]:
            print("  ✗ Certificate claims audit trail is lost!")
            return 1
        print("  ✓ Certificate verification fields correct")
        
        # SUCCESS
        print("\n" + "=" * 50)
        print("RESULT: PARADOX RESOLVED!")
        print("=" * 50)
        print("  ✓ GDPR Article 17: Satisfied (PII unrecoverable)")
        print("  ✓ MiFID II Article 16(7): Satisfied (chain intact)")
        print("  ✓ EU AI Act Article 12: Satisfied (logs preserved)")
        print("  ✓ EDPB 02/2025: Compliant architecture")
        print()
        
        return 0
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
