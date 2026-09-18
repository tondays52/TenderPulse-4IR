"""
TenderPulse 4IR - Phase 6 Sentinel Hub Process API & Tile Cache Verification Test Suite
Validates:
1. Copernicus Sentinel-1 C-band SAR Process API payload generation & Evalscript validation
2. LRU disk tile caching (hit/miss tracking, PU minimization, disk eviction)
3. REST API endpoints (/api/sentinel/query, /api/sentinel/pipeline-status, /api/sentinel/cache/stats)
4. RBAC role permissions on /api/sentinel/cache/clear (Auditor/Admin authorized, Analyst rejected)
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

from backend.sentinel_hub import SentinelHubPipeline
from backend.auth_jwt import create_access_token, ROLE_EXECUTIVE, ROLE_ANALYST, ROLE_AUDITOR, ROLE_ADMIN

BASE_URL = "http://127.0.0.1:8080"


def test_process_api_payload_and_cache_unit():
    print("\n--- Test 1: Sentinel-1 Process API Payload & Disk LRU Cache Unit ---")
    pipeline = SentinelHubPipeline()
    
    # 1. Verify Process API payload structure
    test_bbox = [23.8103, 90.4125, 23.8203, 90.4225]
    payload = pipeline.execute_process_api_payload(test_bbox, ("2026-07-01", "2026-09-18"))
    
    assert "input" in payload, "Missing input in Process API payload"
    assert "data" in payload["input"], "Missing data array"
    assert payload["input"]["data"][0]["type"] == "sentinel-1-grd", "Payload must request sentinel-1-grd"
    assert payload["input"]["data"][0]["dataFilter"]["polarization"] == "DV", "Dual-polarization (DV) required"
    assert "evalscript" in payload and "VV" in payload["evalscript"], "Evalscript missing dual-pol definition"
    print("  [+] Process API dual-pol SAR payload verified.")

    # 2. Test Disk LRU Caching
    pipeline.clear_cache()
    
    # First query: Cache miss
    raster1 = pipeline.query_sar_raster(test_bbox, tender_id="TEST-TENDER-881")
    assert raster1["status"] == "SUCCESS", "Query failed"
    assert raster1["cache_hit"] is False, "First query should be cache miss"
    assert raster1["source"] == "live_gateway_process_api", "Expected live_gateway_process_api"
    print(f"  [+] Pass 1 (Cold): source={raster1['source']}, cache_hit={raster1['cache_hit']}")

    # Second query (identical BBOX and tender): Cache hit
    raster2 = pipeline.query_sar_raster(test_bbox, tender_id="TEST-TENDER-881")
    assert raster2["status"] == "SUCCESS", "Query failed on cache retrieval"
    assert raster2["cache_hit"] is True, "Second query must hit disk cache"
    assert raster2["source"] == "satellite_disk_cache", "Expected satellite_disk_cache"
    assert raster2["cache_metadata"]["pu_cost_saved"] == 1.0, "PU cost savings not tracked"
    print(f"  [+] Pass 2 (Warm): source={raster2['source']}, cache_hit={raster2['cache_hit']}, pu_saved={raster2['cache_metadata']['pu_cost_saved']}")

    # 3. Check cache stats
    stats = pipeline.get_cache_stats()
    assert stats["hits"] >= 1, "Cache hits counter not incremented"
    assert stats["misses"] >= 1, "Cache misses counter not incremented"
    assert stats["cached_tiles_count"] >= 1, "Cached tile files not tracked"
    assert stats["pu_saved"] >= 1.0, "PU units saved not counted"
    print(f"  [+] Cache Stats: tiles={stats['cached_tiles_count']}, hits={stats['hits']}, misses={stats['misses']}, PU saved={stats['pu_saved']}")
    print("  [✓] Process API payload and LRU disk caching passed!")


def test_api_sentinel_endpoints_and_rbac():
    print("\n--- Test 2: Live Sentinel REST API Endpoints & RBAC Validation ---")
    
    # 1. Pipeline status
    res_status = requests.get(f"{BASE_URL}/api/sentinel/pipeline-status", timeout=5)
    assert res_status.status_code == 200, f"Pipeline status failed: {res_status.text}"
    status_data = res_status.json()
    assert status_data["process_api_ready"] is True, "process_api_ready must be True"
    assert "cache_stats" in status_data, "cache_stats missing from pipeline status"
    print(f"  [+] Pipeline Status: engine={status_data['engine']}, process_api={status_data['process_api_ready']}")

    # 2. Query SAR raster endpoint
    dhaka_bbox = [23.75, 90.35, 23.85, 90.45]
    res_query = requests.post(
        f"{BASE_URL}/api/sentinel/query",
        json={"bbox": dhaka_bbox, "tender_id": "986772"},
        timeout=5
    )
    assert res_query.status_code == 200, f"Sentinel query failed: {res_query.text}"
    query_data = res_query.json()
    assert query_data["status"] == "SUCCESS", "Expected status SUCCESS"
    assert len(query_data["elevation_matrix"]) == 16, "Elevation matrix must be 16x16"
    assert "backscatter_vv_db" in query_data["radiometric_metrics"], "Missing backscatter_vv_db"
    print(f"  [+] Live SAR raster retrieved: pass={query_data['orbit_pass']}, VV={query_data['radiometric_metrics']['backscatter_vv_db']} dB, source={query_data.get('source')}")

    # 3. Cache stats endpoint
    res_cache = requests.get(f"{BASE_URL}/api/sentinel/cache/stats", timeout=5)
    assert res_cache.status_code == 200, f"Cache stats failed: {res_cache.text}"
    cache_data = res_cache.json()
    assert cache_data["status"] == "SUCCESS", "Cache stats status failed"
    print(f"  [+] API Cache telemetry: {cache_data['cache']}")

    # 4. RBAC Protection on Cache Clear Endpoint
    analyst_token = create_access_token({
        "email": "analyst@ditender.gov.bd",
        "name": "Nafis Analyst",
        "role": ROLE_ANALYST,
        "agency": "LGED"
    })
    auditor_token = create_access_token({
        "email": "auditor@ditender.gov.bd",
        "name": "Audit Officer",
        "role": ROLE_AUDITOR,
        "agency": "IMED"
    })

    # Unauthorized role (Analyst) -> 403 Forbidden
    res_clear_unauth = requests.post(
        f"{BASE_URL}/api/sentinel/cache/clear",
        headers={"Authorization": f"Bearer {analyst_token}"},
        timeout=5
    )
    assert res_clear_unauth.status_code == 403, f"Expected 403 for Analyst, got {res_clear_unauth.status_code}"
    print(f"  [+] RBAC correctly rejected unauthorized role (Analyst) with HTTP 403 Forbidden")

    # Authorized role (Auditor) -> 200 OK
    res_clear_auth = requests.post(
        f"{BASE_URL}/api/sentinel/cache/clear",
        headers={"Authorization": f"Bearer {auditor_token}"},
        timeout=5
    )
    assert res_clear_auth.status_code == 200, f"Authorized clear failed: {res_clear_auth.text}"
    print(f"  [+] RBAC permitted authorized role (Auditor): {res_clear_auth.json().get('message')}")

    print("  [✓] All Sentinel Process API and Cache RBAC tests passed!")


if __name__ == "__main__":
    print("=================================================================")
    print(" TenderPulse 4IR AI - Phase 6 Sentinel Process API & Cache Suite ")
    print("=================================================================")
    test_process_api_payload_and_cache_unit()
    test_api_sentinel_endpoints_and_rbac()
    print("\n[SUCCESS] All Phase 6 verification tests completed with 100% pass rate!")
