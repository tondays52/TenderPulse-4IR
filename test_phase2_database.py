"""
TenderPulse 4IR - Phase 2 Database Persistence & Spatial Indexing Verification Suite
Verifies SQLAlchemy 2.0 ORM models, CRUD transactions, spatial queries, and live API endpoints.
"""

import os
import sys
import json
import requests

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT_DIR)

from backend.database import engine, SessionLocal, init_db
from backend.models import TenderModel, UserModel, BiddingSyndicateModel, SarAuditModel
import backend.crud as crud

API_BASE = "http://127.0.0.1:8080"


def test_database_connection_and_tables():
    print("\n--- 1. Testing Database Connection & ORM Schema ---")
    init_db()
    db = SessionLocal()
    try:
        tender_count = db.query(TenderModel).count()
        user_count = db.query(UserModel).count()
        syndicate_count = db.query(BiddingSyndicateModel).count()
        print(f"  [PASS] Successfully connected to database.")
        print(f"         Tenders: {tender_count} | Users: {user_count} | Syndicates: {syndicate_count}")
        assert tender_count > 0, "Expected at least 1 migrated tender in database"
        assert user_count > 0, "Expected at least 1 migrated user in database"
    finally:
        db.close()


def test_crud_operations():
    print("\n--- 2. Testing CRUD Operations ---")
    db = SessionLocal()
    test_id = "TEST-999999"
    try:
        # Create
        test_payload = {
            "id": test_id,
            "title": "Automated Test Flyover Construction",
            "agency": "RHD",
            "district": "Dhaka",
            "cost": 150000000.0,
            "tenderSecurity": 3750000.0,
            "lat": 23.8103,
            "lng": 90.4125,
            "bbox": [23.75, 90.35, 23.85, 90.45]
        }
        created = crud.upsert_tender(db, test_payload)
        assert created.tender_id == test_id
        print("  [PASS] Inserted test tender record.")

        # Read
        fetched = crud.get_tender_by_id(db, test_id)
        assert fetched is not None
        assert fetched.title == "Automated Test Flyover Construction"
        assert fetched.latitude == 23.8103
        print("  [PASS] Retrieved test tender by ID.")

        # Spatial query
        spatial_results = crud.get_tenders_by_bbox(db, 23.70, 90.30, 23.90, 90.50)
        found_ids = [t.tender_id for t in spatial_results]
        assert test_id in found_ids
        print(f"  [PASS] Spatial BBOX query located test tender within Dhaka envelope ({len(spatial_results)} found).")

        # Delete / Cleanup
        db.delete(fetched)
        db.commit()
        print("  [PASS] Cleaned up test tender record.")
    finally:
        db.close()


def test_live_api_endpoints():
    print("\n--- 3. Testing Live API Endpoints ---")
    # Health check
    resp = requests.get(f"{API_BASE}/api/health", timeout=5)
    assert resp.status_code == 200, f"Health check failed: {resp.status_code}"
    health = resp.json()
    assert health.get("status") == "ONLINE"
    assert health.get("active_ai_engines", {}).get("database") == "SQLAlchemy-2.0-Persisted"
    print("  [PASS] /api/health confirms database engine: SQLAlchemy-2.0-Persisted.")

    # Live tenders from DB
    resp = requests.get(f"{API_BASE}/api/tenders/live?limit=5", timeout=5)
    assert resp.status_code == 200, f"/api/tenders/live failed: {resp.status_code}"
    data = resp.json()
    assert data.get("source") == "database", f"Expected source: database, got {data.get('source')}"
    assert data.get("count") > 0
    print(f"  [PASS] /api/tenders/live successfully served {data.get('count')} records from persistent DB.")

    # Spatial query endpoint
    spatial_req = {
        "bbox": [20.0, 88.0, 27.0, 93.0]
    }
    resp = requests.post(f"{API_BASE}/api/tenders/spatial-query", json=spatial_req, timeout=5)
    assert resp.status_code == 200, f"/api/tenders/spatial-query failed: {resp.status_code}"
    spatial_data = resp.json()
    assert spatial_data.get("status") == "SUCCESS"
    print(f"  [PASS] /api/tenders/spatial-query successfully resolved nationwide bounding box.")


if __name__ == "__main__":
    print("=================================================================")
    print("  TenderPulse 4IR - Phase 2 Database & Spatial Indexing Test Suite")
    print("=================================================================")
    try:
        test_database_connection_and_tables()
        test_crud_operations()
        test_live_api_endpoints()
        print("\n=================================================================")
        print("  ALL PHASE 2 CHECKS PASSED (100% PERSISTENCE READY)")
        print("=================================================================")
    except AssertionError as ae:
        print(f"\n[FAIL] Test assertion failed: {ae}")
        sys.exit(1)
    except Exception as ex:
        print(f"\n[ERROR] Unexpected error: {ex}")
        sys.exit(1)
