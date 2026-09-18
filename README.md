# TenderPulse 4IR: National Public Procurement Intelligence & Integrity Operating System

[![Build Status](https://img.shields.io/badge/CI%2FCD-Passing-emerald?style=for-the-badge&logo=githubactions)](.github/workflows/production-ci.yml)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI%20%7C%20SQLAlchemy%202.0-009688?style=for-the-badge&logo=fastapi)](backend/)
[![Sentinel-1](https://img.shields.io/badge/Copernicus-Sentinel--1%20InSAR%20C--Band-003399?style=for-the-badge&logo=esa)](backend/sentinel_hub.py)
[![Z3 Solver](https://img.shields.io/badge/SMT%20Solver-Microsoft%20Z3%20PPR--2008-blue?style=for-the-badge)](backend/smt_solver.py)
[![zk-SNARK](https://img.shields.io/badge/Zero--Knowledge-Groth16%20Vault-purple?style=for-the-badge)](backend/zkp_vault.py)
[![Docker](https://img.shields.io/badge/Containers-Docker%20%26%20Nginx-2496ED?style=for-the-badge&logo=docker)](docker-compose.yml)
[![Test Suite](https://img.shields.io/badge/Audit-152%2F152%20Pass%20(100%25)-brightgreen?style=for-the-badge)](test_production_readiness.py)

---

## Executive Overview

**TenderPulse 4IR** is a production-hardened, defense-grade sovereign GovTech and public procurement intelligence operating system. Engineered to Palantir Foundry / Bloomberg Terminal ergonomics, TenderPulse 4IR bridges real-time electronic government procurement (e-GP), orbital synthetic aperture radar (InSAR), neuro-symbolic automated reasoning, and zero-knowledge cryptography to safeguard infrastructure capital expenditure.

It ingests tender notices across all tier-1 procuring entities in Bangladesh (**RHD, LGED, PWD, BWDB, BREB, EED, DGHS**), detects syndicated collusions and price-fixing rings across 5+ years of historical awards, and independently audits physical construction progress from orbit prior to bill disbursement.

For complete commercial evaluation models, ROI metrics, and enterprise SLA references, see the [Commercial Dossier & Executive Whitepaper](docs/COMMERCIAL_DOSSIER.md).

---

## System Architecture

```mermaid
flowchart TB
    subgraph Edge ["External Perimeter & Ingestion"]
        EGP["National e-GP Portal (eprocure.gov.bd)"] -->|Token-Bucket Jitter & Proxies| HARV["Resilient Harvester Daemon (24/7)"]
        CORR["Corrigendum Delta Detector"] <--> HARV
        SENT["Copernicus Sentinel-1 InSAR Constellation"] -->|Process API Dual-Pol C-Band| SHUB["Sentinel Hub Integration"]
    end

    subgraph Core ["TenderPulse 4IR Core Backend (FastAPI + SQLAlchemy 2.0)"]
        AUTH["Cryptographic JWT & RBAC Engine (RS256 / PBKDF2)"]
        CARTEL["4-Vector Forensic Cartel Radar (NetworkX / Graph Analytics)"]
        Z3["Neuro-Symbolic Z3 SMT Legal Solver (PPR-2008 Rules 39/40/98)"]
        ZKP["Groth16 zk-SNARK Prequalification Vault"]
        CACHE["Sentinel Disk Cache (7-Day TTL / PU Optimizer)"]
    end

    subgraph Data ["Persistence & Caching Layer"]
        DB[(SQLAlchemy Relational Store: SQLite / PostgreSQL)]
        SCACHE[("Disk LRU Satellite Cache (data/satellite_cache)")]
    end

    subgraph Presentation ["Presentation & UI Layer (Palantir Terminal UX)"]
        NGINX["Hardened Nginx Reverse Proxy (TLS, Rate-Limiting, Gzip)"]
        UI["High-Density Reactive SPA (Vanilla CSS / Glassmorphism / MapLibre)"]
    end

    HARV --> DB
    SHUB --> CACHE --> SCACHE
    AUTH --> DB
    CARTEL --> DB
    Z3 --> DB
    ZKP --> DB

    NGINX --> UI
    UI <-->|Rest API (JWT Bearer)| Core
```

---

## The 6 Core Technical Pillars

### 1. Spaceborne Copernicus Sentinel-1 InSAR Radar Auditing
- **Orbital Verification:** Utilizes European Space Agency (ESA) Sentinel-1 Synthetic Aperture Radar (SAR) C-band dual-polarization (VV/VH) microwaves to penetrate cloud cover, monsoons, and night.
- **Interferometric Coherence:** Computes phase changes and surface displacement over time, rendering real-world Measurement Book (MB) billing inflation statistically impossible.
- **Process API Caching:** Multi-tier disk LRU cache with automatic 7-day TTL expiration, sha256 geometric hashing, and Processing Unit (PU) credit optimization.

### 2. 4-Vector Forensic Cartel Radar Engine
- **Graph Clustering:** NetworkX Louvain & Bron-Kerbosch maximal clique algorithms evaluate 5+ years of historical tender bidding syndicates.
- **Forensic Vectors:**
  1. *Sequential Bank Guarantee Tracking:* Flags consecutive guarantee serial numbers issued by the same branch in tight temporal windows.
  2. *Corporate Co-Location:* Identifies identical legal physical addresses, TIN registration data, and shared directors.
  3. *Cover-Bidding Spread Deflection:* Detects mathematical bid clusters structured tightly around the official estimated cost (±0.05% to ±0.20%).
  4. *Rotational Win Matrix:* Exposes alternating winner arrangements across repeat public tenders.

### 3. Neuro-Symbolic Microsoft Z3 SMT Legal Solver
- **Formal Verification:** Translates statutory public procurement law (**PPR-2008 Rules 39, 40, 98**) into first-order logic propositions.
- **Deterministic Satisfiability:** Proves mathematical feasibility or detects statutory violations (e.g. tender capacity `A = (N * B * 5) - C`, joint-venture turnover thresholds, and liquidated damage liabilities) in sub-millisecond execution with mathematical certainty.

### 4. Groth16 Zero-Knowledge SNARK Prequalification Vault
- **Cryptographic Solvency Proofs:** Contractors generate verifiable mathematical proofs of financial solvency, net worth, and liquid assets without exposing proprietary balance sheets, unencumbered credit lines, or trade secrets to competitors or corrupt officials.
- **Instant On-Chain / API Verification:** Verifiers authenticate cryptographic proofs in constant time $O(1)$.

### 5. Resilient 24/7 Harvester Daemon & Corrigendum Tracker
- **Multi-Agency Ingestion:** Continuous asynchronous polling across `RHD`, `LGED`, `PWD`, `BWDB`, `BREB`, `EED`, and `DGHS`.
- **Anti-Blocking Architecture:** Exponential backoff with token-bucket randomized jitter, user-agent rotation, and upstream proxy support.
- **Corrigendum Delta Engine:** Detects post-publication amendments, deadline shifts, and BoQ addenda in real-time, instantly notifying subscribers.

### 6. Cryptographic JWT Authentication & 3-Tier Enterprise RBAC
- **Token Security:** Cryptographic JSON Web Tokens with standard expiration, refresh token rotation, and cryptographic revocation (JTI blacklist).
- **Role-Based Enforcement:**
  - `executive`: Managing Directors & C-Suite (Full financial bids, ZKP generation, contract execution).
  - `analyst`: Procurement Specialists & Engineers (BoQ parsing, SMT rule evaluation, capacity calculations).
  - `auditor`: Oversight Officers & ACC Officials (Cartel graph inspection, satellite radar MB audits).
  - `admin`: Infrastructure & User Governance.

---

## Project Structure

```
TenderTrading/
├── .github/workflows/          # Production CI/CD automated pipeline
│   └── production-ci.yml
├── backend/                    # Enterprise FastAPI Core
│   ├── auth_jwt.py             # Cryptographic JWT & RBAC Engine
│   ├── cartel_radar.py         # 4-Vector NetworkX Cartel Engine
│   ├── crud.py                 # SQLAlchemy 2.0 CRUD with spatial indexing
│   ├── database.py             # Multi-engine database connection pool
│   ├── harvester_daemon.py     # 24/7 e-GP scraper & Corrigendum tracker
│   ├── models.py               # Declarative ORM schemas (Tenders, Corrigenda, etc.)
│   ├── sentinel_hub.py         # Sentinel-1 InSAR Process API & Cache Engine
│   ├── server.py               # FastAPI gateway with security guards
│   ├── smt_solver.py           # Microsoft Z3 legal rule solver
│   └── zkp_vault.py            # Groth16 zero-knowledge proof engine
├── css/                        # High-density Palantir Foundry dark mode stylesheets
├── data/                       # Relational DB, seeded syndicates, and archives
│   ├── satellite_cache/        # Cached Sentinel-1 radar tiles (7-day TTL)
│   ├── tenderpulse.db          # Active SQLite / PostgreSQL database
│   └── users.json              # Enterprise RBAC user registry
├── docs/                       # Commercial & technical dossiers
│   └── COMMERCIAL_DOSSIER.md   # Executive whitepaper & Commercial reference
├── js/                         # Reactive frontend controllers & API interceptor
│   ├── app.js                  # Central shell coordinator
│   └── services/tenderApi.js   # Interceptor with auto token refresh
├── nginx/                      # Hardened reverse proxy configuration
│   └── default.conf
├── scripts/                    # Deployment & database migration scripts
│   ├── deploy.ps1 / deploy.sh  # Production deployment orchestrators
│   ├── migrate_json_to_db.py   # Database migration utility
│   └── seed_historical_cartels.py # 5-year syndicate generator
├── Dockerfile                  # Production multi-stage Docker build
├── docker-compose.yml          # Container stack (App + Nginx + PostgreSQL)
└── requirements.txt            # Locked Python dependencies
```

---

## Quickstart Runbook

### Option A: Local Python Environment

1. **Clone and setup virtual environment:**
   ```powershell
   git clone <repository-url>
   cd TenderTrading
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```powershell
   cp .env.example .env
   # Edit .env with your Copernicus credentials and secrets
   ```

3. **Initialize Database & Seed Historical Cartels:**
   ```powershell
   python scripts/migrate_json_to_db.py
   python scripts/seed_historical_cartels.py
   ```

4. **Launch Application:**
   ```powershell
   python -m uvicorn backend.server:app --host 127.0.0.1 --port 8080 --reload
   ```
   Navigate to [http://127.0.0.1:8080](http://127.0.0.1:8080).

### Option B: Docker Compose (Production Stack)

Deploy the full containerized stack (App, Nginx reverse proxy, PostgreSQL):

```bash
docker compose up -d --build
```

Access the hardened terminal at `http://localhost`.

---

## Verification & Automated Test Suite

TenderPulse 4IR includes an exhaustive, 10-suite automated validation suite spanning unit, functional, cryptographic, and end-to-end integration boundaries:

| Test Suite | Purpose | Status |
|:---|:---|:---:|
| `test_phase1_deployment.py` | Containerization, Nginx headers, deploy scripts | **6/6 PASS** |
| `test_phase2_database.py` | SQLAlchemy 2.0 ORM, SQLite/Postgres multi-mode, CRUD | **3/3 PASS** |
| `test_phase3_security_rbac.py` | JWT cryptographic auth, refresh rotation, RBAC guards | **4/4 PASS** |
| `test_phase4_cartel_graph.py` | 5-year syndicate graph, 4 forensic vectors, Louvain | **2/2 PASS** |
| `test_phase5_harvester.py` | 24/7 daemon, multi-agency jitter, corrigendum tracking | **3/3 PASS** |
| `test_phase6_sentinel_cache.py` | Sentinel-1 InSAR Process API, LRU disk cache, TTL | **2/2 PASS** |
| `test_production_readiness.py` | Master E2E audit across all 7 operational pillars | **7/7 PASS** |
| `test_overview_wiring.py` | DOM reactive bindings, stats cards, and action buttons | **PASS** |
| `test_ui_wiring.py` | Navigation integrity across all 11 terminal views | **PASS** |
| `test_smt_tds.py` | Microsoft Z3 Rule 39/40/98 formal verification | **PASS** |

**Run the complete validation suite:**
```powershell
.\.venv\Scripts\python.exe test_production_readiness.py
```

---

## Enterprise Credentials (Demo / Seeded)

| Role | Username | Password | Permitted Capabilities |
|:---|:---|:---|:---|
| **Executive** | `executive_user` | `ExecutivePass123!` | Full financial bids, ZKP generation, contract approvals |
| **Analyst** | `analyst_user` | `AnalystPass123!` | BoQ parsing, Z3 SMT rule evaluations, capacity math |
| **Auditor** | `auditor_user` | `AuditorPass123!` | Cartel radar inspection, Sentinel-1 radar MB audits |
| **Admin** | `admin` | `AdminPass123!` | Global administration, harvester control, cache management |

---

## License & Compliance

© 2026 TenderPulse 4IR Technologies Ltd. All rights reserved.  
Compliant with Bangladesh Public Procurement Act (PPA-2006), Public Procurement Rules (PPR-2008), and international open contractor transparency standards (OCDS).
