"""
TenderPulse 4IR AI - 64-District Bangladesh GIS Cartel Heat Map Verification Suite
Tests the geospatial aggregation endpoint, all 64 district coordinates, integrity scores,
cross-district syndicate arcs, filtering, and RBAC authentication.
"""

import sys
import requests
import json

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_URL = "http://127.0.0.1:8080"


def test_district_heatmap():
    print("===========================================================================")
    print(" [*] TESTING 64-DISTRICT BANGLADESH GIS CARTEL HEATMAP & GEOSPATIAL ENGINE")
    print(f" Target: {BASE_URL}")
    print("===========================================================================\n")

    # 1. Authenticate as Auditor
    print("--- 1. Authenticating Roles for Geospatial Telemetry ---")
    auditor_login = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "majumder.law@tendertrading.gov.bd",
        "password": "majumder123"
    }, timeout=10)
    assert auditor_login.status_code == 200, f"Auditor login failed: {auditor_login.text}"
    auditor_token = auditor_login.json()["access_token"]
    print(f"[✓] Auditor authenticated (token length: {len(auditor_token)})")

    headers = {"Authorization": f"Bearer {auditor_token}"}

    # 2. National 64-District Heat Map Aggregation
    print("\n--- 2. Testing Full 64-District National Heat Map Telemetry ---")
    resp = requests.get(f"{BASE_URL}/api/cartel/district-heatmap", headers=headers, timeout=15)
    assert resp.status_code == 200, f"Heatmap request failed: {resp.status_code} {resp.text}"
    data = resp.json()

    assert data.get("success") is True, "Expected success=True"
    assert data["total_districts"] == 64, f"Expected 64 districts, got {data['total_districts']}"
    assert len(data["districts"]) == 64, f"Expected 64 district objects, got {len(data['districts'])}"

    nat_score = data["national_integrity_score"]
    tot_pkg = data["total_packages"]
    tot_vol_cr = data["total_volume_cr"]
    col_vol_cr = data["collusive_volume_cr"]
    crit_count = data["critical_threat_districts_count"]

    print(f"[✓] Successfully retrieved 64 administrative districts:")
    print(f"    National Market Integrity: {nat_score}/100")
    print(f"    Total Packages Monitored:  {tot_pkg:,}")
    print(f"    Total Procurement Volume:  ৳{tot_vol_cr:,.2f} Cr")
    print(f"    Collusive Anomaly Volume:  ৳{col_vol_cr:,.2f} Cr")
    print(f"    Critical Cartel Rings:     {crit_count} Districts")

    assert tot_pkg >= 45000, f"Expected at least 45,000 packages, got {tot_pkg}"
    assert 50.0 <= nat_score <= 90.0, f"Unexpected national integrity score: {nat_score}"
    assert crit_count > 0, "Expected at least 1 critical cartel ring district"

    # 3. Verify Geographic Validity & Data Integrity on Each District
    print("\n--- 3. Verifying Centroid Coordinates and Attributes across all 64 Districts ---")
    district_names = set()
    divisions_found = set()

    for d in data["districts"]:
        name = d["district"]
        district_names.add(name)
        div = d["division"]
        divisions_found.add(div)

        lat = d["latitude"]
        lon = d["longitude"]
        score = d["integrity_score"]
        tier = d["threat_tier"]

        # Bangladesh geographic bounds: 20.5 <= lat <= 26.7, 88.0 <= lon <= 92.8
        assert 20.5 <= lat <= 26.7, f"Invalid latitude for {name}: {lat}"
        assert 88.0 <= lon <= 92.8, f"Invalid longitude for {name}: {lon}"
        assert 0.0 <= score <= 100.0, f"Invalid score for {name}: {score}"
        assert tier in ("CRITICAL", "HIGH", "ELEVATED", "MODERATE", "CLEAN"), f"Invalid tier for {name}: {tier}"

    print(f"[✓] All 64 district centroids geometrically verified within Bangladesh bounding box.")
    print(f"[✓] Divisions represented ({len(divisions_found)}): {sorted(list(divisions_found))}")
    assert len(divisions_found) == 8, f"Expected 8 divisions, found {len(divisions_found)}"

    # Check prominent cartel districts
    dhaka_dist = next(d for d in data["districts"] if d["district"] == "Dhaka")
    print(f"[✓] Spot Check: Dhaka District -> Volume: ৳{dhaka_dist['total_volume_cr']} Cr, Integrity: {dhaka_dist['integrity_score']}/100, Tier: {dhaka_dist['threat_tier']}")
    print(f"    Active Syndicates in Dhaka: {dhaka_dist['active_syndicates']}")
    assert len(dhaka_dist["active_syndicates"]) > 0, "Expected active syndicates in Dhaka"

    # 4. Cross-District Collusion Arcs
    print("\n--- 4. Testing Cross-District Syndicate Collusion Arcs (Tentacles) ---")
    arcs = data.get("collusion_arcs", [])
    print(f"[✓] Identified {len(arcs)} cross-district collusion arcs across syndicate rings.")
    assert len(arcs) >= 10, f"Expected at least 10 collusion arcs, got {len(arcs)}"
    sample_arc = arcs[0]
    print(f"    Sample Arc: {sample_arc['source_district']} ↔ {sample_arc['target_district']} ({sample_arc['syndicate']})")
    assert sample_arc["source_district"] != sample_arc["target_district"]

    # 5. Query Filtering: Division Filter
    print("\n--- 5. Testing Division Filter (division=Dhaka) ---")
    dhaka_resp = requests.get(f"{BASE_URL}/api/cartel/district-heatmap?division=Dhaka", headers=headers, timeout=10)
    assert dhaka_resp.status_code == 200
    dhaka_data = dhaka_resp.json()
    assert dhaka_data["total_districts"] == 13, f"Expected 13 districts in Dhaka Division, got {dhaka_data['total_districts']}"
    for d in dhaka_data["districts"]:
        assert d["division"] == "Dhaka", f"Expected Dhaka division, got {d['division']}"
    print(f"[✓] Division filter accurately isolated all 13 districts in Dhaka division.")

    # 6. Query Filtering: Agency Filter
    print("\n--- 6. Testing Agency Filter (agency=Roads and Highways Department (RHD)) ---")
    rhd_resp = requests.get(f"{BASE_URL}/api/cartel/district-heatmap?agency=Roads and Highways Department (RHD)", headers=headers, timeout=10)
    assert rhd_resp.status_code == 200
    rhd_data = rhd_resp.json()
    assert rhd_data["total_packages"] > 0
    print(f"[✓] Agency filter retrieved RHD specific volume: {rhd_data['total_packages']:,} packages (৳{rhd_data['total_volume_cr']:,.2f} Cr)")

    # 7. RBAC Role Security
    print("\n--- 7. Testing RBAC Role Security ---")
    bad_auth_resp = requests.get(f"{BASE_URL}/api/cartel/district-heatmap", headers={"Authorization": "Bearer bad.token.here"}, timeout=10)
    assert bad_auth_resp.status_code == 401, f"Expected 401 for invalid JWT, got {bad_auth_resp.status_code}"
    print(f"[✓] RBAC Guard: Cryptographically invalid token rejected with HTTP 401 Unauthorized.")

    print("\n===========================================================================")
    print(" [✓] ALL 7 GIS HEATMAP VERIFICATION SUITES PASSED (100% OPERATIONAL)")
    print("===========================================================================\n")


if __name__ == "__main__":
    test_district_heatmap()
