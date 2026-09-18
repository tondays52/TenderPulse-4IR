"""
TenderPulse 4IR AI - Z3 SMT Solver & TDS Legal Proof Engine Test Suite
Tests formal first-order logic verification, CPTU PPR 2008 statutory constraints,
Rule 39/40 variations, e-PW3-8 security, financial capacity invariants, and backend/frontend wiring.
"""

import sys
import os
import json
import urllib.request
import urllib.error

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT_DIR)

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from backend.smt_solver import CptuLegalProver

BASE_URL = "http://127.0.0.1:8080"


def test_smt_solver_unit():
    print("\n--- 1. Testing CptuLegalProver Unit Logic & Z3 Constraints ---")
    prover = CptuLegalProver()

    # Case 1: Fully Compliant Standard Case (SAT)
    res1 = prover.verify_contract_compliance({
        "original_contract_value": 85.80,
        "variation_amount": 10.50, # 12.24% (<= 15%)
        "cabinet_approval_obtained": False,
        "performance_security_pct": 10.0, # >= 10%
        "max_annual_turnover": 45.0,
        "completion_period_years": 2.0,
        "existing_commitments": 32.0,
        "tender_value": 85.80 # Cap = (45*2*1.5) - 32 = 135 - 32 = 103 >= 85.80
    })
    assert res1["status"] == "SAT", f"Case 1 Expected SAT, got {res1['status']}"
    assert len(res1["violations"]) == 0, f"Case 1 Expected 0 violations, got {res1['violations']}"
    assert "SMT-CPTU-" in res1["certificate_id"]
    print(f" [PASS] Case 1 (Standard Compliant): Status={res1['status']}, Cert={res1['certificate_id']}, Solver={res1['solver_backend']}")

    # Case 2: Rule 39 Statutory Breach (VO > 15% without Cabinet Approval -> UNSAT)
    res2 = prover.verify_contract_compliance({
        "original_contract_value": 85.80,
        "variation_amount": 18.00, # 20.98% (> 15%)
        "cabinet_approval_obtained": False,
        "performance_security_pct": 10.0,
        "max_annual_turnover": 45.0,
        "completion_period_years": 2.0,
        "existing_commitments": 32.0,
        "tender_value": 85.80
    })
    assert res2["status"] == "UNSAT", f"Case 2 Expected UNSAT, got {res2['status']}"
    assert any("Rule 39" in v for v in res2["violations"]), f"Case 2 Expected Rule 39 violation, got {res2['violations']}"
    assert len(res2["recommendations"]) > 0, "Case 2 Expected recommendations"
    print(f" [PASS] Case 2 (Rule 39 Breach VO > 15%): Status={res2['status']}, Violations={res2['violations'][0][:60]}...")

    # Case 3: Rule 40 Statutory Exemption (VO > 15% WITH Cabinet Approval -> SAT)
    res3 = prover.verify_contract_compliance({
        "original_contract_value": 85.80,
        "variation_amount": 18.00, # 20.98% (> 15%)
        "cabinet_approval_obtained": True, # Cabinet Exemption Active
        "performance_security_pct": 10.0,
        "max_annual_turnover": 45.0,
        "completion_period_years": 2.0,
        "existing_commitments": 32.0,
        "tender_value": 85.80
    })
    assert res3["status"] == "SAT", f"Case 3 Expected SAT with Cabinet Clearance, got {res3['status']}"
    assert len(res3["violations"]) == 0, f"Case 3 Expected 0 violations, got {res3['violations']}"
    print(f" [PASS] Case 3 (Rule 40 Cabinet Exemption): Status={res3['status']}, Cert={res3['certificate_id']}")

    # Case 4: Form e-PW3-8 Security Breach (< 10% -> UNSAT)
    res4 = prover.verify_contract_compliance({
        "original_contract_value": 85.80,
        "variation_amount": 10.50,
        "cabinet_approval_obtained": False,
        "performance_security_pct": 7.5, # < 10%
        "max_annual_turnover": 45.0,
        "completion_period_years": 2.0,
        "existing_commitments": 32.0,
        "tender_value": 85.80
    })
    assert res4["status"] == "UNSAT", f"Case 4 Expected UNSAT for Security < 10%, got {res4['status']}"
    assert any("e-PW3-8" in v for v in res4["violations"]), f"Case 4 Expected e-PW3-8 violation, got {res4['violations']}"
    print(f" [PASS] Case 4 (Form e-PW3-8 Under-Security 7.5%): Status={res4['status']}, Violations={res4['violations'][0][:60]}...")

    # Case 5: Rule 98 Financial Capacity Deficit (Assessed Cap < Tender Value -> UNSAT)
    res5 = prover.verify_contract_compliance({
        "original_contract_value": 85.80,
        "variation_amount": 10.50,
        "cabinet_approval_obtained": False,
        "performance_security_pct": 10.0,
        "max_annual_turnover": 20.0, # Cap = (20*1.5*1.5) - 30 = 45 - 30 = 15 < 85.80
        "completion_period_years": 1.5,
        "existing_commitments": 30.0,
        "tender_value": 85.80
    })
    assert res5["status"] == "UNSAT", f"Case 5 Expected UNSAT for Capacity Deficit, got {res5['status']}"
    assert any("Capacity" in v for v in res5["violations"]), f"Case 5 Expected Capacity violation, got {res5['violations']}"
    print(f" [PASS] Case 5 (Rule 98 Capacity Deficit): Status={res5['status']}, Violations={res5['violations'][0][:60]}...")


def test_smt_backend_api():
    print(f"\n--- 2. Testing Live FastAPI Backend Endpoint ({BASE_URL}/api/smt/verify) ---")
    req_payload = {
        "original_contract_value": 48.50,
        "variation_amount": 5.20,
        "cabinet_approval_obtained": False,
        "performance_security_pct": 10.0,
        "max_annual_turnover": 35.0,
        "completion_period_years": 2.0,
        "existing_commitments": 18.0,
        "tender_value": 48.50
    }
    data = json.dumps(req_payload).encode('utf-8')
    req = urllib.request.Request(
        f"{BASE_URL}/api/smt/verify",
        data=data,
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            assert response.status == 200, f"Expected HTTP 200, got {response.status}"
            body = json.loads(response.read().decode())
            assert "status" in body
            assert "certificate_id" in body
            assert "proof_trace" in body
            print(f" [PASS] POST /api/smt/verify responded with HTTP 200:")
            print(f"        Status: {body['status']}")
            print(f"        Certificate ID: {body['certificate_id']}")
            print(f"        Solver Backend: {body['solver_backend']}")
            print(f"        Proof Steps: {len(body['proof_trace'])} formal deductions")
    except Exception as e:
        print(f" [FAIL] /api/smt/verify endpoint failed: {e}")
        raise e


def test_frontend_wiring():
    print("\n--- 3. Testing Frontend Files, 3D Canvas & HTML Wiring ---")
    # Verify files exist
    files_to_check = [
        os.path.join(ROOT_DIR, "js", "smt-3d.js"),
        os.path.join(ROOT_DIR, "js", "neuro-symbolic-smt.js"),
        os.path.join(ROOT_DIR, "js", "tds-auditor.js"),
        os.path.join(ROOT_DIR, "index.html")
    ]
    for fp in files_to_check:
        assert os.path.exists(fp), f"Missing required frontend file: {fp}"
        print(f" [PASS] Verified file exists: {os.path.basename(fp)} ({os.path.getsize(fp)} bytes)")

    # Verify index.html contains the necessary elements
    with open(os.path.join(ROOT_DIR, "index.html"), "r", encoding="utf-8") as f:
        html_content = f.read()

    elements_to_check = [
        'id="smt3dCanvas"',
        'id="smtOrigValue"',
        'id="smtVoValue"',
        'id="smtPerfSecurity"',
        'id="smtTurnoverA"',
        'id="smtPeriodN"',
        'id="smtCommitB"',
        'id="smtCabinetClearance"',
        'id="smtVoBadge"',
        'id="btnRunSmtSolver"',
        'id="smtProofContainer"',
        'src="js/smt-3d.js"',
        'src="js/neuro-symbolic-smt.js"'
    ]
    for elem in elements_to_check:
        assert elem in html_content, f"index.html is missing element: {elem}"
        print(f" [PASS] index.html contains: {elem}")

    # Verify js/smt-3d.js exports Smt3DVisualizer and window.initSmt3D
    with open(os.path.join(ROOT_DIR, "js", "smt-3d.js"), "r", encoding="utf-8") as f:
        smt3d_content = f.read()
    assert "class Smt3DVisualizer" in smt3d_content
    assert "window.initSmt3D" in smt3d_content
    assert "updateProofState" in smt3d_content
    print(" [PASS] js/smt-3d.js contains Smt3DVisualizer, window.initSmt3D & updateProofState")

    # Verify js/neuro-symbolic-smt.js exports solveAsync & exportSmtCertificate
    with open(os.path.join(ROOT_DIR, "js", "neuro-symbolic-smt.js"), "r", encoding="utf-8") as f:
        smt_js_content = f.read()
    assert "solveAsync" in smt_js_content
    assert "window.exportSmtCertificate" in smt_js_content
    print(" [PASS] js/neuro-symbolic-smt.js contains solveAsync & exportSmtCertificate")


if __name__ == "__main__":
    print("================================================================================")
    print(" TenderPulse 4IR - Microsoft Z3 SMT Solver & TDS Legal Proof Test Suite")
    print("================================================================================")
    test_smt_solver_unit()
    test_smt_backend_api()
    test_frontend_wiring()
    print("\n================================================================================")
    print(" 🚀 ALL Z3 SMT SOLVER & TDS AUDITOR TESTS PASSED (100% VERIFIED)")
    print("================================================================================")
