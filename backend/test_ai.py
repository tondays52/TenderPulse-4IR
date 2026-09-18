"""
Automated Test Suite for TenderPulse 4IR AI Backend Modules
Tests Z3 SMT Prover, NetworkX Cartel Radar, Sentinel-1 SAR Auditor, and PDF Parser.
"""

import sys
import os

# Ensure Windows PowerShell/cmd UTF-8 compatibility
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# Add parent directory to sys.path so backend package imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.smt_solver import CptuLegalProver
from backend.cartel_radar import CartelRadarEngine
from backend.sar_processor import SarProgressAuditor
from backend.pdf_parser import TenderPdfParser


def test_smt_prover():
    print("--- [1/4] Testing Microsoft Z3 SMT Legal Prover ---")
    prover = CptuLegalProver()

    # Case A: Compliant contract (VO = 12.2% <= 15%, PS = 10%, Capacity OK)
    res_sat = prover.verify_contract_compliance({
        "original_contract_value": 85.80,
        "variation_amount": 10.50,
        "cabinet_approval_obtained": False,
        "performance_security_pct": 10.0,
        "max_annual_turnover": 45.0,
        "completion_period_years": 2.0,
        "existing_commitments": 32.0,
        "tender_value": 85.80
    })
    print(f"Compliant Case Result: {res_sat['status']} (Backend: {res_sat['solver_backend']})")
    print(f"Proof Cert: {res_sat['certificate_id']}")
    assert res_sat["status"] == "SAT", "Expected SAT for compliant contract"

    # Case B: Non-compliant contract (VO = 23.3% > 15% without cabinet approval)
    res_unsat = prover.verify_contract_compliance({
        "original_contract_value": 85.80,
        "variation_amount": 20.00,
        "cabinet_approval_obtained": False,
        "performance_security_pct": 8.0,  # Below 10%
        "max_annual_turnover": 20.0,
        "completion_period_years": 1.0,
        "existing_commitments": 25.0,     # Capacity deficit
        "tender_value": 85.80
    })
    print(f"Non-Compliant Case Result: {res_unsat['status']}")
    print(f"Violations detected: {len(res_unsat['violations'])}")
    for v in res_unsat["violations"]:
        print(f"  -> {v}")
    assert res_unsat["status"] == "UNSAT", "Expected UNSAT for violating contract"
    print("✓ SMT Prover PASSED\n")


def test_cartel_radar():
    print("--- [2/4] Testing NetworkX Cartel Radar ---")
    cartel = CartelRadarEngine()
    analysis = cartel.analyze_bidding_syndicate()
    print(f"Status: {analysis['status']}")
    print(f"Contractors Indexed: {analysis['contractors_indexed']}")
    print(f"Edges Detected: {analysis['edges_detected']}")
    print(f"Syndicates Flagged: {len(analysis['detected_syndicates'])}")
    for syn in analysis["detected_syndicates"]:
        print(f"  -> {syn['syndicate_id']}: {syn['collusion_type']} ({', '.join(syn['members'])})")
    assert analysis["contractors_indexed"] > 0, "Expected contractors in graph"
    assert len(analysis["detected_syndicates"]) > 0, "Expected syndicates detected"
    print("✓ Cartel Radar PASSED\n")


def test_sar_auditor():
    print("--- [3/4] Testing Sentinel-1 SAR Progress Auditor ---")
    auditor = SarProgressAuditor()
    audit = auditor.audit_physical_progress({
        "contract_id": "RHD/2026/PW-04",
        "claimed_mb_progress_pct": 68.0,
        "latitude": 22.7010,
        "longitude": 90.3535,
        "project_type": "Highway Embankment & Asphalt Pavement"
    })
    print(f"Contract: {audit['contract_id']}")
    print(f"Claimed MB: {audit['claimed_mb_progress_pct']}% vs SAR Derived: {audit['physical_ground_truth_pct']}%")
    print(f"Discrepancy Delta: +{audit['discrepancy_delta_pct']}% ({audit['audit_status']})")
    print(f"SAR Certificate ID: {audit['audit_certificate_id']}")
    assert audit["discrepancy_delta_pct"] > 0, "Expected positive discrepancy delta"
    print("✓ SAR Auditor PASSED\n")


def test_pdf_parser():
    print("--- [4/4] Testing e-GP PDF & BOQ Schedule Parser ---")
    parser = TenderPdfParser()
    sample_text = """
    GOVERNMENT OF THE PEOPLE'S REPUBLIC OF BANGLADESH
    Roads and Highways Department (RHD)
    Office of the Executive Engineer, Barishal Road Division
    
    Tender ID: 1098421
    Name of Work: Construction of 4-Lane Rigid Pavement & Drainage from Ch. 12+000 to 24+500
    Minimum Liquidated Damages: 0.1% per day up to maximum 10%
    Minimum Average Annual Construction Turnover: BDT 45.00 Crore in last 5 years
    
    Section 6: Bill of Quantities (BOQ)
    1 Excavation in all types of soil Cum 50000 190.00
    2 Granular Sub-base course Cum 30000 3500.00
    3 Dense Bituminous Macadam Sqm 120000 1350.00
    """
    res = parser.parse_text_stream(sample_text, "Sample_ePW3.pdf")
    print(f"Procuring Entity: {res['metadata']['procuring_entity']}")
    print(f"Tender ID: {res['metadata']['tender_id']}")
    print(f"Turnover: BDT {res['metadata']['turnover_requirement_cr']} Cr")
    print(f"BOQ Items Parsed: {res['boq_summary']['total_items']}")
    print(f"Estimated Total: ৳{res['boq_summary']['estimated_total_bdt_cr']} Cr")
    assert res["metadata"]["tender_id"] == "1098421", "Expected tender ID 1098421"
    print("✓ PDF Parser PASSED\n")


def test_egp_scraper():
    print("--- [5/5] Testing Live Bangladesh e-GP Portal Scraper ---")
    from backend.egp_live_scraper import EgpLiveScraper
    scraper = EgpLiveScraper()
    tenders = scraper.fetch_live_tenders("LGED", limit=2)
    print(f"Retrieved: {len(tenders)} live tenders")
    if tenders:
        t = tenders[0]
        print(f"  -> Tender ID: {t['tenderId']} | {t['title'][:55]}...")
        print(f"  -> Entity: {t['agency']}")
        print(f"  -> Est. Cost: ৳{t['estimatedCost']/10000000:.2f} Cr | Security: ৳{t['tenderSecurity']/100000:.1f} Lakh")
        print(f"  -> Source: {t['source']}")
    assert len(tenders) > 0, "Expected at least 1 tender parsed"
    synced = scraper.sync_to_storage(tenders)
    print(f"Storage Sync: {synced} records added to live_feed.json")
    print("✓ Live e-GP Scraper PASSED\n")


if __name__ == "__main__":
    print("==================================================")
    print(" TenderPulse 4IR AI Backend - Unit & Integration Test")
    print("==================================================\n")
    test_smt_prover()
    test_cartel_radar()
    test_sar_auditor()
    test_pdf_parser()
    test_egp_scraper()
    print("==================================================")
    print(" ALL 4IR AI MODULES VERIFIED SUCCESSFULLY (100% OK)")
    print("==================================================")
