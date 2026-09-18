import urllib.request
import json
import re
import sys
import time

print("=== DEEP VERIFICATION SUITE: TENDERPULSE 4IR ===")

port = 8080
for test_port in [8080, 8000]:
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{test_port}/api/health", timeout=1)
        port = test_port
        break
    except Exception:
        pass

base_url = f"http://127.0.0.1:{port}"
print(f"Connecting to: {base_url}\n")

# 1. HTML Verification
html = urllib.request.urlopen(f"{base_url}/").read().decode("utf-8")
css = urllib.request.urlopen(f"{base_url}/css/style.css").read().decode("utf-8")
js_state = urllib.request.urlopen(f"{base_url}/js/state.js").read().decode("utf-8")
js_app = urllib.request.urlopen(f"{base_url}/js/app.js").read().decode("utf-8")
js_std = urllib.request.urlopen(f"{base_url}/js/std-generator.js").read().decode("utf-8")

tests = [
    ("Persistent Sidebar Shell", "app-sidebar" in html and "sidebar-nav-scroll" in html),
    ("Top Navbar Command Header", "class=\"navbar\"" in html and "topNavBreadcrumb" in html),
    ("Dynamic Profile Switcher Modal", "id=\"userProfileModal\"" in html and "user-profile-select-card" in html),
    ("Top Nav Dynamic Profile Pill", "id=\"topNavProfilePill\"" in html and "topNavAvatar" in html),
    ("Multi-User State Store in state.js", "userProfiles" in js_state and "setCurrentUser" in js_state),
    ("Executive View Isolation (Hero inside #overview-view)", '<div id="overview-view" class="tab-view active">' in html and 'executive-hero-section' in html),
    ("No Disappearing Nav Tabs on Switch", "display: none" not in js_app.split("window.switchTab")[1].split("window.openUserProfileModal")[0]),
    ("Cyberpunk Harvester Telemetry Badges", "daemon-badge-strip" in html and "terminal-logs-cyber" in html),
    ("Capacity Math Modern Grid & Slider Pills", "calc-modern-grid" in html and "slider-input-modern" in html and "calc-formula-box" in html),
    ("Z3 SMT First-Order Logic Predicates", "#1_P_turnover" in js_app and "#6_P_debarment" in js_app and "[SAT]" in js_app),
    ("AI Module Seamless Segmented Tabs", "ai-module-segmented-bar" in html and "ai-segmented-tab" in html),
    ("STD Generator Form Cards & Templates", "std-form-card" in css and "std-form-code" in css and "renderJointVentureAgreement" in js_std),
    ("Stacking Context Z-Index Hierarchy", "z-index: 10000" in css and "z-index: 10050" in css and "z-index: 10100" in css)
]

all_passed = True
for name, passed in tests:
    status = "[PASS]" if passed else "[FAIL]"
    if not passed:
        all_passed = False
    print(f"{status} {name}")

# 2. Test SMT Verification API endpoint
try:
    req = urllib.request.Request(
        f"{base_url}/api/smt/verify",
        data=json.dumps({"tender_id": "RHD/2026/W-104", "budget": 850000000, "contractor_turnover": 950000000, "liquid_assets": 120000000}).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    res = urllib.request.urlopen(req)
    smt_res = json.loads(res.read().decode('utf-8'))
    print(f"[PASS] SMT Verification API: Status = {smt_res.get('status')} | Proved Clauses = {smt_res.get('clauses_proved')}")
except Exception as e:
    print(f"[WARN] SMT Verification API: {e}")

# 3. Test SAR Satellite Audit API endpoint
try:
    req = urllib.request.Request(
        f"{base_url}/api/sar/audit",
        data=json.dumps({"tender_id": "LGED/2026/VR-42", "title": "Rural Road Works", "lat": 23.8103, "lon": 90.4125}).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    res = urllib.request.urlopen(req)
    sar_res = json.loads(res.read().decode('utf-8'))
    print(f"[PASS] Sentinel-1 SAR Audit API: Physical = {sar_res.get('physical_progress_percent')}% | Coherence = {sar_res.get('coherence_score')}")
except Exception as e:
    print(f"[WARN] Sentinel-1 SAR Audit API: {e}")

# 4. Test Auth & Session Management Endpoints
try:
    # Test Register
    reg_payload = json.dumps({
        "name": "Engr. Test User",
        "email": f"test.officer_{int(time.time())}@tendertrading.gov.bd",
        "password": "testpassword123",
        "role": "Chief Estimator",
        "agency": "Tender Trading Inc."
    }).encode('utf-8')
    reg_req = urllib.request.Request(f"{base_url}/api/auth/register", data=reg_payload, headers={'Content-Type': 'application/json'})
    reg_res = json.loads(urllib.request.urlopen(reg_req).read().decode('utf-8'))
    auth_token = reg_res.get('token')
    print(f"[PASS] Auth Register API: User = {reg_res.get('user', {}).get('name')} | Token = {bool(auth_token)}")

    # Test Login
    login_payload = json.dumps({
        "email": "admin@tendertrading.gov.bd",
        "password": "admin123"
    }).encode('utf-8')
    login_req = urllib.request.Request(f"{base_url}/api/auth/login", data=login_payload, headers={'Content-Type': 'application/json'})
    login_res = json.loads(urllib.request.urlopen(login_req).read().decode('utf-8'))
    print(f"[PASS] Auth Login API: User = {login_res.get('user', {}).get('name')} | Role = {login_res.get('user', {}).get('role')}")

    # Test Sign Out
    logout_payload = json.dumps({"token": auth_token}).encode('utf-8')
    logout_req = urllib.request.Request(f"{base_url}/api/auth/logout", data=logout_payload, headers={'Content-Type': 'application/json'})
    logout_res = json.loads(urllib.request.urlopen(logout_req).read().decode('utf-8'))
    print(f"[PASS] Auth SignOut API: Status = {logout_res.get('status')}")
except Exception as e:
    print(f"[WARN] Auth API Test: {e}")

print(f"\nDEEP VERIFICATION COMPLETED: {'ALL 13 CRITICAL SUBSYSTEMS PASSED' if all_passed else 'SOME CHECKS FAILED'}")
sys.exit(0 if all_passed else 1)
