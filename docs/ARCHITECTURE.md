# VCP v1.1 Crypto-Shredding Architecture

## Overview

This document describes the technical architecture of the VCP v1.1 Crypto-Shredding implementation, which resolves the GDPR-MiFID II regulatory paradox through cryptographic key management.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Trading Platform Layer                            │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │   MT5 EA    │  │   cTrader   │  │  FIX Engine │  │  Custom API │   │
│  │             │  │   cBot      │  │             │  │             │   │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘   │
│         │                │                │                │           │
│         └────────────────┴────────────────┴────────────────┘           │
│                                   │                                      │
│                          VCP MQL5 Bridge                                 │
│                      (vcp_gdpr_bridge.mqh)                              │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                            HTTP/JSON POST
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         VCP Sidecar Layer                                │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                   VCP Sidecar Adapter                            │   │
│  │                 (vcp_sidecar_adapter.py)                         │   │
│  │                                                                   │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │   │
│  │  │ HTTP Server │  │ Event Queue │  │ Chain Manager           │  │   │
│  │  │ :8765       │  │             │  │ (hash chain maintenance)│  │   │
│  │  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────────┘  │   │
│  │         │                │                    │                  │   │
│  └─────────┴────────────────┴────────────────────┴──────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      VCP Core Processing Layer                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                   VCPCryptoShredder                               │   │
│  │                (vcp_crypto_shredding.py)                          │   │
│  │                                                                   │   │
│  │   ┌─────────────────┐    ┌─────────────────┐                     │   │
│  │   │  Event Creator  │    │  Chain Verifier │                     │   │
│  │   │  - UUIDv7 gen   │    │  - Hash verify  │                     │   │
│  │   │  - Timestamp    │    │  - Merkle proof │                     │   │
│  │   │  - Hash chain   │    │                 │                     │   │
│  │   └────────┬────────┘    └────────┬────────┘                     │   │
│  │            │                      │                               │   │
│  │            └──────────────────────┘                               │   │
│  │                        │                                          │   │
│  └────────────────────────┼──────────────────────────────────────────┘   │
│                           │                                              │
│                           ▼                                              │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                 Key Management System (KMS)                       │   │
│  │                                                                   │   │
│  │   ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │   │
│  │   │ Key Store   │  │ Key Destroy │  │ Destruction Log         │  │   │
│  │   │ (per-subj)  │  │ (crypto-    │  │ (audit trail)           │  │   │
│  │   │             │  │  shredding) │  │                         │  │   │
│  │   └─────────────┘  └─────────────┘  └─────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│              Production: Replace with HSM integration                    │
│              (AWS CloudHSM, Azure Key Vault, Thales Luna)               │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         Storage Layer                                    │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────┐  │
│  │  Event Chain    │  │  Erasure Certs  │  │  Merkle Roots           │  │
│  │  (encrypted)    │  │  (immutable)    │  │  (external anchor)      │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. VCP MQL5 Bridge (`vcp_gdpr_bridge.mqh`)

The bridge component runs inside MetaTrader 5 and:

- Captures trading events (orders, executions, cancellations)
- Marks PII fields for encryption (`ENC:AES256:` prefix)
- Serializes events to JSON
- Sends events to the Sidecar via HTTP POST

**Key Classes:**
- `CVCPGDPRBridge` - Main bridge class
- `VCPTradeEvent` - Event structure with GDPR metadata
- `VCPErasureCertificate` - Erasure proof structure

### 2. VCP Sidecar Adapter (`vcp_sidecar_adapter.py`)

HTTP server that:

- Receives events from trading platforms
- Routes events to the crypto-shredder
- Handles GDPR erasure requests
- Provides verification endpoints

**Endpoints:**
| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/stats` | Server statistics |
| GET | `/chain` | View event chain |
| GET | `/verify` | Verify chain integrity |
| POST | `/vcp/event` | Submit new event |
| POST | `/vcp/erasure` | Execute GDPR erasure |

### 3. VCPCryptoShredder (`vcp_crypto_shredding.py`)

Core implementation that:

- Creates VCP-compliant events
- Encrypts PII fields with per-subject keys
- Maintains hash chain integrity
- Executes crypto-shredding on erasure
- Generates erasure certificates

**Key Methods:**
```python
create_event(event_type, payload, pii_fields, subject_id)
execute_erasure(subject_id) -> ErasureCertificate
verify_chain_integrity() -> Dict
can_recover_pii(event) -> Dict[str, bool]
```

### 4. Key Management System (KMS)

Manages encryption keys:

- Generates AES-256 keys per data subject
- Stores keys securely (HSM in production)
- Destroys keys on erasure request
- Maintains destruction audit log

**Security Model:**
- Each data subject has their own encryption key
- Keys are never exposed outside KMS
- Destruction is irreversible
- All operations are logged

## Data Flow

### Event Creation Flow

```
1. Trading EA generates signal/order
         │
         ▼
2. VCP Bridge creates event structure
   - Mark PII fields for encryption
   - Add GDPR metadata
         │
         ▼
3. Send to Sidecar (HTTP POST)
         │
         ▼
4. Sidecar routes to CryptoShredder
         │
         ▼
5. CryptoShredder:
   a. Get/create key for subject
   b. Encrypt PII fields (AES-256-GCM)
   c. Calculate hash (prev_hash + encrypted_payload)
   d. Add to chain
         │
         ▼
6. Event stored with:
   - Encrypted PII
   - Hash chain linkage
   - GDPR metadata
```

### GDPR Erasure Flow

```
1. Data subject requests erasure
         │
         ▼
2. DPO initiates erasure via API
   POST /vcp/erasure { "subject_id": "..." }
         │
         ▼
3. CryptoShredder:
   a. Find all keys for subject
   b. Securely destroy keys (overwrite + delete)
   c. Create ERA event in chain
   d. Generate erasure certificate
         │
         ▼
4. Post-erasure state:
   - Hash chain: INTACT ✓
   - PII data: UNRECOVERABLE ✓
   - Audit trail: PRESERVED ✓
         │
         ▼
5. Return certificate to DPO
   (for regulatory evidence)
```

## Cryptographic Specifications

### Encryption

| Component | Algorithm | Standard |
|-----------|-----------|----------|
| PII Encryption | AES-256-GCM | NIST SP 800-38D |
| Event Hashing | SHA-256 | FIPS 180-4 |
| Key Derivation | HKDF-SHA256 | RFC 5869 |
| UUID Generation | UUIDv7 | RFC 9562 |

### Event Hash Chain

```
Hash[n] = SHA256(Hash[n-1] || Payload[n])

Where:
- Hash[0] = "0" × 64 (genesis)
- Payload = JSON.stringify(encrypted_payload, sort_keys=True)
```

### Key Destruction

1. **Overwrite**: Replace key bytes with random data
2. **Delete**: Remove from key store
3. **Log**: Record destruction in audit trail
4. **Certificate**: Generate cryptographic proof

## Security Considerations

### Threat Model

| Threat | Mitigation |
|--------|------------|
| Key extraction | HSM storage in production |
| Unauthorized erasure | Role-based access control |
| Chain tampering | Hash chain verification |
| Log manipulation | External anchoring (optional) |

### Production Recommendations

1. **HSM Integration**: Replace simulated KMS with hardware HSM
2. **Access Control**: Implement RBAC for erasure operations
3. **Audit Logging**: External, immutable audit log
4. **External Anchoring**: Periodic Merkle root publication
5. **Key Rotation**: Regular key rotation policy

## Compliance Mapping

| Requirement | Implementation |
|-------------|----------------|
| GDPR Art. 17 | Crypto-shredding via key destruction |
| MiFID II Art. 16(7) | Hash chain preserved post-erasure |
| MiFID II RTS 25 | Microsecond timestamps, clock sync status |
| EU AI Act Art. 12 | Automatic event capture |
| EDPB 02/2025 | Cryptographic erasure architecture |

---

© 2025 VeritasChain Standards Organization
