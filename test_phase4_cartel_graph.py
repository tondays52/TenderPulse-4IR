"""
TenderPulse 4IR - Phase 4 Cartel Graph Engine & Multi-Vector Collusion Verification Suite
Verifies 4 forensic collusion vectors:
1. Shared & consecutive bank guarantee serial numbers
2. Corporate address & TIN co-location clustering
3. Cover-bidding price spreads (+2% to +9% artificial quorum margin)
4. Rotational winning reciprocity matrices
And verifies the live REST API endpoints and RBAC protection.
"""

import os
import sys
import json
import requests

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT_DIR)

from backend.cartel_radar import CartelRadarEngine
from backend.auth_jwt import create_access_token, ROLE_AUDITOR, ROLE_ANALYST

API_BASE = "http://127.0.0.1:8080"

def test_multivector_forensic_engine():
    print("\n--- 1. Testing CartelRadarEngine Multi-Vector Collusion Forensics ---")
    engine = CartelRadarEngine()
    result = engine.analyze_bidding_syndicate()

    assert result["status"] == "ANALYSIS_COMPLETE"
    assert "forensic_vectors" in result
    vectors = result["forensic_vectors"]

    # Vector 1: Shared/Consecutive Bank Guarantees
    bgs = vectors.get("shared_bank_guarantees", [])
    assert len(bgs) > 0, "Expected at least 1 shared/consecutive bank guarantee match"
    bg_match = bgs[0]
    assert "CONSECUTIVE" in bg_match["match_type"] or "IDENTICAL" in bg_match["match_type"]
    print(f"  [PASS] Vector 1 (Bank Guarantees): Flagged {len(bgs)} matches (Sample: {bg_match['guarantee_a']} vs {bg_match['guarantee_b']})")

    # Vector 2: Corporate Address Co-Location
    addrs = vectors.get("address_clusters", [])
    assert len(addrs) > 0, "Expected at least 1 corporate address cluster"
    addr_match = addrs[0]
    assert "Motijheel" in addr_match["shared_address"] or "Sena Kalyan" in addr_match["shared_address"]
    print(f"  [PASS] Vector 2 (Address Clustering): Flagged {len(addrs)} co-located bidders at: '{addr_match['shared_address']}'")

    # Vector 3: Cover-Bidding Margin
    covers = vectors.get("cover_bidding_instances", [])
    assert len(covers) > 0, "Expected cover-bidding instances"
    sample_cover = covers[0]
    assert 2.0 <= sample_cover["spread_pct"] <= 9.0
    print(f"  [PASS] Vector 3 (Cover Bidding): Flagged {len(covers)} instances (Sample: {sample_cover['contractor']} spread=+{sample_cover['spread_pct']}%)")

    # Vector 4: Rotational Winning Reciprocity
    rotations = vectors.get("rotational_winning_pairs", [])
    assert len(rotations) > 0, "Expected rotational winning pairs"
    sample_rot = rotations[0]
    assert sample_rot["reciprocity_score"] >= 0.50
    print(f"  [PASS] Vector 4 (Rotational Wins): Flagged {len(rotations)} alternating pairs (Reciprocity: {sample_rot['reciprocity_score']})")

    # Network topology nodes and edges
    nodes = result.get("nodes", [])
    edges = result.get("edges", [])
    assert len(nodes) >= 4, "Expected at least 4 indexed contractor nodes"
    assert len(edges) >= 3, "Expected at least 3 co-bidding network edges"
    
    # Check that high-risk contractors are flagged
    high_risk_nodes = [n for n in nodes if n.get("risk_level") in ("CRITICAL_CARTEL", "SUSPECTED_COLLUSION")]
    assert len(high_risk_nodes) > 0
    print(f"  [PASS] Graph Topology: {len(nodes)} nodes, {len(edges)} edges, {len(high_risk_nodes)} high-risk cartel entities detected.")


def test_live_cartel_api():
    print("\n--- 2. Testing Live Cartel Analysis API with RBAC ---")
    auditor_jwt = create_access_token({"email": "auditor@tendertrading.gov.bd", "name": "Chief Auditor", "role": ROLE_AUDITOR})
    analyst_jwt = create_access_token({"email": "analyst@tendertrading.gov.bd", "name": "Estimator", "role": ROLE_ANALYST})

    # Auditor request (Authorized)
    r_auditor = requests.post(
        f"{API_BASE}/api/cartel/analyze",
        json={},
        headers={"Authorization": f"Bearer {auditor_jwt}"},
        timeout=5
    )
    assert r_auditor.status_code == 200, f"Expected 200, got {r_auditor.status_code}"
    data = r_auditor.json()
    assert "forensic_vectors" in data
    assert "overall_market_integrity_score" in data
    print(f"  [PASS] /api/cartel/analyze served multi-vector forensic report (Market Integrity: {data['overall_market_integrity_score']}/100).")

    # Analyst request (Denied with 403 Forbidden)
    r_analyst = requests.post(
        f"{API_BASE}/api/cartel/analyze",
        json={},
        headers={"Authorization": f"Bearer {analyst_jwt}"},
        timeout=5
    )
    assert r_analyst.status_code == 403, f"Expected 403, got {r_analyst.status_code}"
    print("  [PASS] RBAC Enforcement: Unauthorized Analyst role rejected with HTTP 403 Forbidden.")


if __name__ == "__main__":
    print("=================================================================")
    print("  TenderPulse 4IR - Phase 4 Cartel Graph Engine Verification")
    print("=================================================================")
    try:
        test_multivector_forensic_engine()
        test_live_cartel_api()
        print("\n=================================================================")
        print("  ALL PHASE 4 CHECKS PASSED (100% FORENSIC CARTEL GRAPH READY)")
        print("=================================================================")
    except AssertionError as ae:
        print(f"\n[FAIL] Test assertion failed: {ae}")
        sys.exit(1)
    except Exception as ex:
        print(f"\n[ERROR] Unexpected error: {ex}")
        sys.exit(1)
