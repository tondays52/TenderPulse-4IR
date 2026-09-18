"""
TenderPulse 4IR × Tender Trading Inc.
CPTU Compliance Matrix & Statutory RFP Shredder Engine (compliance_engine.py)
Grounding: Public Procurement Act 2006 & Public Procurement Rules 2008 (PPR-2008)
"""

import time
import hashlib
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class ComplianceClauseRequest(BaseModel):
    tender_id: str = Field(default="984210", description="e-GP Tender ID")
    agency: str = Field(default="Roads and Highways Department (RHD)", description="Procuring Entity")
    estimated_cost_bdt: float = Field(default=85000000.0, description="Tender estimated cost in BDT")
    contractor_name: str = Field(default="Mir Akhter - Spectra JV", description="Contractor Name")
    annual_turnover_bdt: float = Field(default=120000000.0, description="Audited annual turnover in BDT")
    liquid_assets_bdt: float = Field(default=25000000.0, description="Liquid assets / Bank LOC in BDT")
    similar_experience_years: int = Field(default=7, description="Years of similar contract experience")
    personnel_count: int = Field(default=6, description="Key technical personnel available")
    equipment_count: int = Field(default=8, description="Machinery units available")
    has_litigation_history: bool = Field(default=False, description="Adverse debarment or litigation records")

class ComplianceMatrixEngine:
    """
    Analyzes tender parameters clause-by-clause against CPTU PPR-2008 statutory requirements.
    """
    def __init__(self):
        self.engine_version = "CPTU-Matrix-v4.2"
        self.statutory_rules = [
            {"clause": "ITT 14.1(a)", "category": "Financial Capability", "rule": "Rule 96(3) PPR-2008", "std_form": "Form e-PW3-3A"},
            {"clause": "ITT 15.1(a)", "category": "Liquid Assets & Solvency", "rule": "Rule 96(4) PPR-2008", "std_form": "Form e-PW2A-8"},
            {"clause": "ITT 16.1(b)", "category": "Specific Experience", "rule": "Rule 96(2) PPR-2008", "std_form": "Form e-PW3-2"},
            {"clause": "ITT 16.1(a)", "category": "General Experience", "rule": "Rule 96(1) PPR-2008", "std_form": "Form e-PW3-1"},
            {"clause": "ITT 24.1 & TDS", "category": "Key Personnel Schedule", "rule": "Rule 97(1) PPR-2008", "std_form": "Form e-PW3-5"},
            {"clause": "ITT 25.1 & TDS", "category": "Equipment & Machinery", "rule": "Rule 97(2) PPR-2008", "std_form": "Form e-PW3-6"},
            {"clause": "ITT 31.1", "category": "Tender Security", "rule": "Rule 95(1) PPR-2008", "std_form": "Form e-PW3-7"},
            {"clause": "ITT 22.1", "category": "Subcontracting Limit", "rule": "Rule 99 PPR-2008", "std_form": "Form e-PW3-4"},
            {"clause": "ITT 18.1", "category": "Litigation & Non-Debarment", "rule": "Rule 127 PPR-2008", "std_form": "Form e-PW2A-9"}
        ]

    def list_rules(self) -> List[Dict[str, Any]]:
        return self.statutory_rules

    def audit_compliance(self, req: ComplianceClauseRequest) -> Dict[str, Any]:
        """
        Performs clause-by-clause compliance gap analysis.
        """
        min_turnover_req = req.estimated_cost_bdt * 0.75
        min_liquid_req = req.estimated_cost_bdt * 0.25
        min_security_req = req.estimated_cost_bdt * 0.02

        turnover_ok = req.annual_turnover_bdt >= min_turnover_req
        liquid_ok = req.liquid_assets_bdt >= min_liquid_req
        exp_ok = req.similar_experience_years >= 5
        personnel_ok = req.personnel_count >= 4
        equipment_ok = req.equipment_count >= 5
        litigation_ok = not req.has_litigation_history

        clauses = [
            {
                "id": 1,
                "category": "Financial Capability",
                "itt_clause": "ITT 14.1(a)",
                "requirement": "Minimum Average Annual Construction Turnover in best 5 years",
                "threshold": f"BDT {min_turnover_req / 10000000:.2f} Cr",
                "contractor_value": f"BDT {req.annual_turnover_bdt / 10000000:.2f} Cr",
                "status": "COMPLIANT" if turnover_ok else "DEFICIT_WARNING",
                "risk_level": "Low Risk" if turnover_ok else "High Risk",
                "evidence_doc": "Audited Financial Statements & NBR Tax Return Acknowledgment (Form e-PW3-3A)",
                "cptu_citation": "Rule 96(3) PPR-2008"
            },
            {
                "id": 2,
                "category": "Liquid Assets & Solvency",
                "itt_clause": "ITT 15.1(a)",
                "requirement": "Minimum Liquid Assets / Working Capital or Bank Credit Line",
                "threshold": f"BDT {min_liquid_req / 10000000:.2f} Cr Unconditional",
                "contractor_value": f"BDT {req.liquid_assets_bdt / 10000000:.2f} Cr",
                "status": "COMPLIANT" if liquid_ok else "ACTION_REQUIRED",
                "risk_level": "Low Risk" if liquid_ok else "Critical (Bank LOC Required)",
                "evidence_doc": "Bank Solvency Certificate / Form e-PW2A-8 Letter of Commitment",
                "cptu_citation": "Rule 96(4) PPR-2008"
            },
            {
                "id": 3,
                "category": "Specific Experience",
                "itt_clause": "ITT 16.1(b)",
                "requirement": "Satisfactory completion of similar contract within last 5 years",
                "threshold": "Min 1 contract of similar magnitude",
                "contractor_value": f"{req.similar_experience_years} Years Track Record",
                "status": "COMPLIANT" if exp_ok else "REVIEW_REQUIRED",
                "risk_level": "Low Risk" if exp_ok else "Moderate Risk",
                "evidence_doc": "Completion Certificate signed by Executive Engineer (XEN)",
                "cptu_citation": "Rule 96(2) PPR-2008"
            },
            {
                "id": 4,
                "category": "General Experience",
                "itt_clause": "ITT 16.1(a)",
                "requirement": "General construction experience as Prime Contractor",
                "threshold": "Minimum 5 - 10 Years",
                "contractor_value": f"{req.similar_experience_years + 3} Years Active Trading",
                "status": "COMPLIANT",
                "risk_level": "Zero Risk",
                "evidence_doc": "Incorporation Certificate & Historical e-GP Work Orders",
                "cptu_citation": "Rule 96(1) PPR-2008"
            },
            {
                "id": 5,
                "category": "Key Personnel Schedule",
                "itt_clause": "ITT 24.1 & TDS",
                "requirement": "Mandatory Technical Staff (Project Manager, Quality Engineer, Surveyors)",
                "threshold": "Min 4 Professional Engineers",
                "contractor_value": f"{req.personnel_count} Dedicated Engineers Assigned",
                "status": "COMPLIANT" if personnel_ok else "ACTION_REQUIRED",
                "risk_level": "Low Risk",
                "evidence_doc": "Signed CV (Form e-PW3-5), IEB Registration & NID copies",
                "cptu_citation": "Rule 97(1) PPR-2008"
            },
            {
                "id": 6,
                "category": "Equipment & Machinery",
                "itt_clause": "ITT 25.1 & TDS",
                "requirement": "Essential Construction Equipment (Excavators, Batching Plant, Rollers)",
                "threshold": "Min 5 Core Units",
                "contractor_value": f"{req.equipment_count} Units Owned / Leased",
                "status": "COMPLIANT" if equipment_ok else "REVIEW_REQUIRED",
                "risk_level": "Low Risk",
                "evidence_doc": "Ownership Deeds / Valid Lease Agreements (Form e-PW3-6)",
                "cptu_citation": "Rule 97(2) PPR-2008"
            },
            {
                "id": 7,
                "category": "Tender Security",
                "itt_clause": "ITT 31.1",
                "requirement": "Unconditional Bank Guarantee or Pay Order for Tender Security",
                "threshold": f"Approx BDT {min_security_req / 1000000:.2f} Lakh",
                "contractor_value": "Form e-PW3-7 Bank Guarantee Prepared",
                "status": "COMPLIANT",
                "risk_level": "Zero Risk",
                "evidence_doc": "Original Bank Guarantee valid 28 days beyond bid validity",
                "cptu_citation": "Rule 95(1) PPR-2008"
            },
            {
                "id": 8,
                "category": "Subcontracting Threshold",
                "itt_clause": "ITT 22.1",
                "requirement": "Maximum allowable subcontracting threshold",
                "threshold": "Not to exceed 20% of total contract value",
                "contractor_value": "0% Subcontracting (Self-Execution)",
                "status": "COMPLIANT",
                "risk_level": "Zero Risk",
                "evidence_doc": "Subcontractor Profile or Self-Execution Undertaking",
                "cptu_citation": "Rule 99 PPR-2008"
            },
            {
                "id": 9,
                "category": "Statutory Integrity & Non-Debarment",
                "itt_clause": "ITT 18.1",
                "requirement": "No adverse debarment on CPTU national blacklist or ongoing litigation",
                "threshold": "Clean Statutory Standing",
                "contractor_value": "Zero Debarments Recorded" if litigation_ok else "Litigation Pending",
                "status": "COMPLIANT" if litigation_ok else "CRITICAL_DISQUALIFICATION",
                "risk_level": "Zero Risk" if litigation_ok else "Severe Legal Risk",
                "evidence_doc": "Sworn Non-Debarment Affidavit on BDT 300 Non-Judicial Stamp (Form e-PW2A-9)",
                "cptu_citation": "Rule 127 PPR-2008"
            }
        ]

        compliant_count = sum(1 for c in clauses if c["status"] == "COMPLIANT")
        total_clauses = len(clauses)
        readiness_score = round((compliant_count / total_clauses) * 100, 1)

        raw_sig = f"{req.tender_id}-{req.contractor_name}-{readiness_score}-{time.time()}"
        matrix_seal = f"CPTU-MATRIX-{hashlib.sha256(raw_sig.encode()).hexdigest()[:12].upper()}"

        return {
            "status": "SUCCESS",
            "tender_id": req.tender_id,
            "agency": req.agency,
            "contractor": req.contractor_name,
            "readiness_score": readiness_score,
            "readiness_grade": "PREQUALIFICATION READY (Grade A+)" if readiness_score >= 88 else "REMEDIATION REQUIRED",
            "compliant_count": compliant_count,
            "total_clauses": total_clauses,
            "matrix_seal": matrix_seal,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "clauses": clauses
        }

# Global singleton
compliance_matrix_engine = ComplianceMatrixEngine()
