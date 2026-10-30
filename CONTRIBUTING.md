# Contributing to VCP Crypto-Shredding PoC

Thank you for your interest in contributing to the VeritasChain Protocol! This document provides guidelines and instructions for contributing.

## Code of Conduct

By participating in this project, you agree to abide by the [Contributor Covenant Code of Conduct](https://www.contributor-covenant.org/version/2/1/code_of_conduct/).

## How to Contribute

### Reporting Issues

1. **Search existing issues** to avoid duplicates
2. **Use issue templates** when available
3. **Provide details**:
   - Clear description of the problem
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment (OS, Python version, etc.)

### Submitting Pull Requests

1. **Fork the repository**
2. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes**
4. **Write/update tests**
5. **Run the test suite**:
   ```bash
   pytest tests/ -v
   ```
6. **Commit with clear messages**:
   ```bash
   git commit -m "feat: add crypto-shredding batch processing"
   ```
7. **Push and create PR**

### Commit Message Convention

We follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation only
- `style:` Code style (formatting, etc.)
- `refactor:` Code refactoring
- `test:` Adding/updating tests
- `chore:` Maintenance tasks

### Code Style

- **Python**: Follow PEP 8, use type hints
- **MQL5**: Follow MQL5 naming conventions
- **Documentation**: Use docstrings (Google style)

### Testing Requirements

- All new features must include tests
- Maintain >80% code coverage
- Tests must pass on Python 3.10, 3.11, 3.12

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR-USERNAME/vcp-gdpr-poc.git
cd vcp-gdpr-poc

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt  # includes pytest; there is no requirements-dev.txt

# Run tests
pytest tests/ -v
```

## Areas for Contribution

### High Priority
- [ ] HSM integration (AWS CloudHSM, Azure Key Vault)
- [ ] PostgreSQL/TimescaleDB persistence
- [ ] External blockchain anchoring
- [ ] Zero-knowledge proof integration

### Documentation
- [ ] API documentation improvements
- [ ] Tutorial videos
- [ ] Multi-language translations (DE, FR, ES)

### Testing
- [ ] Performance benchmarks
- [ ] Stress testing for HFT scenarios
- [ ] Security audit assistance

## Security

**Do not report security vulnerabilities through public issues.**

Email: security@veritaschain.org

See [SECURITY.md](SECURITY.md) for details.

## License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.

## Questions?

- Email: technical@veritaschain.org
- GitHub Discussions: [veritaschain/vcp-gdpr-poc/discussions](https://github.com/veritaschain/vcp-gdpr-poc/discussions)

---

Thank you for contributing to the future of verifiable AI and algorithmic trading transparency! 🚀
