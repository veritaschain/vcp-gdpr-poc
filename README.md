# VCP v1.1 Crypto-Shredding PoC

## "The Erasable Immutable Log" — Solving the GDPR-MiFID II Paradox

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![VCP Version](https://img.shields.io/badge/VCP-v1.1-green.svg)](https://github.com/veritaschain/vcp-spec)
[![IETF Draft](https://img.shields.io/badge/IETF-draft--kamimura--scitt--vcp-orange.svg)](https://datatracker.ietf.org/doc/draft-kamimura-scitt-vcp/)

---

## 🎯 The Problem: A Regulatory Paradox

European algorithmic trading firms face an impossible choice:

| Regulation | Requirement | Implication |
|------------|-------------|-------------|
| **GDPR Article 17** | "Right to Erasure" | Must delete personal data on request |
| **MiFID II Article 16(7)** | 5-7 Year Retention | Must preserve all trading records |

**The Paradox:** How do you prove data was deleted while proving it was never altered?

---

## ✅ The Solution: Crypto-Shredding

VCP v1.1 resolves this paradox through **cryptographic key destruction**:

```
┌─────────────────────────────────────────────────────────────┐
│           Before Erasure        │     After Erasure         │
├─────────────────────────────────────────────────────────────┤
│  Event₁ ──hash──▶ Event₂        │  Event₁ ──hash──▶ Event₂  │
│  [Encrypted PII]                │  [Encrypted PII]          │
│  KEY exists in HSM              │  KEY destroyed            │
│  PII: ✓ Recoverable             │  PII: ✗ Unrecoverable     │
│  Hash chain: ✓ Valid            │  Hash chain: ✓ Valid!     │
└─────────────────────────────────────────────────────────────┘
```

**The Result:**
- ✓ **MiFID II**: Hash chain preserved, audit trail intact
- ✓ **GDPR**: Personal data cryptographically unrecoverable
- ✓ **EDPB Guidelines 02/2025**: Compliant architecture

---

## 📁 Repository Structure

```
vcp-gdpr-poc/
├── src/
│   ├── python/
│   │   ├── vcp_crypto_shredding.py   # Core implementation
│   │   └── vcp_sidecar_adapter.py    # HTTP server for MT5/cTrader
│   ├── mql5/
│   │   └── vcp_gdpr_bridge.mqh       # MT5 integration
│   └── demo/
│       └── index.html                 # Interactive web demo
├── tests/
│   └── test_crypto_shredding.py      # Comprehensive test suite
├── docs/
│   ├── ARCHITECTURE.md               # Technical architecture
│   └── REGULATORY_MAPPING.md         # EU regulation alignment
├── examples/
│   └── sample_events.json            # Example VCP events
├── requirements.txt
├── LICENSE
└── README.md
```

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the Demo

**Python CLI Demo:**
```bash
python src/python/vcp_crypto_shredding.py
```

**Web Demo:**
```bash
# Open in browser
open src/demo/index.html
```

**Sidecar Server (for MT5 integration):**
```bash
python src/python/vcp_sidecar_adapter.py --port 8765
```

### 3. Run Tests

```bash
pytest tests/ -v
```

---

## 📊 Interactive Demo

Open `src/demo/index.html` in your browser to experience:

1. **Phase 1: RECORD** — Create trading events with encrypted PII
2. **Phase 2: RETAIN** — Verify hash chain integrity
3. **Phase 3: ERASE** — Execute GDPR crypto-shredding
4. **Phase 4: VERIFY** — Confirm paradox resolution

![Demo Screenshot](docs/demo-screenshot.png)

---

## 🔧 Integration Guide

### Python Integration

```python
from vcp_crypto_shredding import VCPCryptoShredder, EventType

# Initialize
shredder = VCPCryptoShredder()

# Create event with encrypted PII
event = shredder.create_event(
    event_type=EventType.ORD,
    payload={
        "account_id": "ACC-12345-DE",
        "email": "trader@example.de",
        "symbol": "EURUSD",
        "quantity": 100000
    },
    pii_fields=["account_id", "email"],
    subject_id="TRADER-DE-12345"
)

# Later: Execute GDPR erasure
certificate = shredder.execute_erasure("TRADER-DE-12345")

# Verify chain is still intact
result = shredder.verify_chain_integrity()
assert result["verified"] == True  # ✓ MiFID II compliant

# Verify PII is unrecoverable
pii_status = shredder.can_recover_pii(event)
assert pii_status["account_id"] == False  # ✓ GDPR compliant
```

### MT5 (MQL5) Integration

```mql5
#include <VCP/vcp_gdpr_bridge.mqh>

CVCPGDPRBridge bridge;

int OnInit()
{
   bridge.Init("MY-EA-001", "1.0.0", "http://localhost:8765/vcp/event");
   return INIT_SUCCEEDED;
}

void OnTick()
{
   VCPTradeEvent event;
   
   if(bridge.CreateOrderEvent(event, Symbol(), ORDER_TYPE_BUY, 1.0, Ask))
   {
      bridge.SendToSidecar(event);
   }
}
```

---

## 📋 Regulatory Compliance

### Covered Regulations

| Regulation | Article | Requirement | VCP Solution |
|------------|---------|-------------|--------------|
| **GDPR** | Art. 17 | Right to Erasure | Crypto-shredding |
| **MiFID II** | Art. 16(7) | 5-7 Year Retention | Hash chain preservation |
| **MiFID II** | RTS 25 | Clock Sync | TimestampPrecision, ClockSyncStatus |
| **EU AI Act** | Art. 12 | Automatic Logging | VCP-CORE event capture |
| **EDPB** | Guidelines 02/2025 | Blockchain & GDPR | Architecture alignment |

### Erasure Certificate

Upon GDPR erasure request, VCP generates a cryptographic certificate:

```json
{
  "type": "VCP_ERASURE_CERTIFICATE",
  "version": "1.0",
  "subject_id_hash": "a1b2c3d4e5...",
  "erasure_timestamp": "2025-01-17T10:30:00Z",
  "keys_destroyed": 3,
  "method": "CRYPTOGRAPHIC_KEY_DESTRUCTION",
  "compliance_references": [
    "GDPR Article 17(1)",
    "EDPB Guidelines 02/2025",
    "VCP-PRIVACY v1.1"
  ],
  "verification": {
    "hash_chain_intact": true,
    "pii_recoverable": false,
    "audit_trail_preserved": true
  },
  "certificate_hash": "f6e5d4c3b2a1..."
}
```

---

## 🔐 Security Considerations

### Key Management

- **Production**: Use HSM (AWS CloudHSM, Azure Key Vault, Thales Luna)
- **Key Rotation**: Supported via per-event key generation
- **Destruction Verification**: Logged in immutable audit trail

### Cryptographic Primitives

| Component | Algorithm | Standard |
|-----------|-----------|----------|
| Encryption | AES-256-GCM | NIST SP 800-38D |
| Hashing | SHA-256 | FIPS 180-4 |
| Signatures | Ed25519 | RFC 8032 |
| Key Derivation | HKDF | RFC 5869 |

---

## 📚 Documentation

- [VCP Specification v1.1](https://github.com/veritaschain/vcp-spec/tree/main/spec/v1.1)
- [IETF Draft](https://datatracker.ietf.org/doc/draft-kamimura-scitt-vcp/)
- [EU Regulatory Mapping](docs/REGULATORY_MAPPING.md)
- [Architecture Guide](docs/ARCHITECTURE.md)

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
git clone https://github.com/veritaschain/vcp-gdpr-poc.git
cd vcp-gdpr-poc
pip install -r requirements.txt
pip install -r requirements-dev.txt
pytest tests/ -v
```

---

## 📜 License

Apache License 2.0 — See [LICENSE](LICENSE) for details.

---

## 📞 Contact

**VeritasChain Standards Organization (VSO)**

- Website: [veritaschain.org](https://veritaschain.org)
- GitHub: [github.com/veritaschain](https://github.com/veritaschain)
- Email: technical@veritaschain.org
- IETF: [draft-kamimura-scitt-vcp](https://datatracker.ietf.org/doc/draft-kamimura-scitt-vcp/)

---

<p align="center">
  <strong>"Verify, Don't Trust"</strong><br>
  <em>AI needs a Flight Recorder</em>
</p>
