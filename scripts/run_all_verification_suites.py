"""
========================================================================================
 TenderPulse 4IR AI - Master Consolidated Verification Suite
 Runs all 5 platform verification suites back-to-back:
 1. 7 Commercial Production Readiness Pillars (test_production_readiness.py)
 2. Interactive End-to-End User Journey Tests (test_interactive_e2e_user_journey.py)
 3. 50,000+ Scaled Historical Cartel Radar (test_phase4_large_scale_cartel.py)
 4. Live Overview Dashboard Dynamic Bindings (test_overview_live_wiring.py)
 5. Zero-Knowledge Prover & PDF BOQ Parser (scripts/test_zkp_and_pdf.py)
========================================================================================
"""

import sys
import os
import subprocess
import time

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PYTHON_EXE = sys.executable

SUITES = [
    {
        "name": "7 Commercial Production Readiness Pillars",
        "script": os.path.join(ROOT_DIR, "test_production_readiness.py"),
        "description": "Docker, SQLite/Postgres ORM, JWT RBAC, Cartel Radar, Harvester, Sentinel Hub, Z3 SMT Prover"
    },
    {
        "name": "Interactive End-to-End User Journey (58 Assertions)",
        "script": os.path.join(ROOT_DIR, "test_interactive_e2e_user_journey.py"),
        "description": "Executive/Auditor/Analyst Auth, 403 Guards, Z3 SAT/UNSAT, SAR Coherence, Harvester Queue"
    },
    {
        "name": "50,000+ Scaled Historical Cartel Radar",
        "script": os.path.join(ROOT_DIR, "test_phase4_large_scale_cartel.py"),
        "description": "50,200 awards, 64 districts, 8 agencies, 16 syndicates, 4 forensic vectors, sub-second query"
    },
    {
        "name": "Live Overview Dashboard Dynamic Bindings",
        "script": os.path.join(ROOT_DIR, "test_overview_live_wiring.py"),
        "description": "32 live reactive data bindings replacing hardcoded mock metrics across 11 views"
    },
    {
        "name": "Zero-Knowledge Prover (zk-SNARKs) & PDF Parser",
        "script": os.path.join(ROOT_DIR, "scripts", "test_zkp_and_pdf.py"),
        "description": "Groth16/BN254 turnover proof & verification, Section 6 PDF BOQ schedule extraction"
    }
]

def run_master():
    t_master_start = time.time()
    print("\n" + "=" * 85)
    print("      TENDERPULSE 4IR AI - MASTER CONSOLIDATED VERIFICATION PASS")
    print(f"      Execution Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')} | Target: http://127.0.0.1:8080")
    print("=" * 85 + "\n")

    results = []
    for idx, suite in enumerate(SUITES, 1):
        print(f"\n[{idx}/{len(SUITES)}] RUNNING: {suite['name']}")
        print(f"      Scope: {suite['description']}")
        print("-" * 85)
        
        t0 = time.time()
        proc = subprocess.run(
            [PYTHON_EXE, suite["script"]],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        elapsed = time.time() - t0
        passed = (proc.returncode == 0)

        # Print truncated output for clarity
        lines = proc.stdout.strip().splitlines()
        for line in lines[-12:]:
            print(f"  | {line}")

        if not passed and proc.stderr:
            print(f"  [!] STDERR: {proc.stderr.strip()[:300]}")

        status_str = "PASS" if passed else "FAIL"
        print(f"--> Result: [{status_str}] in {elapsed:.2f}s\n")
        results.append({
            "name": suite["name"],
            "status": status_str,
            "time": elapsed,
            "passed": passed
        })

    t_total = time.time() - t_master_start

    print("\n" + "=" * 85)
    print("                     FINAL CONSOLIDATED SCORECARD")
    print("=" * 85)
    all_passed = True
    for r in results:
        mark = "✓ PASS" if r["passed"] else "✗ FAIL"
        print(f"  {mark:<8} | {r['name']:<50} | {r['time']:>6.2f}s")
        if not r["passed"]:
            all_passed = False

    print("-" * 85)
    total_status = "ALL SUITES PASSED (100% PRODUCTION READY)" if all_passed else "SOME SUITES FAILED"
    print(f"  STATUS: {total_status} | Total Execution Time: {t_total:.2f}s")
    print("=" * 85 + "\n")

    return 0 if all_passed else 1

if __name__ == "__main__":
    code = run_master()
    sys.exit(code)
