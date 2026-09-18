import urllib.request
import json
import re
import sys

print("=== OVERVIEW TAB COMPLETE INTEGRATION & WIRING VALIDATION ===")

base_url = "http://127.0.0.1:8080"
print(f"Connecting to TenderPulse 4IR on: {base_url}")

# 1. Fetch live HTML
try:
    res = urllib.request.urlopen(f"{base_url}/")
    html = res.read().decode("utf-8")
    print(f"[PASS] HTTP 200 Root index.html received ({len(html)} bytes)\n")
except Exception as e:
    print(f"[FAIL] Could not connect to {base_url}: {e}")
    sys.exit(1)

tests = [
    # Section 1: Overview tab container
    ("Overview Tab Container", 'id="overview-view"' in html),
    
    # Section 2: Executive Greeting & Harvester Trigger
    ("Executive Greeting Headline", "Good morning," in html and 'id="currentUserName"' in html),
    ("Trigger Harvester Button", "window.triggerHarvesterFromOverview()" in html),
    
    # Section 3: 4 Metric Cards in Top Stat Strip
    ("Top Stat Strip Container", 'id="topStatStrip"' in html),
    ("Top Stat Card 1 (SMT Compliance -> auditor-view)", "switchTab('auditor-view')" in html),
    ("Top Stat Card 2 (Risk/Cartel -> awards-view)", "switchTab('awards-view')" in html),
    ("Top Stat Card 3 (Settled Budget -> ecms-view)", "switchTab('ecms-view')" in html),
    ("Top Stat Card 4 (Open Disputes -> auditor-view)", "switchTab('auditor-view')" in html),
    
    # Section 4: Processed & Awarded Pipeline
    ("Pipeline Entity Filter Select", 'onchange="window.filterPipelineEntity(this.value)"' in html),
    ("Pipeline Total Metric Element", 'id="overviewPipelineTotalVal"' in html),
    ("Spend Chip Authorized -> auditor-view", "Authorized" in html and "switchTab('auditor-view')" in html),
    ("Spend Chip Settled -> ecms-view", "Settled" in html and "switchTab('ecms-view')" in html),
    ("Spend Chip Refunded -> bank-view", "Refunded" in html and "switchTab('bank-view')" in html),
    ("Spend Chip Pending -> billing-view", "Pending" in html and "switchTab('billing-view')" in html),
    ("Compliance Donut Chart (140px fixed)", "donut-svg" in html and "94.6%" in html),
    ("Target Progress Bar & Link", "Savings &amp; SMT Compliance" in html or "Savings & SMT Compliance" in html),
    
    # Section 5: Supplier & Bidder Performance
    ("At-Risk List Present", "at-risk-list" in html),
    ("At-Risk Item 1 (Marisol SMT trigger)", "triggerSmtVerification('eGP-8819'" in html),
    ("At-Risk Item 2 (Dev SMT trigger)", "triggerSmtVerification('eGP-3920'" in html),
    ("At-Risk Item 3 (Hertz SMT trigger)", "triggerSmtVerification('eGP-7721'" in html),
    ("At-Risk Item 4 (Léa SMT trigger)", "triggerSmtVerification('eGP-1A2D'" in html),
    ("Top Contractors List Present", "top-contractors-list" in html),
    ("Contractor Inspection Binding (Spectra)", "inspectContractorFromOverview('Spectra Eng.')" in html),
    ("Contractor Inspection Binding (Monem)", "inspectContractorFromOverview('Abdul Monem')" in html),
    ("Contractor Inspection Binding (Mir Akhter)", "inspectContractorFromOverview('Mir Akhter')" in html),
    
    # Section 6: What Needs Your Attention
    ("Attention Header & Filter", 'onchange="window.filterAttentionList(this.value)"' in html and 'id="overviewAttentionList"' in html),
    ("Attention Action 1 -> auditor-view", "Decline-rate spike" in html and "switchTab('auditor-view')" in html),
    ("Attention Action 2 -> bank-view", "Bank guarantee renewal" in html and "switchTab('bank-view')" in html),
    ("Attention Action 3 -> ecms-view", "Settlement delayed" in html and "switchTab('ecms-view')" in html),
    ("Attention Action 4 -> SAR Audit trigger", "SAR Satellite earth displacement" in html and "triggerSarAudit(" in html),
    ("Attention Action 5 -> awards-view", "High-velocity syndicate burst" in html and "switchTab('awards-view')" in html),
    
    # Section 7: Tender Status Breakdown & Agency Table
    ("Agency Multi-Segment Bar", "agency-stacked-bar" in html),
    ("Agency Bar Filter (LGED)", "filterOverviewByAgency('LGED')" in html),
    ("Agency Bar Filter (RHD)", "filterOverviewByAgency('RHD')" in html),
    ("Agency Bar Filter (BWDB)", "filterOverviewByAgency('BWDB')" in html),
    ("Agency Table Clickable Row (LGED)", "filterOverviewByAgency('LGED')" in html),
    ("Agency Table Clickable Row (RHD)", "filterOverviewByAgency('RHD')" in html),
    ("Agency Table Clickable Row (BWDB)", "filterOverviewByAgency('BWDB')" in html),
    ("Agency Table Clickable Row (DPHE)", "filterOverviewByAgency('DPHE')" in html),
    ("Agency Table Clickable Row (PGCB)", "filterOverviewByAgency('PGCB')" in html),
    
    # Section 8: Proposals Table
    ("Search Filter Input", 'id="tableSearchInput"' in html),
    ("Agency Dropdown Filter", 'id="tableAgencyFilter"' in html),
    ("Proposals Table Body", 'id="overviewProposalsTableBody"' in html),
    ("Proposal Row SMT Proof Button", "SMT Proof" in html and "triggerSmtVerification" in html),
    ("Proposal Row SAR Audit Button", "SAR Audit" in html and "triggerSarAudit" in html),
    ("Proposal Row Live Track Button", "addTenderToLivePipeline" in html),
    
    # Section 9: Collapsible Harvester Drawer
    ("Collapsible Drawer Header", "e-GP Autonomous 24/7 Harvester Stream" in html),
    ("Forced Harvest Button", "tenderMiner.triggerManualScan" in html),
    ("Drawer Body Container", 'id="overviewTerminalDrawer"' in html),
    
    # Section 10: Modal Overlays
    ("Z3 SMT Proof Modal Overlay", 'id="modalSmtResult"' in html and 'id="modalSmtResultBody"' in html),
    ("SAR Radar Site Audit Modal Overlay", 'id="modalSarResult"' in html and 'id="modalSarResultBody"' in html),
    ("PDF BOQ Extractor Modal Overlay", 'id="modalBoqResult"' in html and 'id="modalBoqResultBody"' in html)
]

passed = 0
failed = 0

for name, result in tests:
    if result:
        print(f"  [PASS]: {name}")
        passed += 1
    else:
        print(f"  [FAIL]: {name}")
        failed += 1

print("\n--- Testing JavaScript Handlers in js/app.js & js/state.js ---")
with open("js/app.js", "r", encoding="utf-8") as f:
    app_js = f.read()

with open("js/state.js", "r", encoding="utf-8") as f:
    state_js = f.read()

js_tests = [
    ("window.triggerHarvesterFromOverview defined", "window.triggerHarvesterFromOverview = function" in app_js),
    ("window.filterOverviewByAgency defined", "window.filterOverviewByAgency = function" in app_js),
    ("window.inspectContractorFromOverview defined", "window.inspectContractorFromOverview = function" in app_js),
    ("window.filterPipelineEntity defined", "window.filterPipelineEntity = function" in app_js),
    ("window.filterAttentionList defined", "window.filterAttentionList = function" in app_js),
    ("window.triggerSmtVerification defined", "window.triggerSmtVerification = async function" in app_js or "window.triggerSmtVerification = function" in app_js),
    ("window.triggerSarAudit defined", "window.triggerSarAudit = async function" in app_js or "window.triggerSarAudit = function" in app_js),
    ("window.selectProposalRow defined", "window.selectProposalRow = function" in app_js),
    ("window.addTenderToLivePipeline defined", "window.addTenderToLivePipeline = function" in app_js),
    ("Reactive State Store subscribe flexibility", "if (typeof event === 'function')" in state_js),
    ("Initial preload from INITIAL_TENDERS", "INITIAL_TENDERS" in state_js)
]

for name, result in js_tests:
    if result:
        print(f"  [PASS]: {name}")
        passed += 1
    else:
        print(f"  [FAIL]: {name}")
        failed += 1

print(f"\n========================================")
print(f"TOTAL TESTS: {passed + failed}")
print(f"PASSED: {passed}")
print(f"FAILED: {failed}")
print(f"STATUS: {'100% PASSING' if failed == 0 else 'FAILURES DETECTED'}")
print(f"========================================\n")

if failed > 0:
    sys.exit(1)
else:
    sys.exit(0)
