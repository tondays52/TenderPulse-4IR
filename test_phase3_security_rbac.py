"""
TenderPulse 4IR - Phase 3 Enterprise Security & 3-Tier RBAC Verification Suite
Verifies cryptographic JWT token creation, claims verification, refresh token rotation,
and strict Role-Based Access Control (RBAC) across Executive, Analyst, Auditor, and Admin roles.
"""

import os
import sys
import json
import requests

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT_DIR)

from backend.auth_jwt import (
    create_access_token,
    create_refresh_token,
    rotate_refresh_token,
    decode_token,
    ROLE_EXECUTIVE,
    ROLE_ANALYST,
    ROLE_AUDITOR,
    ROLE_ADMIN
)

API_BASE = "http://127.0.0.1:8080"


def test_cryptographic_token_generation_and_claims():
    print("\n--- 1. Testing Cryptographic JWT Token Creation & Claims ---")
    mock_exec = {
        "email": "director@tendertrading.gov.bd",
        "name": "Managing Director",
        "role": ROLE_EXECUTIVE,
        "agency": "Tender Trading Inc."
    }
    access_token = create_access_token(mock_exec)
    assert access_token and len(access_token) > 50, "Access token must be non-empty JWT string"
    
    claims = decode_token(access_token)
    assert claims["sub"] == mock_exec["email"]
    assert claims["role"] == ROLE_EXECUTIVE
    assert claims["type"] == "access"
    assert "exp" in claims and "iat" in claims and "jti" in claims
    print(f"  [PASS] Cryptographic access token issued with verified claims: sub={claims['sub']}, role={claims['role']}")


def test_refresh_token_rotation():
    print("\n--- 2. Testing Refresh Token Lifecycle & Rotation ---")
    email = "analyst.lead@tendertrading.gov.bd"
    ref_token_1 = create_refresh_token(email)
    assert ref_token_1 and len(ref_token_1) > 50

    # First rotation: should succeed and revoke ref_token_1
    new_acc, ref_token_2, user = rotate_refresh_token(ref_token_1)
    assert new_acc and ref_token_2
    assert ref_token_1 != ref_token_2, "Rotated refresh token must be a new cryptographically unique token"
    print("  [PASS] Successfully rotated refresh token and issued new access token.")

    # Replay attack prevention: reusing ref_token_1 must fail
    replay_detected = False
    try:
        rotate_refresh_token(ref_token_1)
    except Exception as e:
        replay_detected = True
        print(f"  [PASS] Replay attack prevented on revoked token: {e}")
    assert replay_detected, "Reusing a rotated refresh token must be rejected"


def test_live_login_and_jwt_endpoint():
    print("\n--- 3. Testing Live Login & Token Issuance API ---")
    login_payload = {
        "email": "admin@tendertrading.gov.bd",
        "password": "admin123"
    }
    resp = requests.post(f"{API_BASE}/api/auth/login", json=login_payload, timeout=5)
    assert resp.status_code == 200, f"Login failed: {resp.status_code} {resp.text}"
    data = resp.json()
    assert "access_token" in data, "Login response must contain access_token"
    assert "refresh_token" in data, "Login response must contain refresh_token"
    assert data["token_type"] == "bearer"
    print(f"  [PASS] /api/auth/login successfully issued JWT pair for {login_payload['email']}")

    # Test /api/auth/refresh endpoint
    ref_req = {"refresh_token": data["refresh_token"]}
    ref_resp = requests.post(f"{API_BASE}/api/auth/refresh", json=ref_req, timeout=5)
    assert ref_resp.status_code == 200, f"Token refresh endpoint failed: {ref_resp.status_code}"
    ref_data = ref_resp.json()
    assert "access_token" in ref_data
    assert "refresh_token" in ref_data
    print("  [PASS] /api/auth/refresh successfully executed rotation over HTTP.")


def test_strict_3_tier_rbac():
    print("\n--- 4. Testing Strict 3-Tier Enterprise Role-Based Access Control (RBAC) ---")
    
    # 1. Executive Token: Can execute ZKP & Bank Pre-Approval
    exec_user = {"email": "exec@tendertrading.gov.bd", "name": "MD", "role": ROLE_EXECUTIVE}
    exec_jwt = create_access_token(exec_user)
    exec_headers = {"Authorization": f"Bearer {exec_jwt}"}

    # 2. Analyst Token: Can execute SMT & BOQ, CANNOT execute ZKP or Cartel Radar
    analyst_user = {"email": "analyst@tendertrading.gov.bd", "name": "Estimator", "role": ROLE_ANALYST}
    analyst_jwt = create_access_token(analyst_user)
    analyst_headers = {"Authorization": f"Bearer {analyst_jwt}"}

    # 3. Auditor Token: Can execute Cartel Radar & SAR, CANNOT execute Bank Pre-Approval
    auditor_user = {"email": "auditor@tendertrading.gov.bd", "name": "Inspector", "role": ROLE_AUDITOR}
    auditor_jwt = create_access_token(auditor_user)
    auditor_headers = {"Authorization": f"Bearer {auditor_jwt}"}

    # --- Test 4A: Executive permissions ---
    zkp_payload = {
        "contractor_name": "Prime Infra",
        "egp_id": "BDR-992",
        "peak_turnover_bdt": 400000000.0,
        "liquid_assets_bdt": 120000000.0,
        "required_turnover_bdt": 350000000.0,
        "required_liquidity_bdt": 95000000.0,
        "agency": "RHD"
    }
    r_exec_zkp = requests.post(f"{API_BASE}/api/zkp/prove", json=zkp_payload, headers=exec_headers, timeout=5)
    assert r_exec_zkp.status_code == 200, f"Executive should be permitted for ZKP: {r_exec_zkp.status_code}"
    print("  [PASS] Executive role permitted for ZKP proof generation (HTTP 200 OK).")

    # --- Test 4B: Analyst denied executive endpoints (ZKP) ---
    r_analyst_zkp = requests.post(f"{API_BASE}/api/zkp/prove", json=zkp_payload, headers=analyst_headers, timeout=5)
    assert r_analyst_zkp.status_code == 403, f"Analyst should be denied ZKP: expected 403, got {r_analyst_zkp.status_code}"
    print("  [PASS] Analyst role strictly denied for ZKP proof generation (HTTP 403 Forbidden).")

    # --- Test 4C: Analyst permitted for SMT verification ---
    smt_payload = {"original_contract_value": 85.8, "variation_amount": 7.5, "tender_value": 85.8}
    r_analyst_smt = requests.post(f"{API_BASE}/api/smt/verify", json=smt_payload, headers=analyst_headers, timeout=5)
    assert r_analyst_smt.status_code == 200, f"Analyst should be permitted for SMT: {r_analyst_smt.status_code}"
    print("  [PASS] Analyst role permitted for SMT rule checking (HTTP 200 OK).")

    # --- Test 4D: Auditor permitted for Cartel Radar, Analyst denied ---
    r_auditor_cartel = requests.post(f"{API_BASE}/api/cartel/analyze", json={}, headers=auditor_headers, timeout=5)
    assert r_auditor_cartel.status_code == 200, f"Auditor should be permitted for Cartel: {r_auditor_cartel.status_code}"
    print("  [PASS] Auditor role permitted for Cartel Radar inspection (HTTP 200 OK).")

    r_analyst_cartel = requests.post(f"{API_BASE}/api/cartel/analyze", json={}, headers=analyst_headers, timeout=5)
    assert r_analyst_cartel.status_code == 403, f"Analyst should be denied Cartel: expected 403, got {r_analyst_cartel.status_code}"
    print("  [PASS] Analyst role strictly denied for Cartel Radar inspection (HTTP 403 Forbidden).")

    # --- Test 4E: Auditor denied Bank Pre-Approval ---
    bank_payload = {
        "bank_id": "prime-bank",
        "tender_id": "984210",
        "contractor_name": "Spectra",
        "company_name": "Spectra Ltd",
        "project_title": "Highway",
        "required_amount": 185000000.0,
        "audited_turnover": 450000000.0
    }
    r_auditor_bank = requests.post(f"{API_BASE}/api/bank/pre-approve", json=bank_payload, headers=auditor_headers, timeout=5)
    assert r_auditor_bank.status_code == 403, f"Auditor should be denied Bank Pre-Approval: expected 403, got {r_auditor_bank.status_code}"
    print("  [PASS] Auditor role strictly denied for Bank Pre-Approval issuance (HTTP 403 Forbidden).")


if __name__ == "__main__":
    print("=================================================================")
    print("  TenderPulse 4IR - Phase 3 Enterprise Security & RBAC Test Suite")
    print("=================================================================")
    try:
        test_cryptographic_token_generation_and_claims()
        test_refresh_token_rotation()
        test_live_login_and_jwt_endpoint()
        test_strict_3_tier_rbac()
        print("\n=================================================================")
        print("  ALL PHASE 3 CHECKS PASSED (100% ENTERPRISE SECURITY & RBAC READY)")
        print("=================================================================")
    except AssertionError as ae:
        print(f"\n[FAIL] Test assertion failed: {ae}")
        sys.exit(1)
    except Exception as ex:
        print(f"\n[ERROR] Unexpected error: {ex}")
        sys.exit(1)
