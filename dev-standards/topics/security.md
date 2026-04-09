# Security Standards

**Status:** Draft (foundational — expand during project brainstorming)

## Core Principle

Validate at trust boundaries. Treat external input as untrusted. Keep secrets out of code.

---

## Related Topics

- **Input validation at boundaries**: See [Data Integrity Standards](./data-integrity.md) — trust boundaries and data boundaries overlap; validation serves both security and data correctness
- **Secrets management**: See [Configuration Standards](./configuration.md) — patterns for loading, validating, and injecting secrets

---

## Tier Requirements

### Exploratory

- Secrets in `.env` files (not committed)
- Basic input validation on external data
- No hardcoded credentials

### Internal

- All Exploratory requirements
- Input validation with clear error messages
- Parameterized queries (no string interpolation for SQL/NoSQL)
- Encryption for sensitive data at rest

### Production

- All Internal requirements
- Secrets in environment variables or secret manager
- Encryption in transit (HTTPS, TLS)
- Authentication on all non-public endpoints
- Authorization checks per operation
- Audit logging for sensitive actions
- Dependency vulnerability scanning

---

## Current Tooling

| Concern | Approach |
|---------|----------|
| Secrets | `.env` files (gitignored) |
| Encryption | Standard packages (Python: `cryptography`, JS/TS: `crypto`, MongoDB: field-level encryption) |

---

## Trust Boundaries

Validate data when it crosses these boundaries:

- User input → Application
- External API response → Application
- File upload → Application
- Database read (if data origin untrusted) → Application

---

## Common Vulnerabilities Reference

| Vulnerability | Prevention |
|---------------|------------|
| Injection (SQL, NoSQL, command) | Parameterized queries, never interpolate |
| Broken authentication | Secure session handling, MFA for sensitive ops |
| Sensitive data exposure | Encrypt at rest and transit, minimal data retention |
| Broken access control | Check permissions on every request |

---

## Expand During Brainstorming

When a project involves user data, authentication, or public exposure, revisit this document and specify:

- Authentication method (JWT, sessions, OAuth)
- Authorization model (RBAC, ABAC, simple checks)
- Data classification (what's sensitive?)
- Compliance requirements (GDPR, etc.)
- Specific encryption requirements
