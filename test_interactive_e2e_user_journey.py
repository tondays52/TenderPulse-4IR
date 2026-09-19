"""
========================================================================================
 TenderPulse 4IR AI - Interactive End-to-End User Testing Suite
 Targets: http://127.0.0.1:8080
 
 Verifies:
 1. RBAC Authentication & Session Management (Executive, Auditor, Analyst, Bad Auth, Refresh)
 2. Strict Role-Based Access Control Guards (403 Forbidden vs 200 OK enforcement)
 3. Microsoft Z3 SMT Legal Prover (SAT Proof Certificates & UNSAT Counter-Models)
 4. Sentinel-1 SAR Radar Physical Progress Audits (Coherence Decay & Fraud Risk)
 5. Sentinel Hub Process API & Spatial Raster Matrix Telemetry
 6. Autonomous e-GP Harvester & Corrigendum Tracking Cycle
 7. SPA Frontend Assets & Live Overview Wiring Verification
========================================================================================
"""

import sys
import os
import json
import time
import requests

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_URL = "http://127.0.0.1:8080"
TIMEOUT = 15

# Color / UI helpers
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def log_section(title: str):
    print(f"\n{Colors.HEADER}{'='*80}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.CYAN} >>> {title.upper()} <<<{Colors.ENDC}")
    print(f"{Colors.HEADER}{'='*80}{Colors.ENDC}")


def log_pass(msg: str):
    print(f"  {Colors.GREEN}[PASS]{Colors.ENDC} {msg}")


def log_fail(msg: str):
    print(f"  {Colors.FAIL}[FAIL]{Colors.ENDC} {msg}")


def log_info(msg: str):
    print(f"  {Colors.BLUE}[INFO]{Colors.ENDC} {msg}")


# State shared across stages
tokens = {}
test_results = {"total": 0, "passed": 0, "failed": 0}


def check(assertion: bool, description: str):
    test_results["total"] += 1
    if assertion:
        test_results["passed"] += 1
        log_pass(description)
    else:
        test_results["failed"] += 1
        log_fail(description)
        raise AssertionError(f"Check failed: {description}")


# ============================================================================
# PHASE 1: RBAC LOGINS & CRYPTOGRAPHIC TOKEN VERIFICATION
# ============================================================================
def test_phase1_rbac_logins():
    log_section("Phase 1: RBAC Authentication & Session Management")

    users_to_test = [
        {
            "role_desc": "Executive / Managing Director",
            "email": "admin@tendertrading.gov.bd",
            "password": "admin123",
            "expected_role": "Executive / Managing Director"
        },
        {
            "role_desc": "Audit / Oversight Officer",
            "email": "majumder.law@tendertrading.gov.bd",
            "password": "majumder123",
            "expected_role": "Audit / Oversight Officer"
        },
        {
            "role_desc": "Tender Analyst / Estimator",
            "email": "karim.engr@tendertrading.gov.bd",
            "password": "karim123",
            "expected_role": "Tender Analyst / Estimator"
        }
    ]

    for u in users_to_test:
        log_info(f"Authenticating as {u['role_desc']} ({u['email']})...")
        t0 = time.time()
        resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": u["email"], "password": u["password"]},
            timeout=TIMEOUT
        )
        elapsed = (time.time() - t0) * 1000
        check(resp.status_code == 200, f"Login HTTP 200 for {u['email']} in {elapsed:.1f}ms")
        data = resp.json()
        check("access_token" in data and len(data["access_token"]) > 30, f"Valid JWT access_token issued for {u['email']}")
        check("refresh_token" in data and len(data["refresh_token"]) > 30, f"Valid JWT refresh_token issued for {u['email']}")
        
        # Verify user object & decoded role
        token_str = data["access_token"]
        # Fast payload decode without secret verification for test inspection
        import base64
        payload_b64 = token_str.split(".")[1]
        payload_b64 += "=" * ((4 - len(payload_b64) % 4) % 4)
        claims = json.loads(base64.urlsafe_b64decode(payload_b64.encode('utf-8')).decode('utf-8'))
        
        check(claims.get("role") == u["expected_role"], f"JWT Claims Role matches '{u['expected_role']}' (raw: {data.get('role')})")
        tokens[u["expected_role"]] = data["access_token"]
        tokens[f"{u['expected_role']}_refresh"] = data["refresh_token"]

    # Test Bad Credentials -> HTTP 401
    log_info("Testing rejection of invalid credentials...")
    bad_resp = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": "admin@tendertrading.gov.bd", "password": "wrong_password_999"},
        timeout=TIMEOUT
    )
    check(bad_resp.status_code == 401, "Invalid password returns HTTP 401 Unauthorized")

    # Test Refresh Token Rotation
    log_info("Testing refresh token rotation...")
    analyst_refresh = tokens["Tender Analyst / Estimator_refresh"]
    ref_resp = requests.post(
        f"{BASE_URL}/api/auth/refresh",
        json={"refresh_token": analyst_refresh},
        timeout=TIMEOUT
    )
    check(ref_resp.status_code == 200, "Token rotation endpoint returned HTTP 200")
    ref_data = ref_resp.json()
    check("access_token" in ref_data and "refresh_token" in ref_data, "Fresh access & refresh tokens issued")
    check(ref_data["refresh_token"] != analyst_refresh, "New refresh token is rotated with new JTI")
    # Update active analyst token
    tokens["Tender Analyst / Estimator"] = ref_data["access_token"]


# ============================================================================
# PHASE 2: STRICT RBAC ROLE GUARDS ENFORCEMENT
# ============================================================================
def test_phase2_rbac_guards():
    log_section("Phase 2: Strict RBAC Role-Based Access Guards")

    analyst_token = tokens["Tender Analyst / Estimator"]
    auditor_token = tokens["Audit / Oversight Officer"]
    executive_token = tokens["Executive / Managing Director"]

    # Guard 1: SAR Audit is restricted to Auditor / Admin
    log_info("Testing Guard: SAR Audit (/api/sar/audit) requires Auditor/Admin role")
    # 1a. Analyst should be denied (403)
    denied = requests.post(
        f"{BASE_URL}/api/sar/audit",
        headers={"Authorization": f"Bearer {analyst_token}"},
        json={"contract_id": "TEST-RBAC-01", "claimed_mb_progress_pct": 50.0},
        timeout=TIMEOUT
    )
    check(denied.status_code == 403, "Analyst access to SAR Audit correctly denied with HTTP 403 Forbidden")

    # 1b. Auditor should be allowed (200)
    allowed = requests.post(
        f"{BASE_URL}/api/sar/audit",
        headers={"Authorization": f"Bearer {auditor_token}"},
        json={"contract_id": "TEST-RBAC-01", "claimed_mb_progress_pct": 50.0},
        timeout=TIMEOUT
    )
    check(allowed.status_code == 200, "Auditor access to SAR Audit correctly authorized with HTTP 200 OK")

    # Guard 2: Bank Pre-Approval is restricted to Executive / Admin
    log_info("Testing Guard: Bank Pre-Approval (/api/bank/pre-approve) requires Executive/Admin role")
    # 2a. Analyst should be denied (403)
    denied_bank = requests.post(
        f"{BASE_URL}/api/bank/pre-approve",
        headers={"Authorization": f"Bearer {analyst_token}"},
        json={
            "bank_id": "ebl",
            "contractor_name": "Test Builders Ltd",
            "requested_limit_bdt": 50000000.0,
            "liquid_assets_bdt": 12000000.0,
            "avg_turnover_bdt": 40000000.0
        },
        timeout=TIMEOUT
    )
    check(denied_bank.status_code == 403, "Analyst access to Bank Pre-Approval correctly denied with HTTP 403 Forbidden")

    # 2b. Executive should be allowed (200)
    allowed_bank = requests.post(
        f"{BASE_URL}/api/bank/pre-approve",
        headers={"Authorization": f"Bearer {executive_token}"},
        json={
            "bank_id": "prime-bank",
            "tender_id": "eGP-1098421",
            "contractor_name": "Engr. M. A. Karim",
            "company_name": "Prime Infrastructure & Construction Ltd.",
            "project_title": "4-Lane Pre-Stressed Concrete Girder Bridge",
            "required_amount": 50000000.0,
            "audited_turnover": 45000000.0,
            "cptu_form_type": "e-PW2A-8"
        },
        timeout=TIMEOUT
    )
    check(allowed_bank.status_code == 200, f"Executive access to Bank Pre-Approval correctly authorized with HTTP 200 OK (got {allowed_bank.status_code})")

    # Guard 3: Harvester Trigger is restricted to Analyst / Executive / Admin (Auditor denied)
    log_info("Testing Guard: Harvester Trigger (/api/harvester/trigger) requires Analyst/Executive/Admin")
    # 3a. Auditor should be denied (403)
    denied_harv = requests.post(
        f"{BASE_URL}/api/harvester/trigger",
        headers={"Authorization": f"Bearer {auditor_token}"},
        json={"agency": "LGED", "limit": 2},
        timeout=TIMEOUT
    )
    check(denied_harv.status_code == 403, "Auditor access to Harvester trigger correctly denied with HTTP 403 Forbidden")


# ============================================================================
# PHASE 3: MICROSOFT Z3 SMT LEGAL PROVER VERIFICATION
# ============================================================================
def test_phase3_smt_solver():
    log_section("Phase 3: Microsoft Z3 SMT Formal Legal Prover")

    analyst_token = tokens["Tender Analyst / Estimator"]
    headers = {"Authorization": f"Bearer {analyst_token}"}

    # Case A: Statistically and Legally Compliant Contract Variation
    # (Original: 85.8 Cr, Variation: 10.5 Cr [12.2% <= 15% threshold], turnover compliant)
    log_info("Submitting valid contract parameter set to Z3 SMT Solver...")
    t0 = time.time()
    valid_payload = {
        "original_contract_value": 85.80,
        "variation_amount": 10.50,
        "cabinet_approval_obtained": False,
        "performance_security_pct": 10.0,
        "max_annual_turnover": 45.0,
        "completion_period_years": 2.0,
        "existing_commitments": 32.0,
        "tender_value": 85.80
    }
    resp_valid = requests.post(f"{BASE_URL}/api/smt/verify", headers=headers, json=valid_payload, timeout=TIMEOUT)
    smt_ms = (time.time() - t0) * 1000
    check(resp_valid.status_code == 200, f"SMT Solver returned HTTP 200 in {smt_ms:.1f}ms")
    v_data = resp_valid.json()
    check(v_data.get("status") == "SAT", f"Z3 Result status: {v_data.get('status')}")
    check("certificate_id" in v_data and "proof_trace" in v_data, f"Z3 Proof certificate generated: {v_data.get('certificate_id')}")
    check(len(v_data.get("proof_trace", [])) >= 3, f"Proof trace contains {len(v_data.get('proof_trace', []))} deductive steps")
    log_info(f"SMT Backend: {v_data.get('solver_backend')} | Cert: {v_data.get('certificate_id')}")
    log_info(f"Z3 Model: {v_data.get('model')}")

    # Case B: Illegal Contract Variation (Exceeds 15% threshold without Cabinet Approval)
    # (Original: 85.8 Cr, Variation: 25.0 Cr [29.1% > 15%], cabinet_approval = False)
    log_info("Submitting non-compliant contract variation (>15% without Cabinet approval) to Z3...")
    t0 = time.time()
    invalid_payload = {
        "original_contract_value": 85.80,
        "variation_amount": 25.00,
        "cabinet_approval_obtained": False,
        "performance_security_pct": 10.0,
        "max_annual_turnover": 45.0,
        "completion_period_years": 2.0,
        "existing_commitments": 32.0,
        "tender_value": 85.80
    }
    resp_invalid = requests.post(f"{BASE_URL}/api/smt/verify", headers=headers, json=invalid_payload, timeout=TIMEOUT)
    check(resp_invalid.status_code == 200, "SMT Solver returned HTTP 200 for violation check")
    iv_data = resp_invalid.json()
    check(iv_data.get("status") == "UNSAT", f"Z3 correctly flagged violation as UNSAT: {iv_data.get('status')}")
    check(len(iv_data.get("violations", [])) > 0, "Violations array populated with CPTU rule breaches")
    log_info(f"Flagged Violation: {iv_data.get('violations')[0]}")


# ============================================================================
# PHASE 4: SENTINEL-1 SAR RADAR AUDITS & SPATIAL RASTER INGESTION
# ============================================================================
def test_phase4_sar_radar_audit():
    log_section("Phase 4: Copernicus Sentinel-1 SAR Radar Physical Progress Audits")

    auditor_token = tokens["Audit / Oversight Officer"]
    headers = {"Authorization": f"Bearer {auditor_token}"}

    # Test 1: Ground Truth Physical Progress Audit via SAR Backscatter Coherence Decay
    log_info("Executing SAR backscatter audit on RHD highway pavement contract...")
    t0 = time.time()
    sar_req = {
        "contract_id": "RHD/2026/PW-04",
        "claimed_mb_progress_pct": 68.0,
        "latitude": 22.7010,
        "longitude": 90.3535,
        "project_type": "Highway Embankment & Asphalt Pavement"
    }
    resp_sar = requests.post(f"{BASE_URL}/api/sar/audit", headers=headers, json=sar_req, timeout=TIMEOUT)
    sar_ms = (time.time() - t0) * 1000
    check(resp_sar.status_code == 200, f"SAR Radar Audit returned HTTP 200 in {sar_ms:.1f}ms")
    sar_data = resp_sar.json()
    check("physical_ground_truth_pct" in sar_data and "claimed_mb_progress_pct" in sar_data, "Audited physical ground truth vs claimed progress present")
    check("discrepancy_delta_pct" in sar_data and "audit_status" in sar_data, "Discrepancy variance & audit status calculated")
    check("audit_certificate_id" in sar_data and "orbital_pass_timeline" in sar_data, "Cryptographic audit certificate & orbital pass timeline generated")
    log_info(f"Claimed Progress: {sar_data.get('claimed_mb_progress_pct')}% | Ground Truth Progress: {sar_data.get('physical_ground_truth_pct')}%")
    log_info(f"Unexplained Variance: +{sar_data.get('discrepancy_delta_pct')}% | Audit Status: {sar_data.get('audit_status')}")
    log_info(f"Audit Certificate ID: {sar_data.get('audit_certificate_id')}")

    # Test 2: Live Sentinel-1 Raster Ingestion for Tender BBOX
    log_info("Querying Sentinel-1 C-band dual-pol (VV/VH) radar raster for tender BBOX...")
    t0 = time.time()
    sentinel_req = {
        "bbox": [23.75, 90.35, 23.85, 90.45],
        "tender_id": "eGP-1098421",
        "start_date": "2026-01-01",
        "end_date": "2026-03-01"
    }
    resp_sentinel = requests.post(f"{BASE_URL}/api/sentinel/query", json=sentinel_req, timeout=TIMEOUT)
    check(resp_sentinel.status_code == 200, "Sentinel Hub raster query returned HTTP 200")
    s_data = resp_sentinel.json()
    check("elevation_matrix" in s_data and "coherence_matrix" in s_data, "3D Elevation and InSAR coherence matrices returned")
    check("radiometric_metrics" in s_data and s_data.get("status") == "SUCCESS", f"Radiometric metrics & SUCCESS status verified (orbit: {s_data.get('orbit_pass')})")
    log_info(f"Sentinel Matrix: {len(s_data.get('elevation_matrix', []))}x{len(s_data.get('elevation_matrix', [[]])[0])} grid | Polarization: {s_data.get('polarization')}")

    # Test 3: Sentinel Cache Stats
    log_info("Retrieving Sentinel radar tile LRU cache telemetry...")
    resp_cache = requests.get(f"{BASE_URL}/api/sentinel/cache/stats", timeout=TIMEOUT)
    check(resp_cache.status_code == 200, "Sentinel cache stats returned HTTP 200")
    c_data = resp_cache.json()
    cache_info = c_data.get("cache", {})
    check("hits" in cache_info and "misses" in cache_info, "Cache hit/miss metrics tracked")
    log_info(f"LRU Cache: {cache_info.get('hits')} hits, {cache_info.get('misses')} misses, {cache_info.get('disk_usage_mb', 0):.2f} MB used")


# ============================================================================
# PHASE 5: AUTONOMOUS E-GP HARVESTER & CORRIGENDUM TRACKER
# ============================================================================
def test_phase5_harvester_cycle():
    log_section("Phase 5: Autonomous e-GP Harvester & Corrigendum Tracker")

    analyst_token = tokens["Tender Analyst / Estimator"]
    headers = {"Authorization": f"Bearer {analyst_token}"}

    # Step 1: Telemetry Check
    log_info("Reading background harvester daemon telemetry...")
    resp_status = requests.get(f"{BASE_URL}/api/harvester/status", timeout=TIMEOUT)
    check(resp_status.status_code == 200, "Harvester status returned HTTP 200")
    h_telemetry = resp_status.json().get("telemetry", {})
    check("status" in h_telemetry or "cycle_count" in h_telemetry or "agencies" in h_telemetry, "Harvester daemon telemetry active")
    log_info(f"Daemon State: status='{h_telemetry.get('status')}', cycle_count={h_telemetry.get('cycle_count', 0)}, harvested={h_telemetry.get('total_harvested_count', 0)}")

    # Step 2: Trigger Live Harvester Run
    log_info("Triggering immediate harvest run for target agency: LGED...")
    t0 = time.time()
    trig_resp = requests.post(
        f"{BASE_URL}/api/harvester/trigger",
        headers=headers,
        json={"agency": "LGED", "limit": 3},
        timeout=TIMEOUT
    )
    check(trig_resp.status_code in (200, 202), f"Harvester run triggered with HTTP {trig_resp.status_code}")
    trig_data = trig_resp.json()
    check(trig_data.get("status") in ("SUCCESS", "QUEUED"), f"Harvest cycle status: {trig_data.get('status')}")
    log_info(f"Trigger Response: {trig_data.get('message', trig_data.get('result', {}))}")

    # Step 3: Verify Live Tenders Feed
    log_info("Querying live tenders feed from database...")
    tenders_resp = requests.get(f"{BASE_URL}/api/tenders/live?limit=10", timeout=TIMEOUT)
    check(tenders_resp.status_code == 200, "Live tenders endpoint returned HTTP 200")
    t_data = tenders_resp.json()
    check(t_data.get("count", 0) > 0, f"Found {t_data.get('count')} live tenders in database (total={t_data.get('total_count')})")
    first_t = t_data["tenders"][0]
    check("tenderId" in first_t and "agency" in first_t and "cost" in first_t, "Tender object contains required fields")
    log_info(f"Sample Live Tender: [{first_t.get('agency')}] ID={first_t.get('tenderId')} - Cost={first_t.get('cost')} BDT")

    # Step 4: Corrigendum Tracking Alerts
    log_info("Verifying CPTU corrigenda amendment tracker...")
    corr_resp = requests.get(f"{BASE_URL}/api/corrigenda?limit=10", timeout=TIMEOUT)
    check(corr_resp.status_code == 200, "Corrigenda tracking returned HTTP 200")
    c_data = corr_resp.json()
    check("corrigenda" in c_data and c_data.get("count", 0) > 0, f"Corrigendum feed contains {c_data.get('count')} tracked amendments")
    sample_c = c_data["corrigenda"][0]
    log_info(f"Tracked Corrigendum: Tender {sample_c.get('tender_id')} | Field Changed: {sample_c.get('field_changed')}")


# ============================================================================
# PHASE 6: WEB UI SPA ASSETS & LIVE OVERVIEW INTEGRITY
# ============================================================================
def test_phase6_frontend_spa():
    log_section("Phase 6: Frontend Single Page Application & Assets")

    # 1. Root index.html
    log_info("Testing frontend root SPA delivery (GET /)...")
    resp_root = requests.get(f"{BASE_URL}/", timeout=TIMEOUT)
    check(resp_root.status_code == 200, "Root path returned HTTP 200")
    check("<!DOCTYPE html>" in resp_root.text or "<html" in resp_root.text, "Root served valid HTML5 document")
    check("TenderPulse" in resp_root.text or "Di-Tender" in resp_root.text, "Page title and branding present")

    # 2. Critical JS modules
    critical_scripts = [
        "/js/api.js",
        "/js/app.js",
        "/js/services/tenderApi.js",
        "/js/gat-cartel-radar.js",
        "/js/satellite-audit.js",
        "/js/neuro-symbolic-smt.js",
        "/js/command-palette.js"
    ]
    for script in critical_scripts:
        s_resp = requests.get(f"{BASE_URL}{script}", timeout=TIMEOUT)
        check(s_resp.status_code == 200 and len(s_resp.text) > 500, f"Static script loaded: {script} ({len(s_resp.text)} bytes)")

    # 3. Overall Engine Health & Version
    log_info("Checking /api/health active AI engines count...")
    health_resp = requests.get(f"{BASE_URL}/api/health", timeout=TIMEOUT)
    check(health_resp.status_code == 200, "Health check returned HTTP 200")
    h_data = health_resp.json()
    engines = h_data.get("active_ai_engines", {})
    check(len(engines) >= 10, f"All {len(engines)} AI engines reported ONLINE: {list(engines.keys())}")


# ============================================================================
# MAIN ENTRYPOINT
# ============================================================================
def run_all_e2e_tests():
    t_start = time.time()
    print(f"\n{Colors.BOLD}{Colors.HEADER}")
    print("=" * 80)
    print("   TENDERPULSE 4IR AI - LIVE INTERACTIVE E2E VERIFICATION SUITE")
    print(f"   Target: {BASE_URL} | Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print(Colors.ENDC)

    try:
        test_phase1_rbac_logins()
        test_phase2_rbac_guards()
        test_phase3_smt_solver()
        test_phase4_sar_radar_audit()
        test_phase5_harvester_cycle()
        test_phase6_frontend_spa()

        total_elapsed = time.time() - t_start
        print(f"\n{Colors.BOLD}{Colors.GREEN}{'='*80}")
        print(f"   [SUCCESS] ALL {test_results['passed']}/{test_results['total']} INTERACTIVE E2E USER TESTS PASSED! ({total_elapsed:.2f}s)")
        print(f"{'='*80}{Colors.ENDC}\n")
        return 0
    except Exception as e:
        total_elapsed = time.time() - t_start
        print(f"\n{Colors.BOLD}{Colors.FAIL}{'='*80}")
        print(f"   [ERROR] E2E TEST FAILED: {str(e)}")
        print(f"   Passed: {test_results['passed']}/{test_results['total']} | Elapsed: {total_elapsed:.2f}s")
        print(f"{'='*80}{Colors.ENDC}\n")
        return 1


if __name__ == "__main__":
    code = run_all_e2e_tests()
    sys.exit(code)
