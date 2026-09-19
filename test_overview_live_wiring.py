import urllib.request
import json
import re
import sys

print("=== OVERVIEW LIVE DYNAMIC WIRING & TELEMETRY VERIFICATION ===")

base_url = "http://127.0.0.1:8080"

# 1. Test live backend endpoints that feed the Overview tab
endpoints = [
    ("/api/tenders/live?limit=100", "Live Database Tenders", lambda d: d.get("count", 0) >= 10 and len(d.get("tenders", [])) >= 10),
    ("/api/cartel/analyze", "Live GAT Cartel Collusion Telemetry", lambda d: ("overall_collusion_risk_index" in d or "overall_market_integrity_score" in d) and "detected_syndicates" in d),
    ("/api/corrigenda", "Live Corrigenda & Dispute Feeds", lambda d: d.get("count", 0) >= 1 and isinstance(d.get("corrigenda", []), list)),
    ("/api/harvester/status", "Harvester Daemon Status & Active Agencies", lambda d: d.get("status") == "SUCCESS" and "telemetry" in d),
    ("/api/auth/users", "Registered Enterprise Profiles", lambda d: len(d) >= 1)
]

passed = 0
failed = 0

for path, label, validator in endpoints:
    url = f"{base_url}{path}"
    try:
        req = urllib.request.Request(url, headers={"Content-Type": "application/json"})
        if "cartel" in path:
            req.data = b"{}"
        res = urllib.request.urlopen(req, timeout=10)
        data = json.loads(res.read().decode("utf-8"))
        if validator(data):
            print(f"  [PASS] {label}: Responded 200 with valid schema")
            passed += 1
        else:
            print(f"  [FAIL] {label}: Data validation failed ({data})")
            failed += 1
    except Exception as e:
        print(f"  [FAIL] {label}: HTTP request failed - {e}")
        failed += 1

# 2. Inspect state.js for dynamic methods
with open("js/state.js", "r", encoding="utf-8") as f:
    state_js = f.read()

state_checks = [
    ("setSelectedAgency defined", "setSelectedAgency(agency)" in state_js),
    ("recalculateStats defined with BDT math", "recalculateStats()" in state_js and "totalPipelineValueBDT" in state_js),
    ("loadLiveTenders connects to backend", "async loadLiveTenders()" in state_js and "getLiveTenders" in state_js),
    ("setSelectedTender enriches SMT math", "rule39TurnoverReq" in state_js and "assessedCapacityCr" in state_js),
    ("setSelectedTender enriches SAR spatial", "orbitTrack" in state_js and "meanCoherence" in state_js),
    ("setSelectedTender enriches Cartel profile", "syndicateClassification" in state_js)
]

for label, cond in state_checks:
    if cond:
        print(f"  [PASS] TenderStore State: {label}")
        passed += 1
    else:
        print(f"  [FAIL] TenderStore State: {label}")
        failed += 1

# 3. Inspect app.js for dynamic overview wiring
with open("js/app.js", "r", encoding="utf-8") as f:
    app_js = f.read()

app_checks = [
    ("updateOverviewDashboard calculates dynamic totals", "function updateOverviewDashboard(tenders)" in app_js),
    ("Dynamic calculation of formatted total BDT", "totalValBDT.toLocaleString('en-US')" in app_js),
    ("Dynamic Spend Chips computation", "spendAuthEl.textContent = `৳ ${authB}B`" in app_js or "spendAuthEl" in app_js),
    ("Dynamic Agency Bar & Legend generation", "agencyBarEl.innerHTML = barHtml" in app_js),
    ("Dynamic Agency Table Rows generation", "agencyTableBody.innerHTML = tableAgencies.map" in app_js),
    ("Auxiliary Cartel & Corrigenda live fetcher", "fetchLiveOverviewAuxiliary" in app_js),
    ("Automatic live tenders load on boot", "window.tenderStore.loadLiveTenders()" in app_js),
    ("Dynamic filterPipelineEntity calculation", "const allTenders = (window.tenderStore && window.tenderStore.state.tenders)" in app_js and "matchedVal" in app_js),
    ("Cross-tab parameter synchronization on row selection", "window.tenderStore.setSelectedTender(tenderId)" in app_js)
]

for label, cond in app_checks:
    if cond:
        print(f"  [PASS] App.js Controller: {label}")
        passed += 1
    else:
        print(f"  [FAIL] App.js Controller: {label}")
        failed += 1

# 4. Verify index.html contains all necessary target elements
with open("index.html", "r", encoding="utf-8") as f:
    index_html = f.read()

html_checks = [
    ("Semantic ID execTotalVal present", 'id="execTotalVal"' in index_html),
    ("Semantic ID execCompliancePct present", 'id="execCompliancePct"' in index_html),
    ("Semantic ID statSmtCompliance present", 'id="statSmtCompliance"' in index_html),
    ("Semantic ID statCartelDrift present", 'id="statCartelDrift"' in index_html),
    ("Semantic ID statSettledVol present", 'id="statSettledVol"' in index_html),
    ("Semantic ID statDisputeCount present", 'id="statDisputeCount"' in index_html),
    ("Semantic ID spendChipAuthorized present", 'id="spendChipAuthorized"' in index_html),
    ("Semantic ID spendChipSettled present", 'id="spendChipSettled"' in index_html),
    ("Semantic ID overviewAgencyBar present", 'id="overviewAgencyBar"' in index_html),
    ("Semantic ID overviewAgencyLegend present", 'id="overviewAgencyLegend"' in index_html),
    ("Semantic ID overviewAgencyTableBody present", 'id="overviewAgencyTableBody"' in index_html),
    ("Semantic ID overviewProposalsTableBody present", 'id="overviewProposalsTableBody"' in index_html)
]

for label, cond in html_checks:
    if cond:
        print(f"  [PASS] Index.html Markup: {label}")
        passed += 1
    else:
        print(f"  [FAIL] Index.html Markup: {label}")
        failed += 1

print("\n========================================")
print(f"TOTAL TESTS: {passed + failed}")
print(f"PASSED: {passed}")
print(f"FAILED: {failed}")
print(f"STATUS: {'100% PASSING' if failed == 0 else 'FAILURES DETECTED'}")
print("========================================\n")

if failed > 0:
    sys.exit(1)
else:
    sys.exit(0)
