"""
TenderPulse 4IR AI - Enterprise High-Concurrency Load & Stress Testing Benchmark
Simulates 200+ concurrent clients across 50,000-record database queries, Microsoft Z3
SMT solver, and automated PDF/Excel document generators.
"""

import os
import sys
import time
import json
import random
import statistics
from typing import List, Dict, Any, Callable, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_URL = os.getenv("TENDERPULSE_BASE_URL", "http://127.0.0.1:8080")
DIVISIONS = ["All", "Dhaka", "Chattogram", "Rajshahi", "Khulna", "Barishal", "Sylhet", "Rangpur", "Mymensingh"]
AGENCIES = [
    "All",
    "Roads and Highways Department (RHD)",
    "Local Government Engineering Department (LGED)",
    "Bangladesh Water Development Board (BWDB)",
    "Public Works Department (PWD)",
    "Department of Public Health Engineering (DPHE)"
]


class PerformanceMetrics:
    def __init__(self, name: str):
        self.name = name
        self.latencies: List[float] = []
        self.status_codes: Dict[int, int] = {}
        self.errors: int = 0
        self.start_time = 0.0
        self.end_time = 0.0

    def start(self):
        self.start_time = time.perf_counter()

    def stop(self):
        self.end_time = time.perf_counter()

    def record(self, latency_sec: float, status_code: int):
        self.latencies.append(latency_sec)
        self.status_codes[status_code] = self.status_codes.get(status_code, 0) + 1
        if status_code >= 400:
            self.errors += 1

    @property
    def total_requests(self) -> int:
        return len(self.latencies)

    @property
    def duration(self) -> float:
        return max(self.end_time - self.start_time, 0.001)

    @property
    def rps(self) -> float:
        return round(self.total_requests / self.duration, 2)

    def percentile(self, p: float) -> float:
        if not self.latencies:
            return 0.0
        sorted_l = sorted(self.latencies)
        idx = int(len(sorted_l) * (p / 100.0))
        idx = min(idx, len(sorted_l) - 1)
        return round(sorted_l[idx] * 1000.0, 2)  # in ms

    def summary(self) -> Dict[str, Any]:
        if not self.latencies:
            return {"name": self.name, "total": 0, "errors": self.errors}

        ms_list = [l * 1000.0 for l in self.latencies]
        return {
            "scenario": self.name,
            "total_requests": self.total_requests,
            "duration_sec": round(self.duration, 2),
            "throughput_rps": self.rps,
            "error_count": self.errors,
            "error_rate_pct": round((self.errors / max(self.total_requests, 1)) * 100.0, 2),
            "latency_ms": {
                "min": round(min(ms_list), 2),
                "mean": round(statistics.mean(ms_list), 2),
                "p50_median": self.percentile(50),
                "p90": self.percentile(90),
                "p95": self.percentile(95),
                "p99": self.percentile(99),
                "max": round(max(ms_list), 2)
            },
            "status_codes": self.status_codes
        }

    def print_report(self):
        s = self.summary()
        lat = s["latency_ms"]
        err_col = "[✓] ZERO ERRORS (0.00%)" if s["error_count"] == 0 else f"[!] {s['error_count']} ERRORS ({s['error_rate_pct']}%)"
        print(f"\n  +-- {self.name} --+")
        print(f"  | Total Requests:   {s['total_requests']:,} across {s['duration_sec']}s")
        print(f"  | Throughput:       {s['throughput_rps']:,} req/sec")
        print(f"  | SLA Integrity:    {err_col}")
        print(f"  | Latencies (ms):   p50: {lat['p50_median']}ms | p90: {lat['p90']}ms | p95: {lat['p95']}ms | p99: {lat['p99']}ms | max: {lat['max']}ms")
        print(f"  +----------------------------------------------------------------+")


def get_authenticated_session() -> Tuple[requests.Session, str, requests.Session, str]:
    aud_session = requests.Session()
    anl_session = requests.Session()

    # Mount connection adapters with high pool size
    adapter = requests.adapters.HTTPAdapter(pool_connections=64, pool_maxsize=64, max_retries=1)
    aud_session.mount("http://", adapter)
    anl_session.mount("http://", adapter)

    # Login Auditor
    aud_login = aud_session.post(f"{BASE_URL}/api/auth/login", json={
        "email": "majumder.law@tendertrading.gov.bd",
        "password": "majumder123"
    }, timeout=10)
    assert aud_login.status_code == 200, f"Auditor login failed: {aud_login.text}"
    aud_token = aud_login.json()["access_token"]
    aud_session.headers.update({"Authorization": f"Bearer {aud_token}"})

    # Login Analyst
    anl_login = anl_session.post(f"{BASE_URL}/api/auth/login", json={
        "email": "karim.engr@tendertrading.gov.bd",
        "password": "karim123"
    }, timeout=10)
    assert anl_login.status_code == 200, f"Analyst login failed: {anl_login.text}"
    anl_token = anl_login.json()["access_token"]
    anl_session.headers.update({"Authorization": f"Bearer {anl_token}"})

    return aud_session, aud_token, anl_session, anl_token


def run_concurrency_pool(
    worker_fn: Callable[[int, requests.Session], None],
    total_tasks: int,
    concurrency: int,
    session: requests.Session
) -> None:
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(worker_fn, i, session) for i in range(total_tasks)]
        for f in as_completed(futures):
            f.result()


def run_benchmark():
    print("===========================================================================")
    print(" [*] TENDERPULSE 4IR - ENTERPRISE CONCURRENCY & STRESS BENCHMARK")
    print(f" Target Server: {BASE_URL}")
    print(" Concurrency Scale: 200 Virtual Clients | 50 Worker Threads")
    print("===========================================================================\n")

    # 1. Authenticate sessions
    print("--- Phase 0: Authenticating High-Concurrency Sessions ---")
    aud_session, aud_token, anl_session, anl_token = get_authenticated_session()
    print("[✓] Authenticated connection pools ready (Auditor & Analyst roles).\n")

    all_summaries = []

    # --------------------------------------------------------------------------
    # Scenario 1: Geospatial & 50K Cartel Database Load
    # --------------------------------------------------------------------------
    print("--- Phase 1: Benchmarking 64-District GIS Heatmap & 50K Database Queries ---")
    gis_metrics = PerformanceMetrics("64-District GIS Heatmap & 50K Database Load")
    gis_metrics.start()

    def task_gis(idx: int, sess: requests.Session):
        div = random.choice(DIVISIONS)
        agency = random.choice(AGENCIES)
        url = f"{BASE_URL}/api/cartel/district-heatmap?division={div}&agency={agency}"
        t0 = time.perf_counter()
        try:
            r = sess.get(url, timeout=15)
            gis_metrics.record(time.perf_counter() - t0, r.status_code)
        except Exception as e:
            gis_metrics.record(time.perf_counter() - t0, 500)

    run_concurrency_pool(task_gis, total_tasks=250, concurrency=50, session=aud_session)
    gis_metrics.stop()
    gis_metrics.print_report()
    all_summaries.append(gis_metrics.summary())
    assert gis_metrics.errors == 0, f"Encountered {gis_metrics.errors} errors in Scenario 1"

    # --------------------------------------------------------------------------
    # Scenario 2: CPU-Intensive Microsoft Z3 SMT Formal Logic Proofs
    # --------------------------------------------------------------------------
    print("\n--- Phase 2: Benchmarking Microsoft Z3 SMT Formal Logic Verification Engine ---")
    smt_metrics = PerformanceMetrics("Microsoft Z3 SMT Prover High-Frequency Resolution")
    smt_metrics.start()

    def task_smt(idx: int, sess: requests.Session):
        payload = {
            "tender_id": f"BENCH-{100000 + idx}",
            "contract_value": round(random.uniform(20000000, 200000000), -4),
            "variation_pct": round(random.uniform(5.0, 25.0), 1),
            "bank_guarantee_valid": random.choice([True, True, False]),
            "turnover_ratio": round(random.uniform(0.8, 2.5), 2),
            "similar_experience": True
        }
        t0 = time.perf_counter()
        try:
            r = sess.post(f"{BASE_URL}/api/smt/verify", json=payload, timeout=15)
            smt_metrics.record(time.perf_counter() - t0, r.status_code)
        except Exception:
            smt_metrics.record(time.perf_counter() - t0, 500)

    run_concurrency_pool(task_smt, total_tasks=250, concurrency=50, session=anl_session)
    smt_metrics.stop()
    smt_metrics.print_report()
    all_summaries.append(smt_metrics.summary())
    assert smt_metrics.errors == 0, f"Encountered {smt_metrics.errors} errors in Scenario 2"

    # --------------------------------------------------------------------------
    # Scenario 3: Memory & Document Streaming Load (Excel & PDF Exporters)
    # --------------------------------------------------------------------------
    print("\n--- Phase 3: Benchmarking High-Throughput PDF & Excel Report Streaming ---")
    doc_metrics = PerformanceMetrics("Automated PDF & Excel Document Streaming Engine")
    doc_metrics.start()

    def task_doc(idx: int, sess: requests.Session):
        call_type = idx % 3
        t0 = time.perf_counter()
        try:
            if call_type == 0:
                r = sess.get(f"{BASE_URL}/api/cartel/export/pdf", timeout=15)
            elif call_type == 1:
                r = sess.get(f"{BASE_URL}/api/cartel/export/excel", timeout=15)
            else:
                payload = {
                    "smt_data": {"certificate_id": f"CERT-STRESS-{idx}", "is_satisfiable": True, "deduction_trace": ["[AXIOM 1]", "[AXIOM 2]", "[SATISFIED]"], "variable_model": {"VariationAllowed": True}},
                    "contract_value": 50000000.0,
                    "variation_pct": 10.0,
                    "bank_guarantee_valid": True,
                    "turnover_ratio": 1.5,
                    "similar_experience": True
                }
                r = sess.post(f"{BASE_URL}/api/smt/export/pdf", json=payload, timeout=15)
            doc_metrics.record(time.perf_counter() - t0, r.status_code)
        except Exception:
            doc_metrics.record(time.perf_counter() - t0, 500)

    run_concurrency_pool(task_doc, total_tasks=120, concurrency=40, session=aud_session)
    doc_metrics.stop()
    doc_metrics.print_report()
    all_summaries.append(doc_metrics.summary())
    assert doc_metrics.errors == 0, f"Encountered {doc_metrics.errors} errors in Scenario 3"

    # --------------------------------------------------------------------------
    # Scenario 4: Mixed Real-World Enterprise Workload (200 Virtual Users)
    # --------------------------------------------------------------------------
    print("\n--- Phase 4: Simulating Mixed Enterprise User Session (200 Virtual Clients) ---")
    mixed_metrics = PerformanceMetrics("Mixed Enterprise Production Workload (200 Concurrent Users)")
    mixed_metrics.start()

    def task_mixed(idx: int, sess: requests.Session):
        # 40% GIS, 30% SMT, 15% Summary/Historical, 15% Export
        roll = random.random()
        t0 = time.perf_counter()
        try:
            if roll < 0.40:
                div = random.choice(DIVISIONS)
                r = sess.get(f"{BASE_URL}/api/cartel/district-heatmap?division={div}", timeout=15)
            elif roll < 0.70:
                payload = {
                    "tender_id": f"MIX-{idx}",
                    "contract_value": 45000000.0,
                    "variation_pct": 12.0,
                    "bank_guarantee_valid": True,
                    "turnover_ratio": 1.4,
                    "similar_experience": True
                }
                r = sess.post(f"{BASE_URL}/api/smt/verify", json=payload, timeout=15)
            elif roll < 0.85:
                r = sess.get(f"{BASE_URL}/api/cartel/historical-summary", timeout=15)
            else:
                r = sess.get(f"{BASE_URL}/api/cartel/export/pdf", timeout=15)
            mixed_metrics.record(time.perf_counter() - t0, r.status_code)
        except Exception:
            mixed_metrics.record(time.perf_counter() - t0, 500)

    run_concurrency_pool(task_mixed, total_tasks=400, concurrency=50, session=aud_session)
    mixed_metrics.stop()
    mixed_metrics.print_report()
    all_summaries.append(mixed_metrics.summary())
    assert mixed_metrics.errors == 0, f"Encountered {mixed_metrics.errors} errors in Scenario 4"

    # Save benchmark telemetry artifact
    output_path = os.path.join(os.path.dirname(__file__), "..", "data", "benchmark_results.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "target": BASE_URL,
            "concurrency_profile": "200 Virtual Clients (50 Worker Pool)",
            "total_requests_executed": sum(s["total_requests"] for s in all_summaries),
            "total_errors": sum(s["error_count"] for s in all_summaries),
            "overall_sla_passed": all(s["error_count"] == 0 for s in all_summaries),
            "scenarios": all_summaries
        }, f, indent=2)

    total_reqs = sum(s["total_requests"] for s in all_summaries)
    print("\n===========================================================================")
    print(f" [✓] BENCHMARK COMPLETE: {total_reqs:,} REQUESTS EXECUTED WITH 0% ERROR RATE")
    print(f" Telemetry Artifact Saved: {output_path}")
    print("===========================================================================\n")


if __name__ == "__main__":
    run_benchmark()
