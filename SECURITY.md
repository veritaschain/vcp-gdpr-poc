# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.1.x   | :white_check_mark: |
| 1.0.x   | :x:                |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

### Contact

Email: security@veritaschain.org

### What to Include

1. **Description** of the vulnerability
2. **Steps to reproduce**
3. **Potential impact**
4. **Suggested fix** (if any)

### Response Timeline

- **Acknowledgment**: Within 48 hours
- **Initial assessment**: Within 7 days
- **Resolution**: Depends on severity

### Severity Classification

| Severity | Description | Response Time |
|----------|-------------|---------------|
| Critical | Key compromise, chain manipulation | 24 hours |
| High | PII exposure, auth bypass | 72 hours |
| Medium | DoS, information disclosure | 2 weeks |
| Low | Minor issues | Next release |

## Security Best Practices

### For Production Deployments

1. **Use HSM for key storage**
   - AWS CloudHSM
   - Azure Key Vault
   - Thales Luna

2. **Enable TLS**
   - All Sidecar communications over HTTPS
   - Minimum TLS 1.2

3. **Access Control**
   - Implement authentication for API endpoints
   - Use least-privilege principle

4. **Monitoring**
   - Log all erasure requests
   - Alert on chain verification failures

### Cryptographic Recommendations

- **Current**: AES-256-GCM + Ed25519
- **Future**: Plan migration to post-quantum algorithms (CRYSTALS-Kyber/Dilithium)

## Acknowledgments

We thank all security researchers who responsibly disclose vulnerabilities.

---

VeritasChain Standards Organization
security@veritaschain.org
