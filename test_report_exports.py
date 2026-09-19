"""
TenderPulse 4IR AI - Report Export Verification Suite
Validates:
1. Cartel Forensic Audit Excel Export (GET /api/cartel/export/excel)
2. Cartel Forensic Audit PDF Export (GET /api/cartel/export/pdf)
3. SMT Proof Certificate PDF Export (POST /api/smt/export/pdf)
4. SMT Proof Matrix Excel Export (POST /api/smt/export/excel)
5. RBAC Role Restrictions on Export Endpoints
"""

import sys
import os
import io
import time
import json
import requests
import openpyxl

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_URL = "http://127.0.0.1:8080"
TIMEOUT = 15

def run_export_tests():
    print(f"\n{'='*75}")
    print(" [*] TESTING AUTOMATED PDF & EXCEL REPORT EXPORTS")
    print(f" Target: {BASE_URL}")
    print(f"{'='*75}")

    # 1. Authenticate roles
    print("\n--- 1. Authenticating Roles for Export Access ---")
    auditor_resp = requests.post(f"{BASE_URL}/api/auth/login", json={"email": "majumder.law@tendertrading.gov.bd", "password": "majumder123"})
    assert auditor_resp.status_code == 200
    auditor_token = auditor_resp.json()["access_token"]
    print(f"[✓] Auditor authenticated (token length: {len(auditor_token)})")

    analyst_resp = requests.post(f"{BASE_URL}/api/auth/login", json={"email": "karim.engr@tendertrading.gov.bd", "password": "karim123"})
    assert analyst_resp.status_code == 200
    analyst_token = analyst_resp.json()["access_token"]
    print(f"[✓] Analyst authenticated (token length: {len(analyst_token)})")

    # 2. Test Cartel Excel Export
    print("\n--- 2. Testing Cartel Forensic Audit Excel (.xlsx) Export ---")
    t0 = time.time()
    resp_c_excel = requests.get(
        f"{BASE_URL}/api/cartel/export/excel",
        headers={"Authorization": f"Bearer {auditor_token}"},
        timeout=TIMEOUT
    )
    t_c_excel = time.time() - t0
    assert resp_c_excel.status_code == 200, f"Cartel Excel export failed: {resp_c_excel.text}"
    content_type = resp_c_excel.headers.get("content-type", "")
    assert "openxmlformats" in content_type or "sheet" in content_type or "octet-stream" in content_type, f"Invalid Content-Type: {content_type}"
    excel_bytes = resp_c_excel.content
    assert len(excel_bytes) > 4000, f"Excel file too small: {len(excel_bytes)} bytes"
    
    # Validate with openpyxl
    wb = openpyxl.load_workbook(io.BytesIO(excel_bytes))
    sheet_names = wb.sheetnames
    assert "Executive Summary" in sheet_names, f"Missing Executive Summary sheet: {sheet_names}"
    assert "Detected Syndicates" in sheet_names, f"Missing Detected Syndicates sheet: {sheet_names}"
    assert "Forensic Vectors" in sheet_names, f"Missing Forensic Vectors sheet: {sheet_names}"
    print(f"[✓] Cartel Excel workbook generated in {t_c_excel:.2f}s ({len(excel_bytes)} bytes)")
    print(f"    Validated sheets: {sheet_names}")

    # 3. Test Cartel PDF Export
    print("\n--- 3. Testing Cartel Forensic Audit PDF (.pdf) Export ---")
    t0 = time.time()
    resp_c_pdf = requests.get(
        f"{BASE_URL}/api/cartel/export/pdf",
        headers={"Authorization": f"Bearer {auditor_token}"},
        timeout=TIMEOUT
    )
    t_c_pdf = time.time() - t0
    assert resp_c_pdf.status_code == 200, f"Cartel PDF export failed: {resp_c_pdf.text}"
    assert "application/pdf" in resp_c_pdf.headers.get("content-type", ""), f"Invalid Content-Type: {resp_c_pdf.headers.get('content-type')}"
    pdf_bytes = resp_c_pdf.content
    assert len(pdf_bytes) > 2000, f"PDF file too small: {len(pdf_bytes)} bytes"
    assert pdf_bytes.startswith(b"%PDF"), "File does not begin with standard %PDF header"
    print(f"[✓] Cartel PDF audit dossier generated in {t_c_pdf:.2f}s ({len(pdf_bytes)} bytes)")
    print(f"    PDF Header: {pdf_bytes[:8].decode('latin1')}")

    # 4. Test SMT PDF Certificate Export
    print("\n--- 4. Testing SMT Proof Certificate PDF (.pdf) Export ---")
    smt_payload = {
        "original_contract_value": 85.80,
        "variation_amount": 10.50,
        "cabinet_approval_obtained": False,
        "performance_security_pct": 10.0,
        "max_annual_turnover": 45.0,
        "completion_period_years": 2.0,
        "existing_commitments": 32.0,
        "tender_value": 85.80
    }
    t0 = time.time()
    resp_smt_pdf = requests.post(
        f"{BASE_URL}/api/smt/export/pdf",
        headers={"Authorization": f"Bearer {analyst_token}"},
        json=smt_payload,
        timeout=TIMEOUT
    )
    t_smt_pdf = time.time() - t0
    assert resp_smt_pdf.status_code == 200, f"SMT PDF export failed: {resp_smt_pdf.text}"
    assert "application/pdf" in resp_smt_pdf.headers.get("content-type", ""), f"Invalid Content-Type: {resp_smt_pdf.headers.get('content-type')}"
    smt_pdf_bytes = resp_smt_pdf.content
    assert len(smt_pdf_bytes) > 2000, f"SMT PDF too small: {len(smt_pdf_bytes)} bytes"
    assert smt_pdf_bytes.startswith(b"%PDF"), "SMT PDF does not begin with %PDF header"
    disp = resp_smt_pdf.headers.get("content-disposition", "")
    assert "SMT-CPTU" in disp or "pdf" in disp, f"Content-Disposition missing cert ID: {disp}"
    print(f"[✓] SMT Proof Certificate PDF generated in {t_smt_pdf:.2f}s ({len(smt_pdf_bytes)} bytes)")
    print(f"    Disposition: {disp}")

    # 5. Test SMT Excel Matrix Export
    print("\n--- 5. Testing SMT Proof Matrix Excel (.xlsx) Export ---")
    t0 = time.time()
    resp_smt_excel = requests.post(
        f"{BASE_URL}/api/smt/export/excel",
        headers={"Authorization": f"Bearer {analyst_token}"},
        json=smt_payload,
        timeout=TIMEOUT
    )
    t_smt_excel = time.time() - t0
    assert resp_smt_excel.status_code == 200, f"SMT Excel export failed: {resp_smt_excel.text}"
    smt_excel_bytes = resp_smt_excel.content
    assert len(smt_excel_bytes) > 2000, f"SMT Excel too small: {len(smt_excel_bytes)} bytes"
    wb_smt = openpyxl.load_workbook(io.BytesIO(smt_excel_bytes))
    assert "SMT Proof Matrix" in wb_smt.sheetnames, f"Missing SMT sheet: {wb_smt.sheetnames}"
    print(f"[✓] SMT Proof Matrix Excel generated in {t_smt_excel:.2f}s ({len(smt_excel_bytes)} bytes)")
    print(f"    Sheet name: {wb_smt.sheetnames[0]}")

    # 6. Test RBAC Protection
    print("\n--- 6. Testing RBAC Role Enforcement on Export Endpoints ---")
    # Analyst should NOT be allowed to export Cartel dossier (requires Auditor/Admin/Executive)
    denied_cartel = requests.get(
        f"{BASE_URL}/api/cartel/export/excel",
        headers={"Authorization": f"Bearer {analyst_token}"},
        timeout=TIMEOUT
    )
    assert denied_cartel.status_code == 403, f"Expected 403 for Analyst on Cartel Export, got {denied_cartel.status_code}"
    print("[✓] RBAC Guard: Analyst access to Cartel Excel export rejected with HTTP 403 Forbidden")

    # Invalid token should be rejected with HTTP 401 Unauthorized
    invalid_token_resp = requests.post(
        f"{BASE_URL}/api/smt/export/pdf",
        headers={"Authorization": "Bearer invalid_jwt_token_signature_999"},
        json=smt_payload,
        timeout=TIMEOUT
    )
    assert invalid_token_resp.status_code == 401, f"Expected 401 for invalid token, got {invalid_token_resp.status_code}"
    print("[✓] RBAC Guard: Cryptographically invalid JWT token rejected with HTTP 401 Unauthorized")

    print(f"\n{'='*75}")
    print(" [✓] ALL 6 EXPORT VERIFICATION SUITES PASSED (100%)")
    print(f"{'='*75}\n")

if __name__ == "__main__":
    run_export_tests()
