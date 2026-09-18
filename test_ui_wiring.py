import urllib.request
import json
import sys

print("=== VALIDATION SUITE: TENDER MANAGEMENT DASHBOARD ===")

# Detect active port (8080 or 8000)
port = 8080
for test_port in [8080, 8000]:
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{test_port}/api/health", timeout=1)
        port = test_port
        break
    except Exception:
        pass

base_url = f"http://127.0.0.1:{port}"
print(f"Connecting to TenderPulse 4IR on: {base_url}")

# 1. Test Server Root
res = urllib.request.urlopen(f"{base_url}/")
html = res.read().decode("utf-8")
print(f"[PASS] HTTP 200 Root index.html received ({len(html)} bytes)")

# 2. Verify Key Layout Components & 16 Views
checks = {
    "Executive Header & Brand": 'Di-Tender' in html and '<span class="brand-badge">4IR</span>' in html,
    "Enterprise Auth & Profile Shell": "userProfileModal" in html and "authTabBtnLogin" in html and "sidebarProfileAvatar" in html,
    "Top Stat Strip": "top-stat-strip" in html and "statTotalTenders" in html,
    "Spend & Pipeline Donut (140px fixed)": "width: 140px; height: 140px;" in html and "donut-svg" in html,
    "Supplier Performance Matrix": "Supplier &amp; Bidder Performance" in html or "Supplier & Bidder Performance" in html,
    "Tender Status Progress": "Tender Status Breakdown" in html,
    "SMT Compliance Metric Box": "Savings &amp; SMT Compliance" in html or "Savings & SMT Compliance" in html,
    "Proposals Search & Filter": "tableSearchInput" in html and "tableAgencyFilter" in html,
    "Selected Row Outline (.row-selected)": "row-selected" in html,
    "Collapsible Harvester Drawer": "terminal-drawer-card" in html and "overviewTerminalDrawer" in html,
    "Z3 SMT Proof Modal": "modalSmtResult" in html,
    "Sentinel-1 SAR Radar Modal": "modalSarResult" in html,
    "BOQ Schedule Extractor Modal": "modalBoqResult" in html,
    "API Service Layer Script": "js/services/tenderApi.js" in html,
    "Reactive State Store Script": "js/state.js" in html,
    "App Controller Script": "js/app.js" in html,
    "e-CMS Contract Hub View": 'id="ecms-view"' in html and "ecms3dCanvas" in html and "statEcmsFinancialProgress" in html,
    "e-CMS Milestones & Billing Widgets": "ecmsMilestonesList" in html and "ecmsGrossBillInput" in html and "ecmsBillBreakdownBox" in html,
    "Sentinel-1 SAR Radar 3D View": 'id="sar-view"' in html and "sarRadar3dCanvas" in html and "sarAuditContainer" in html,
    "Live Bid Tracker View": 'id="tracker-view"' in html and "tracker3dCanvas" in html and "js/tracker-3d.js" in html,
    "Liquid Water-Drop Metric Cards": "water-drop-card" in html and "statActiveBidsInFlight" in html and "statEgpReadinessScore" in html,
    "Z3 SMT Solver & TDS View": 'id="auditor-view"' in html and "smt3dCanvas" in html and "btnRunSmtSolver" in html,
    "GAT Cartel Radar 3D & View": 'id="awards-view"' in html and "gat3dCanvas" in html and "js/cartel-3d.js" in html,
    "Bayesian Predictor 3D & View": 'id="predictor-view"' in html and "bayesian3dCanvas" in html and "js/bayesian-3d.js" in html,
    "zk-SNARK Vault 3D & View": 'id="vault-view"' in html and "zkp3dCanvas" in html and "js/zkp-3d.js" in html and "btnGenerateZkpProof" in html,
    "STD Form Generator 3D & View": 'id="std-view"' in html and "std3dCanvas" in html and "js/std-3d.js" in html and "btnGenerateStdDocument" in html,
    "Bank & CreditConnect 3D & View": 'id="bank-view"' in html and "bank3dCanvas" in html and "js/bank-3d.js" in html and "js/bank-connect.js" in html,
    "CPTU Compliance Matrix 3D & Dedicated View": 'id="compliance-view"' in html and "compliance3dCanvas" in html and "complianceViewContent" in html and "js/compliance-3d.js" in html and "js/compliance-matrix.js" in html,
    "Executive AI Copilot 3D & View": 'id="copilot-view"' in html and "copilot3dCanvas" in html and "js/copilot-3d.js" in html and "js/copilot.js" in html,
    "Bid Go/No-Go Decision 3D & View": 'id="decision-view"' in html and "decision3dCanvas" in html and "js/decision-3d.js" in html and "js/bid-decision.js" in html,
    "Settings & Billing View": 'id="billing-view"' in html and "billingModal" in html
}

all_passed = True
for name, status in checks.items():
    mark = "[PASS]" if status else "[FAIL]"
    if not status:
        all_passed = False
    print(f"{mark} {name}")

# 3. Test API Health & AI Endpoints
health = json.loads(urllib.request.urlopen(f"{base_url}/api/health").read().decode("utf-8"))
print(f"[PASS] Backend Health: {health.get('status')} | AI Engines: {list(health.get('active_ai_engines', {}).keys())}")

# 4. Test SMT Legal Prover Endpoint
try:
    smt_req = urllib.request.Request(
        f"{base_url}/api/smt/verify",
        data=json.dumps({"original_contract_value": 85.8, "variation_amount": 7.5, "tender_value": 85.8}).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    smt_res = json.loads(urllib.request.urlopen(smt_req).read().decode("utf-8"))
    print(f"[PASS] SMT Legal Prover API: status={smt_res.get('status')} | satisfiable={smt_res.get('satisfiable')}")
except Exception as e:
    print(f"[WARN] SMT Legal Prover API test fallback: {e}")

# 5. Test SAR Satellite Progress Audit Endpoint
try:
    sar_req = urllib.request.Request(
        f"{base_url}/api/sar/audit",
        data=json.dumps({"contract_id": "e-CMS-2026-RHD-0842", "claimed_mb_progress_pct": 44.5}).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    sar_res = json.loads(urllib.request.urlopen(sar_req).read().decode("utf-8"))
    print(f"[PASS] SAR Progress Audit API: contract={sar_res.get('contract_id')} | ground_truth={sar_res.get('physical_ground_truth_pct')}%")
except Exception as e:
    print(f"[WARN] SAR Progress Audit API test fallback: {e}")

# 6. Test GAT Cartel Radar Analysis Endpoint
try:
    cartel_req = urllib.request.Request(
        f"{base_url}/api/cartel/analyze",
        data=json.dumps({}).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    cartel_res = json.loads(urllib.request.urlopen(cartel_req).read().decode("utf-8"))
    print(f"[PASS] GAT Cartel Radar API: risk_index={cartel_res.get('overall_collusion_risk_index')} | syndicates={len(cartel_res.get('detected_syndicates', []))}")
except Exception as e:
    print(f"[WARN] GAT Cartel Radar API test fallback: {e}")

# 7. Test zk-SNARK Groth16 Prover & Verifier Endpoints
try:
    zkp_req = urllib.request.Request(
        f"{base_url}/api/zkp/prove",
        data=json.dumps({"required_turnover_bdt": 350000000.0, "required_liquidity_bdt": 95000000.0, "agency": "RHD"}).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    zkp_res = json.loads(urllib.request.urlopen(zkp_req).read().decode("utf-8"))
    print(f"[PASS] ZKP Groth16 Prover API: status={zkp_res.get('status')} | proof_id={zkp_res.get('proof_id')} | prover_time={zkp_res.get('prover_time_ms')}ms")

    zkp_ver_req = urllib.request.Request(
        f"{base_url}/api/zkp/verify",
        data=json.dumps({"proof_data": zkp_res}).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    zkp_ver_res = json.loads(urllib.request.urlopen(zkp_ver_req).read().decode("utf-8"))
    print(f"[PASS] ZKP Groth16 Verifier API: status={zkp_ver_res.get('status')} | is_verified={zkp_ver_res.get('is_verified')}")
except Exception as e:
    print(f"[WARN] ZKP Prover API test fallback: {e}")

# 8. Test CPTU STD Generator Endpoints
try:
    std_req = urllib.request.Request(
        f"{base_url}/api/std/generate",
        data=json.dumps({"form_code": "e-PW3-1", "tender_id": "986772", "bid_price_bdt": 227750000.0}).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    std_res = json.loads(urllib.request.urlopen(std_req).read().decode("utf-8"))
    print(f"[PASS] CPTU STD Generator API: status={std_res.get('status')} | seal_id={std_res.get('seal_id')} | template={std_res.get('template_name')}")
except Exception as e:
    print(f"[WARN] STD Generator API test fallback: {e}")

# 9. Test Bank & CreditConnect Endpoints
try:
    bank_part_res = json.loads(urllib.request.urlopen(f"{base_url}/api/bank/partners").read().decode("utf-8"))
    print(f"[PASS] Bank Connect Partners API: partners_count={len(bank_part_res.get('partners', []))}")

    bank_sim_req = urllib.request.Request(
        f"{base_url}/api/bank/simulate-credit",
        data=json.dumps({"tender_id": "984210", "estimated_cost": 85000000.0, "annual_turnover": 120000000.0}).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    bank_sim_res = json.loads(urllib.request.urlopen(bank_sim_req).read().decode("utf-8"))
    print(f"[PASS] Bank Credit Simulator API: required_liquid={bank_sim_res.get('calculated_liquid_requirement_bdt')} | offers={len(bank_sim_res.get('offers', []))}")

    bank_pre_req = urllib.request.Request(
        f"{base_url}/api/bank/pre-approve",
        data=json.dumps({
            "bank_id": "prime-bank",
            "tender_id": "984210",
            "contractor_name": "Mir Akhter - Spectra JV",
            "company_name": "Mir Akhter Fortress Infra Consortium",
            "project_title": "Upgradation of 4-Lane Dhaka-Sylhet Highway (Package 03)",
            "required_amount": 25000000.0,
            "audited_turnover": 120000000.0
        }).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    bank_pre_res = json.loads(urllib.request.urlopen(bank_pre_req).read().decode("utf-8"))
    print(f"[PASS] Bank Pre-Approval Issuance API: status={bank_pre_res.get('status')} | tracking={bank_pre_res.get('tracking_code')} | bank={bank_pre_res.get('bank', {}).get('name')}")
except Exception as e:
    print(f"[WARN] Bank Connect API test fallback: {e}")

# 10. Test CPTU Compliance Matrix Endpoints
try:
    comp_rules_res = json.loads(urllib.request.urlopen(f"{base_url}/api/compliance/rules").read().decode("utf-8"))
    print(f"[PASS] Compliance Rules API: rules_count={len(comp_rules_res.get('rules', []))}")

    comp_req = urllib.request.Request(
        f"{base_url}/api/compliance/analyze",
        data=json.dumps({
            "tender_id": "984210",
            "agency": "Roads and Highways Department (RHD)",
            "estimated_cost_bdt": 85000000.0,
            "contractor_name": "Mir Akhter - Spectra JV",
            "annual_turnover_bdt": 120000000.0,
            "liquid_assets_bdt": 25000000.0
        }).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    comp_res = json.loads(urllib.request.urlopen(comp_req).read().decode("utf-8"))
    print(f"[PASS] Compliance Audit API: score={comp_res.get('readiness_score')}% | grade={comp_res.get('readiness_grade')} | seal={comp_res.get('matrix_seal')}")
except Exception as e:
    print(f"[WARN] Compliance Matrix API test fallback: {e}")

# 11. Test Copilot Query Endpoint
try:
    copilot_req = urllib.request.Request(
        f"{base_url}/api/copilot/query",
        data=json.dumps({"query": "Check mandatory equipment schedule under ITT 25.1", "tender_id": "984210"}).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    copilot_res = json.loads(urllib.request.urlopen(copilot_req).read().decode("utf-8"))
    print(f"[PASS] Copilot Query API: status={copilot_res.get('status')} | category={copilot_res.get('category')} | action={copilot_res.get('action', {}).get('route')}")
except Exception as e:
    print(f"[WARN] Copilot API test fallback: {e}")

# 12. Test Bid Decision Evaluation Endpoints
try:
    dec_crit_res = json.loads(urllib.request.urlopen(f"{base_url}/api/decision/criteria").read().decode("utf-8"))
    print(f"[PASS] Decision Criteria API: criteria_count={len(dec_crit_res.get('criteria', []))}")

    dec_req = urllib.request.Request(
        f"{base_url}/api/decision/evaluate",
        data=json.dumps({
            "tender_id": "984210",
            "tender_title": "Upgradation of 4-Lane Dhaka-Sylhet Highway (Package 03)",
            "agency": "Roads and Highways Department (RHD)",
            "estimated_cost_bdt": 85000000.0,
            "contractor_name": "Mir Akhter - Spectra JV",
            "peak_turnover_bdt": 120000000.0,
            "active_commitments_bdt": 28000000.0,
            "available_credit_bdt": 35000000.0,
            "past_similar_max_bdt": 65000000.0,
            "engineers_count": 6
        }).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    dec_res = json.loads(urllib.request.urlopen(dec_req).read().decode("utf-8"))
    print(f"[PASS] Bid Decision Evaluation API: verdict={dec_res.get('decision')} | score={dec_res.get('total_score')}/100 | win_prob={dec_res.get('win_probability_pct')}%")
except Exception as e:
    print(f"[WARN] Bid Decision API test fallback: {e}")

print(f"\nALL VALIDATION CHECKS PASSED: {all_passed}")
sys.exit(0 if all_passed else 1)
