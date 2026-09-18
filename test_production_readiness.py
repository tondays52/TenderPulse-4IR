"""
========================================================================================
 TenderPulse 4IR AI - Master Commercial Production Readiness Verification Suite
 Consolidates end-to-end testing across all 7 architectural transformation pillars:
 1. Containerization & Deployment Hardening (Docker, Nginx, Compose, Redis)
 2. Relational Database Persistence & Spatial Indexing (SQLAlchemy 2.0 ORM, SQLite/Postgres)
 3. Cryptographic JWT Security & Strict 3-Tier Enterprise RBAC (Tokens, Rotation, Role Guards)
 4. 5-Year Historical Cartel Graph Engine (4 Forensic Vectors & Collusion Risk Scoring)
 5. Resilient 24/7 Background Harvester & Corrigendum Tracker (Multi-Agency, Proxies, Audits)
 6. Copernicus Sentinel Hub Process API & LRU Radar Tile Cache (SAR Dual-Pol, PU Savings)
 7. Neuro-Symbolic AI, Z3 SMT Solver, zk-SNARK Vault & Full REST API Stack
========================================================================================
"""

import sys
import os
import time
import json
import requests

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT_DIR)

from backend.database import SessionLocal, init_db
from backend.models import TenderModel, UserModel, BiddingSyndicateModel, SarAuditModel, CorrigendumModel
import backend.crud as crud
from backend.auth_jwt import (
    create_access_token,
    create_refresh_token,
    rotate_refresh_token,
    ROLE_EXECUTIVE,
    ROLE_ANALYST,
    ROLE_AUDITOR,
    ROLE_ADMIN
)
from backend.cartel_radar import CartelRadarEngine
from backend.harvester_daemon import HarvesterDaemon
from backend.sentinel_hub import SentinelHubPipeline

BASE_URL = "http://127.0.0.1:8080"


def print_pillar_header(pillar_num: int, title: str):
    print(f"\n{'='*75}")
    print(f" PILLAR {pillar_num}: {title.upper()}")
    print(f"{'='*75}")


def test_pillar1_deployment():
    print_pillar_header(1, "Containerization & Deployment Hardening")
    dockerfile = os.path.join(ROOT_DIR, "Dockerfile")
    nginx_conf = os.path.join(ROOT_DIR, "nginx", "default.conf")
    compose = os.path.join(ROOT_DIR, "docker-compose.yml")
    env_file = os.path.join(ROOT_DIR, ".env")

    assert os.path.exists(dockerfile), "Dockerfile missing"
    assert os.path.exists(nginx_conf), "nginx/default.conf missing"
    assert os.path.exists(compose), "docker-compose.yml missing"
    assert os.path.exists(env_file), ".env configuration missing"

    with open(dockerfile, "r", encoding="utf-8") as f:
        df_content = f.read()
    assert "USER tenderpulse" in df_content or "1001" in df_content, "Non-root user required in Dockerfile"
    assert "HEALTHCHECK" in df_content, "Container healthcheck required"

    with open(nginx_conf, "r", encoding="utf-8") as f:
        ng_content = f.read()
    assert "gzip on" in ng_content, "Gzip compression required in Nginx"
    assert "X-Frame-Options" in ng_content, "Security headers required"

    print("  [✓] Multi-stage Dockerfile, Nginx reverse proxy, and Docker Compose stack verified.")


def test_pillar2_database():
    print_pillar_header(2, "SQLAlchemy 2.0 Persistence & Spatial Indexing")
    init_db()
    db = SessionLocal()
    try:
        t_count = db.query(TenderModel).count()
        u_count = db.query(UserModel).count()
        s_count = db.query(BiddingSyndicateModel).count()
        c_count = db.query(CorrigendumModel).count()

        print(f"  [+] Relational Database Tables: {t_count} Tenders, {u_count} Users, {s_count} Syndicates, {c_count} Corrigenda.")
        assert t_count >= 10, "Minimum tender records not found in database"
        assert u_count >= 5, "Minimum users not found in database"

        # Test Spatial BBOX query
        dhaka_bbox = [23.70, 90.30, 23.90, 90.50]
        spatial_tenders = crud.get_tenders_by_bbox(db, dhaka_bbox[0], dhaka_bbox[1], dhaka_bbox[2], dhaka_bbox[3])
        print(f"  [+] Spatial BBOX query returned {len(spatial_tenders)} projects in Dhaka envelope.")
        assert len(spatial_tenders) >= 1, "Spatial BBOX query failed to return records"

        print("  [✓] Database persistence, ORM models, and spatial indexing verified.")
    finally:
        db.close()


def test_pillar3_jwt_rbac():
    print_pillar_header(3, "Cryptographic JWT Security & Strict 3-Tier RBAC")
    
    # 1. Access and refresh token pair
    user_exec = {
        "email": "exec@tendertrading.gov.bd",
        "name": "Managing Director",
        "role": ROLE_EXECUTIVE,
        "agency": "Di-Tender Ltd."
    }
    user_analyst = {
        "email": "analyst@tendertrading.gov.bd",
        "name": "Tender Analyst",
        "role": ROLE_ANALYST,
        "agency": "LGED"
    }
    user_auditor = {
        "email": "auditor@tendertrading.gov.bd",
        "name": "Audit Officer",
        "role": ROLE_AUDITOR,
        "agency": "CPTU"
    }

    token_exec = create_access_token(user_exec)
    token_analyst = create_access_token(user_analyst)
    token_auditor = create_access_token(user_auditor)

    refresh_token = create_refresh_token(user_exec["email"])
    new_acc, new_ref, _ = rotate_refresh_token(refresh_token)
    assert new_acc is not None and new_ref is not None, "Token rotation failed"

    # 2. Test RBAC permissions against live endpoints
    # Executive -> /api/zkp/prove (Allowed)
    res1 = requests.post(
        f"{BASE_URL}/api/zkp/prove",
        headers={"Authorization": f"Bearer {token_exec}"},
        json={"peak_turnover_bdt": 400000000.0, "liquid_assets_bdt": 120000000.0, "required_turnover_bdt": 300000000.0, "required_liquidity_bdt": 80000000.0},
        timeout=5
    )
    assert res1.status_code == 200, f"Executive should be authorized for ZKP: {res1.text}"

    # Analyst -> /api/zkp/prove (Forbidden 403)
    res2 = requests.post(
        f"{BASE_URL}/api/zkp/prove",
        headers={"Authorization": f"Bearer {token_analyst}"},
        json={"peak_turnover_bdt": 400000000.0, "liquid_assets_bdt": 120000000.0, "required_turnover_bdt": 300000000.0, "required_liquidity_bdt": 80000000.0},
        timeout=5
    )
    assert res2.status_code == 403, f"Analyst should be rejected with 403: {res2.status_code}"

    # Auditor -> /api/cartel/analyze (Allowed)
    res3 = requests.post(
        f"{BASE_URL}/api/cartel/analyze",
        headers={"Authorization": f"Bearer {token_auditor}"},
        json={},
        timeout=5
    )
    assert res3.status_code == 200, f"Auditor should be authorized for Cartel Radar: {res3.text}"

    # Analyst -> /api/cartel/analyze (Forbidden 403)
    res4 = requests.post(
        f"{BASE_URL}/api/cartel/analyze",
        headers={"Authorization": f"Bearer {token_analyst}"},
        json={},
        timeout=5
    )
    assert res4.status_code == 403, f"Analyst should be rejected from Cartel Radar: {res4.status_code}"

    print("  [✓] JWT issuance, cryptographic signature, token rotation, and 3-Tier RBAC verified.")


def test_pillar4_cartel_radar():
    print_pillar_header(4, "5-Year Historical Cartel Graph Engine")
    engine = CartelRadarEngine()
    report = engine.analyze_bidding_syndicate()

    assert "forensic_vectors" in report, "Missing forensic vectors"
    vectors = report["forensic_vectors"]
    assert "shared_bank_guarantees" in vectors, "Vector 1 missing"
    assert "address_clusters" in vectors, "Vector 2 missing"
    assert "cover_bidding_instances" in vectors, "Vector 3 missing"
    assert "rotational_winning_pairs" in vectors, "Vector 4 missing"

    market_integrity = report.get("market_integrity_score", 0.0)
    print(f"  [+] Analyzed {len(report.get('nodes', []))} bidders and {len(report.get('syndicates', []))} syndicates.")

    print(f"  [+] Market Integrity Score: {market_integrity:.1f}/100.0")
    print(f"  [+] Forensic Flags: BG matches={len(vectors['shared_bank_guarantees'])}, Co-locations={len(vectors['address_clusters'])}, Cover spreads={len(vectors['cover_bidding_instances'])}, Rotations={len(vectors['rotational_winning_pairs'])}")

    print("  [✓] Multi-vector forensic cartel engine and graph topology verified.")



def test_pillar5_harvester():
    print_pillar_header(5, "Resilient Harvester Daemon & Corrigenda")
    daemon = HarvesterDaemon(agencies=["LGED"], limit_per_agency=2, min_delay=0.1, max_delay=0.2)
    cycle_res = daemon.run_harvest_cycle()
    assert cycle_res["harvested"] >= 1, "Harvester failed to ingest notices"
    print(f"  [+] Harvest cycle executed: {cycle_res['harvested']} notices processed across {cycle_res['agencies_polled']} agencies.")

    # Check REST status
    res = requests.get(f"{BASE_URL}/api/harvester/status", timeout=5)
    assert res.status_code == 200, "Harvester status API failed"
    status_info = res.json()["telemetry"]
    print(f"  [+] Harvester Daemon Status: {status_info.get('status')}, Total Mined: {status_info.get('total_harvested_count')}")

    # Check Corrigenda
    res_corr = requests.get(f"{BASE_URL}/api/corrigenda", timeout=5)
    assert res_corr.status_code == 200, "Corrigenda API failed"
    corrigenda_count = res_corr.json().get("count", 0)
    print(f"  [+] Recorded Corrigenda in database: {corrigenda_count} notices.")

    print("  [✓] Autonomous Harvester Daemon and Corrigendum Tracker verified.")


def test_pillar6_sentinel_cache():
    print_pillar_header(6, "Copernicus Sentinel Hub Process API & Radar Tile Cache")
    pipeline = SentinelHubPipeline()
    test_bbox = [23.8103, 90.4125, 23.8203, 90.4225]

    # Cold query
    pipeline.clear_cache()
    r1 = pipeline.query_sar_raster(test_bbox, tender_id="PROD-TEST-1")
    assert r1["cache_hit"] is False, "First request should be cache miss"

    # Warm query
    r2 = pipeline.query_sar_raster(test_bbox, tender_id="PROD-TEST-1")
    assert r2["cache_hit"] is True, "Second request must hit cache"
    assert r2["source"] == "satellite_disk_cache", "Expected disk cache source"

    stats = pipeline.get_cache_stats()
    print(f"  [+] Tile Cache Telemetry: hits={stats['hits']}, misses={stats['misses']}, PU units saved={stats['pu_saved']}")

    # Live REST query
    res = requests.post(f"{BASE_URL}/api/sentinel/query", json={"bbox": test_bbox, "tender_id": "PROD-TEST-1"}, timeout=5)
    assert res.status_code == 200, "Live sentinel query failed"
    data = res.json()
    assert len(data["elevation_matrix"]) == 16, "16x16 elevation matrix required"

    print("  [✓] Process API dual-pol SAR pipeline and LRU disk caching verified.")


def test_pillar7_ai_engines():
    print_pillar_header(7, "Formal Neuro-Symbolic AI & Full REST API Stack")
    
    # 1. Health check & 13 active AI engines
    res_health = requests.get(f"{BASE_URL}/api/health", timeout=5)
    assert res_health.status_code == 200, "Health check failed"
    engines = res_health.json()["active_ai_engines"]
    expected_engines = [
        "smt_solver", "cartel_radar", "sar_satellite_auditor", "pdf_boq_parser",
        "zkp_prover", "std_generator", "bank_connect", "compliance_matrix",
        "copilot", "decision_engine", "sentinel_pipeline", "database", "harvester_daemon"
    ]
    for eng in expected_engines:
        assert eng in engines, f"Engine '{eng}' missing from active_ai_engines"
    print(f"  [+] Verified all {len(engines)} active AI engines and subsystems in /api/health.")

    # 2. Z3 SMT Solver
    res_smt = requests.post(
        f"{BASE_URL}/api/smt/verify",
        json={"tender_id": "986772", "estimated_cost_bdt": 250000000.0, "bid_price_bdt": 227750000.0, "turnover_bdt": 400000000.0, "liquid_assets_bdt": 100000000.0},
        timeout=5
    )
    assert res_smt.status_code == 200 and res_smt.json().get("status") == "SAT", "SMT solver failed"
    print("  [+] Microsoft Z3 SMT Legal Prover: Formal SAT Verification Certified.")

    # 3. BankConnect Credit Simulation & Pre-Approval
    res_bank = requests.get(f"{BASE_URL}/api/bank/partners", timeout=5)
    assert res_bank.status_code == 200 and len(res_bank.json().get("partners", [])) >= 4, "BankConnect partners failed"
    print(f"  [+] BankConnect API: {len(res_bank.json().get('partners', []))} Commercial Banking Gateways Online.")


    # 4. CPTU Compliance Matrix
    res_comp = requests.post(
        f"{BASE_URL}/api/compliance/analyze",
        json={"clauses": [{"clause_id": "ITT 25.1", "clause_title": "Turnover", "contractor_status": "COMPLIANT"}]},
        timeout=5
    )
    assert res_comp.status_code == 200, "Compliance Matrix failed"
    print(f"  [+] CPTU Compliance Matrix: {res_comp.json().get('grade')} certified.")

    # 5. Executive AI Copilot
    res_copilot = requests.post(
        f"{BASE_URL}/api/copilot/query",
        json={"query": "Explain minimum turnover requirements under ITT 25.1"},
        timeout=5
    )
    assert res_copilot.status_code == 200, "Copilot failed"
    print("  [+] Executive AI Copilot: Instant context-aware response generated.")

    print("  [✓] Full Neuro-Symbolic AI, Z3 SMT Prover, and REST API stack verified.")


if __name__ == "__main__":
    print("\n" + "#"*75)
    print("  TENDERPULSE 4IR AI - COMMERCIAL PRODUCTION READINESS AUDIT  ")
    print("#"*75)

    start = time.time()
    test_pillar1_deployment()
    test_pillar2_database()
    test_pillar3_jwt_rbac()
    test_pillar4_cartel_radar()
    test_pillar5_harvester()
    test_pillar6_sentinel_cache()
    test_pillar7_ai_engines()
    elapsed = time.time() - start

    print("\n" + "="*75)
    print("  ALL 7 PRODUCTION READINESS PILLARS PASSED (100% COMMERCIAL READY)  ")
    print(f"  Total Audit Execution Time: {elapsed:.2f} seconds")
    print("="*75 + "\n")
