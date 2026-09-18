"""
TenderPulse 4IR × Tender Trading Inc.
Institutional Banking & CreditConnect Engine (bank_engine.py)
Grounding: Bangladesh Bank BRPD Regulations & CPTU PPR-2008 Rule 28 / Form e-PW2A-8
"""

import time
import hashlib
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class BankPartner(BaseModel):
    id: str
    name: str
    short_name: str
    credit_rating: str
    program_name: str
    turnaround_hours: int
    interest_rate_range: str
    max_sanction_bdt: float
    shariah_compliant: bool
    branch: str
    contact_person: str
    logo_symbol: str

class CreditSimulationRequest(BaseModel):
    tender_id: str = Field(default="984210", description="e-GP Tender ID")
    estimated_cost: float = Field(default=85000000.0, description="Tender estimated cost in BDT")
    required_liquid_assets: Optional[float] = Field(default=None, description="Required liquid assets in BDT")
    contractor_name: str = Field(default="Mir Akhter - Spectra JV", description="Contractor / JV Name")
    annual_turnover: float = Field(default=120000000.0, description="Audited 5-year average annual turnover")
    preferred_bank_id: Optional[str] = Field(default=None, description="Preferred bank partner ID")

class PreApprovalApplicationRequest(BaseModel):
    bank_id: str
    tender_id: str
    contractor_name: str
    company_name: str
    project_title: str
    required_amount: float
    audited_turnover: float
    cptu_form_type: str = "e-PW2A-8"

class BankConnectEngine:
    """
    Simulates real-time credit line pre-approvals and Form e-PW2A-8 institutional commitments.
    """
    def __init__(self):
        self.partner_banks: List[Dict[str, Any]] = [
            {
                "id": "prime-bank",
                "name": "Prime Bank PLC",
                "short_name": "Prime Bank",
                "credit_rating": "AAA (CRAB / CRISL)",
                "program_name": "Prime Contractor SpeedCredit (e-GP Special Line)",
                "turnaround_hours": 24,
                "interest_rate_range": "9.0% - 11.5% p.a.",
                "max_sanction_bdt": 250000000.0,  # 25 Cr
                "shariah_compliant": False,
                "branch": "Motijheel Corporate Branch, Dhaka",
                "contact_person": "A. K. Azad (VP & Head of Structured Contracting Finance)",
                "logo_symbol": "🏛️"
            },
            {
                "id": "brac-bank",
                "name": "BRAC Bank PLC",
                "short_name": "BRAC Bank",
                "credit_rating": "AAA (CRAB)",
                "program_name": "BRAC InfraConstruct Liquidity & Credit Line Facility",
                "turnaround_hours": 48,
                "interest_rate_range": "9.5% - 12.0% p.a.",
                "max_sanction_bdt": 180000000.0,  # 18 Cr
                "shariah_compliant": False,
                "branch": "Gulshan Head Office, Dhaka",
                "contact_person": "Shahriar Iqbal (Senior Manager, Institutional Assets)",
                "logo_symbol": "🏢"
            },
            {
                "id": "city-bank",
                "name": "The City Bank Limited",
                "short_name": "City Bank",
                "credit_rating": "AA+ (CRISL)",
                "program_name": "City Contractor Priority Line & Bank Guarantee",
                "turnaround_hours": 36,
                "interest_rate_range": "9.2% - 11.8% p.a.",
                "max_sanction_bdt": 300000000.0,  # 30 Cr
                "shariah_compliant": False,
                "branch": "Principal Branch, Dilkusha, Dhaka",
                "contact_person": "Mahmud Hasan (Head of Gov Procurement Banking)",
                "logo_symbol": "🏙️"
            },
            {
                "id": "islami-bank",
                "name": "Islami Bank Bangladesh PLC",
                "short_name": "IBBL",
                "credit_rating": "AAA (CRISL)",
                "program_name": "Shariah Infrastructure Bai-Muajjal Credit Line",
                "turnaround_hours": 48,
                "interest_rate_range": "8.8% - 11.0% p.a. (Profit Rate)",
                "max_sanction_bdt": 350000000.0,  # 35 Cr
                "shariah_compliant": True,
                "branch": "Central Corporate Branch, Dhaka",
                "contact_person": "M. M. Rahman (Executive VP, Corporate Investment)",
                "logo_symbol": "🕌"
            },
            {
                "id": "ebl",
                "name": "Eastern Bank PLC (EBL)",
                "short_name": "EBL",
                "credit_rating": "AAA (CRAB)",
                "program_name": "EBL e-GP Contractor FastLine & Performance Bond",
                "turnaround_hours": 24,
                "interest_rate_range": "9.1% - 11.6% p.a.",
                "max_sanction_bdt": 280000000.0,  # 28 Cr
                "shariah_compliant": False,
                "branch": "EBL Principal Branch, 100 Motijheel, Dhaka",
                "contact_person": "Tanveer Ahmed (Head of Syndications & Structured Finance)",
                "logo_symbol": "🏦"
            }
        ]

    def get_partners(self) -> List[Dict[str, Any]]:
        return self.partner_banks

    def simulate_credit(self, req: CreditSimulationRequest) -> Dict[str, Any]:
        """
        Calculates required liquid asset deficit under CPTU rules and scores partner bank matches.
        Standard Rule: Minimum liquid assets = 20% to 30% of tender estimated cost.
        """
        required_liquid = req.required_liquid_assets or (req.estimated_cost * 0.25)
        
        # Turnovers / Capacity safety ratio
        turnover_coverage = req.annual_turnover / (req.estimated_cost or 1.0)
        
        offers = []
        for bank in self.partner_banks:
            # Check eligibility
            is_eligible = bank["max_sanction_bdt"] >= required_liquid
            
            # Risk Scoring (0 - 100)
            base_score = 92.0
            if turnover_coverage > 1.2:
                base_score += 5.0
            if bank["turnaround_hours"] <= 24:
                base_score += 2.5
            if bank["shariah_compliant"]:
                base_score += 1.0
            match_score = min(99.4, round(base_score, 1))
            
            # Calculate estimated monthly financing cost
            rate_mid = 0.105
            monthly_cost = (required_liquid * rate_mid) / 12.0
            
            offers.append({
                "bank_id": bank["id"],
                "bank_name": bank["name"],
                "short_name": bank["short_name"],
                "credit_rating": bank["credit_rating"],
                "program_name": bank["program_name"],
                "turnaround_hours": bank["turnaround_hours"],
                "interest_rate_range": bank["interest_rate_range"],
                "max_sanction_bdt": bank["max_sanction_bdt"],
                "shariah_compliant": bank["shariah_compliant"],
                "is_eligible": is_eligible,
                "match_score": match_score,
                "estimated_monthly_interest_bdt": round(monthly_cost, 2),
                "required_amount_bdt": required_liquid,
                "recommended": bank["id"] == "prime-bank" or (req.preferred_bank_id == bank["id"])
            })

        # Sort by match score descending
        offers.sort(key=lambda x: x["match_score"], reverse=True)

        return {
            "status": "SUCCESS",
            "tender_id": req.tender_id,
            "estimated_cost_bdt": req.estimated_cost,
            "calculated_liquid_requirement_bdt": required_liquid,
            "turnover_coverage_ratio": round(turnover_coverage, 2),
            "total_institutional_capacity_bdt": sum(b["max_sanction_bdt"] for b in self.partner_banks),
            "offers": offers,
            "cptu_statutory_reference": "CPTU PPR-2008 ITT Clause 15.1 & Form e-PW2A-8 / e-PG3-8"
        }

    def issue_pre_approval(self, req: PreApprovalApplicationRequest) -> Dict[str, Any]:
        """
        Issues an official cryptographic Pre-Approval Certificate for Form e-PW2A-8.
        """
        bank = next((b for b in self.partner_banks if b["id"] == req.bank_id), self.partner_banks[0])
        
        timestamp = time.time()
        raw_sig = f"{bank['id']}-{req.tender_id}-{req.contractor_name}-{req.required_amount}-{timestamp}"
        certificate_hash = hashlib.sha256(raw_sig.encode()).hexdigest().upper()
        tracking_code = f"EGP-LOC-{certificate_hash[:8]}"
        seal_id = f"BANK-SEAL-{certificate_hash[8:16]}"

        return {
            "status": "APPROVED",
            "tracking_code": tracking_code,
            "seal_id": seal_id,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp)),
            "bank": {
                "id": bank["id"],
                "name": bank["name"],
                "branch": bank["branch"],
                "contact_person": bank["contact_person"],
                "credit_rating": bank["credit_rating"]
            },
            "contractor": {
                "name": req.contractor_name,
                "company": req.company_name,
                "audited_turnover_bdt": req.audited_turnover
            },
            "tender": {
                "id": req.tender_id,
                "title": req.project_title,
                "sanction_amount_bdt": req.required_amount
            },
            "commitment_form": req.cptu_form_type,
            "statutory_text": f"We hereby unconditionally commit to provide a line of credit of BDT {req.required_amount:,.2f} to {req.contractor_name} for the execution of Tender ID {req.tender_id} in compliance with Form {req.cptu_form_type}.",
            "validity_days": 120,
            "turnaround_guarantee": f"{bank['turnaround_hours']} Hours",
            "security_hash": certificate_hash
        }

# Global singleton engine
bank_connect_engine = BankConnectEngine()
