# Security Policy — TenderPulse 4IR

**TenderPulse 4IR** is a sovereign-grade national public procurement intelligence and integrity operating system designed for anti-corruption, procurement auditing, and cartel detection. Security, auditability, and defense-in-depth are foundational architectural requirements.

---

## 1. Supported Versions

Security updates and critical vulnerability patches are applied to the active production branch.

| Version | Supported          | Security Maintenance Level |
| ------- | ------------------ | -------------------------- |
| 2.0.x   | :white_check_mark: | Active production & critical patches |
| 1.5.x   | :white_check_mark: | Maintenance only           |
| < 1.5   | :x:                | End of Life (Unsupported)  |

---

## 2. Reporting a Vulnerability

We welcome responsible security disclosures from security researchers, auditors, and civil service engineers.

### How to Report

1. **Email Directly**: Send encrypted or structured reports to:
   - `security@tendertrading.gov.bd` or `majumder.law@tendertrading.gov.bd`
2. **Details to Include**:
   - Vulnerability classification (e.g., Auth bypass, Injection, SMT DoS, WebSocket exhaustion)
   - Step-by-step reproduction steps or proof-of-concept (PoC)
   - Potential impact on national procurement data or audit integrity
   - Recommended remediation if known
3. **Response Timelines**:
   - **Initial Acknowledgement**: Within 24 hours
   - **Triage & Severity Rating (CVSS v3.1)**: Within 72 hours
   - **Remediation & Patch Deployment**: Within 7 business days for High/Critical issues

> **Responsible Disclosure Policy**: Please do NOT publicly disclose or file public GitHub issues for security vulnerabilities until our engineering and security response team has had reasonable time to patch and verify the fix.

---

## 3. Defense-in-Depth Security Architecture

TenderPulse 4IR implements multi-tiered security controls across application layers:

### A. Role-Based Access Control (RBAC) & Authentication
- **HMAC-SHA256 JWT**: Stateless token architecture with tight expirations and explicit role segregation:
  - `ROLE_EXECUTIVE` (Managing Director, C-suite analytics)
  - `ROLE_LEGAL` (Anti-Corruption Commission & legal enforcement)
  - `ROLE_AUDITOR` (IMED / SMT compliance auditors)
  - `ROLE_ENGINEER` (Technical officers & field inspectors)
  - `ROLE_CITIZEN` (Public read-only transparency portal)
- **Constant-Time Password Comparison**: Using `passlib` bcrypt hashing with automatic salt rotation.

### B. Neuro-Symbolic & Formal Verification Safety
- **Microsoft Z3 SMT Execution Isolation**: SMT constraint checking runs in a dedicated thread-safe executor pool with CPU timeouts (5,000ms max) to prevent resource starvation or ReDoS/SMT-DoS attacks against the solver.
- **Strict Grammar Parsing**: Input predicates for tender evaluation are sanitized against malicious constraint injections.

### C. Zero-Knowledge Cryptographic Vault
- **Groth16 zk-SNARK Verification**: Financial turnover and contractor liquidity qualifications are proven without revealing sensitive banking figures or commercial trade secrets.
- **Tamper-Proof Verification Keys**: Cryptographic verification parameters are pinned and immutably checked against tampering.

### D. WebSocket & Live Streaming Perimeter
- **Client Rate Limiting**: Max event push limits and heartbeat pings (`PING/PONG`) with automatic socket pruning on broken connections.
- **Payload Validation**: Strict Pydantic model serialization on all broadcast events to prevent XSS injection via broadcast channels.

### E. Ingestion Harvester Security
- **Anti-Scraping Compliance & Token-Bucket Jitter**: Harvesters enforce exponential backoff and randomized delays (1.5s–4.0s) to guarantee zero-impact on national e-GP portal infrastructure.
- **Input Sanitization**: HTML stripping, parameter encoding, and schema conformance tests before entering SQLite/PostgreSQL storage.

---

## 4. Threat Matrix & Mitigations

| Threat Vector | Potential Impact | In-Place Mitigation |
| ------------- | ---------------- | ------------------- |
| **Bid Rigging / Cartel Spoofing** | Compromised award integrity | 4-Vector GAT Graph Cartel Radar cross-validates historical co-bidding, price clustering, and rotation patterns. |
| **Measurement Book Inflation** | Ghost billing on public works | Copernicus Sentinel-1 InSAR synthetic aperture radar independent orbital verification of physical site displacement. |
| **Token Hijacking / Replay** | Unauthorized audit actions | Short-lived JWTs, TLS 1.3 enforcement, and explicit header authorization checks. |
| **SMT Solver Resource Exhaustion** | Backend denial of service | Worker timeouts, memory bounds, and asynchronous queue dispatching. |
| **Database Tampering** | Falsified historical records | Cryptographic SHA-256 hash chains on tender audit logs and automated integrity seals. |

---

## 5. Security Testing & Auditing

Every release must pass our automated production-readiness security test suites:

```bash
# Run RBAC, JWT, and Cartel Stream security checks
python test_live_cartel_stream.py
python test_production_readiness.py
```

All 17 verification suites validate authorization barriers, payload boundaries, and memory safety.
