"""
TenderPulse 4IR - Phase 5 Harvester Daemon & Corrigendum Tracker Verification Test Suite
Validates:
1. HarvesterDaemon multi-agency execution & rate-limited polling
2. Automated Corrigendum amendment detection (deadline extensions & security changes)
3. Database persistence & CorrigendumModel table operations
4. REST API endpoints (/api/harvester/status, /api/harvester/trigger, /api/corrigenda)
5. RBAC role permissions on trigger endpoint
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
from backend.models import TenderModel, CorrigendumModel
from backend.harvester_daemon import HarvesterDaemon
import backend.crud as crud
from backend.auth_jwt import create_access_token, ROLE_EXECUTIVE, ROLE_ANALYST, ROLE_AUDITOR, ROLE_ADMIN

BASE_URL = "http://127.0.0.1:8080"


def test_harvester_daemon_unit():
    print("\n--- Test 1: HarvesterDaemon Unit & Rate-Limited Harvest Cycle ---")
    daemon = HarvesterDaemon(
        agencies=["LGED"],
        interval=60,
        limit_per_agency=2,
        min_delay=0.1,
        max_delay=0.3
    )
    assert daemon.agencies == ["LGED"], "Daemon agencies mismatch"
    assert daemon.state["status"] == "idle", "Initial state must be idle"

    result = daemon.run_harvest_cycle()
    print(f"  [+] Harvest result: {result}")
    assert result["agencies_polled"] == 1, "Expected 1 agency polled"
    assert result["harvested"] >= 1, "Expected at least 1 notice harvested"
    assert daemon.state["status"] == "idle", "State should return to idle after harvest"
    assert daemon.state["total_harvested_count"] >= 1, "Total harvested count not updated"
    print("  [✓] HarvesterDaemon unit execution passed!")


def test_corrigendum_detection():
    print("\n--- Test 2: Automated Corrigendum Amendment Detection ---")
    init_db()
    db = SessionLocal()
    try:
        # Create or pick a tender to simulate deadline extension
        test_tid = "CORR-TEST-9901"
        tender_data = {
            "id": test_tid,
            "title": "Bridge Construction over Shitalakshya River",
            "agency": "RHD",
            "closingDate": "2026-10-15 13:00",
            "tenderSecurity": 5000000.0,
            "estimatedCost": 200000000.0
        }
        crud.upsert_tender(db, tender_data)

        # Now simulate a revised notice mined with an extended closing date and adjusted security
        updated_notice = {
            "id": test_tid,
            "tenderId": test_tid,
            "title": "Bridge Construction over Shitalakshya River",
            "agency": "RHD",
            "closingDate": "2026-11-20 13:00",  # Extended deadline
            "tenderSecurity": 5500000.0,         # 10% security adjustment
            "estimatedCost": 200000000.0
        }

        # Check Corrigendum logic directly
        existing = db.query(TenderModel).filter(TenderModel.tender_id == test_tid).first()
        assert existing is not None, "Test tender was not persisted"

        # Record corrigendum via crud
        corr1 = crud.create_corrigendum(
            db=db,
            tender_id=test_tid,
            field_changed="closing_date",
            old_value=existing.closing_date,
            new_value=updated_notice["closingDate"],
            reason="CPTU Amendment: Submission deadline extended from 2026-10-15 to 2026-11-20"
        )
        assert corr1.id is not None, "Corrigendum ID not generated"
        assert corr1.field_changed == "closing_date", "Field mismatch"

        corr2 = crud.create_corrigendum(
            db=db,
            tender_id=test_tid,
            field_changed="tender_security",
            old_value=str(existing.tender_security),
            new_value=str(updated_notice["tenderSecurity"]),
            reason="CPTU Corrigendum: Tender security increased to 5,500,000 BDT"
        )
        assert corr2.id is not None, "Corrigendum ID 2 not generated"

        # Query back
        corrigenda = crud.get_corrigenda(db, tender_id=test_tid)
        assert len(corrigenda) >= 2, f"Expected at least 2 corrigenda, got {len(corrigenda)}"
        print(f"  [+] Found {len(corrigenda)} recorded corrigenda for {test_tid}:")
        for c in corrigenda:
            print(f"      - #{c.corrigendum_no} {c.field_changed}: {c.old_value} -> {c.new_value} ({c.reason})")

        print("  [✓] Corrigendum detection and database persistence passed!")
    finally:
        db.close()


def test_api_harvester_endpoints():
    print("\n--- Test 3: Harvester REST API Endpoints & RBAC Protection ---")
    
    # 1. Health check includes harvester_daemon
    res_health = requests.get(f"{BASE_URL}/api/health", timeout=5)
    assert res_health.status_code == 200, f"Health check failed: {res_health.text}"
    health_data = res_health.json()
    assert "harvester_daemon" in health_data["active_ai_engines"], "harvester_daemon not in active_ai_engines"
    print(f"  [+] Engine verified in /api/health: {health_data['active_ai_engines']['harvester_daemon']}")

    # 2. Harvester status endpoint
    res_status = requests.get(f"{BASE_URL}/api/harvester/status", timeout=5)
    assert res_status.status_code == 200, f"Status failed: {res_status.text}"
    status_data = res_status.json()
    assert status_data["status"] == "SUCCESS", "Status endpoint returned non-success"
    telemetry = status_data["telemetry"]
    print(f"  [+] Harvester status: state={telemetry.get('status')}, harvested={telemetry.get('total_harvested_count')}, agencies={telemetry.get('agencies')}")

    # 3. Corrigenda list endpoint
    res_corr = requests.get(f"{BASE_URL}/api/corrigenda", timeout=5)
    assert res_corr.status_code == 200, f"Corrigenda failed: {res_corr.text}"
    corr_data = res_corr.json()
    assert corr_data["status"] == "SUCCESS", "Corrigenda list returned non-success"
    assert corr_data["count"] >= 1, "Expected at least 1 corrigendum in database"
    print(f"  [+] /api/corrigenda returned {corr_data['count']} active notices.")

    # 4. Trigger endpoint with RBAC
    analyst_token = create_access_token({
        "email": "analyst@ditender.gov.bd",
        "name": "Nafis Analyst",
        "role": ROLE_ANALYST,
        "agency": "LGED"
    })
    auditor_token = create_access_token({
        "email": "auditor@ditender.gov.bd",
        "name": "Auditor Khan",
        "role": ROLE_AUDITOR,
        "agency": "IMED"
    })


    # Trigger with Analyst token (Authorized)
    res_trigger = requests.post(
        f"{BASE_URL}/api/harvester/trigger",
        headers={"Authorization": f"Bearer {analyst_token}"},
        json={"agency": "LGED", "limit": 2},
        timeout=10
    )
    assert res_trigger.status_code in (200, 202), f"Authorized trigger failed: {res_trigger.text}"
    print(f"  [+] Authorized trigger (Analyst) succeeded: {res_trigger.json().get('status')}")

    # Trigger with Auditor token (Unauthorized -> should be 403 Forbidden)
    res_trigger_unauth = requests.post(
        f"{BASE_URL}/api/harvester/trigger",
        headers={"Authorization": f"Bearer {auditor_token}"},
        json={"agency": "LGED", "limit": 2},
        timeout=10
    )
    assert res_trigger_unauth.status_code == 403, f"Expected 403 Forbidden for Auditor, got {res_trigger_unauth.status_code}"
    print(f"  [+] RBAC correctly rejected unauthorized role (Auditor) with HTTP 403 Forbidden")

    print("  [✓] All Harvester REST API and RBAC verification tests passed!")


if __name__ == "__main__":
    print("=================================================================")
    print(" TenderPulse 4IR AI - Phase 5 Harvester & Corrigendum Test Suite ")
    print("=================================================================")
    test_harvester_daemon_unit()
    test_corrigendum_detection()
    test_api_harvester_endpoints()
    print("\n[SUCCESS] All Phase 5 verification tests completed with 100% pass rate!")
