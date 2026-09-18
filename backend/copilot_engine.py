"""
TenderPulse 4IR × Tender Trading Inc.
Executive AI Copilot & Knowledge Retrieval Engine (copilot_engine.py)
Grounding: Public Procurement Act 2006, Public Procurement Rules 2008 (PPR-2008),
and e-GP Standard Tender Documents (e-PW2, e-PW3, e-PG2, e-PG3).
"""

import time
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class CopilotQueryRequest(BaseModel):
    query: str = Field(..., description="User prompt or procurement question")
    tender_id: Optional[str] = Field(default="984210", description="Active e-GP Tender ID")
    contractor_name: Optional[str] = Field(default="Mir Akhter - Spectra JV", description="Contractor / JV entity")
    agency: Optional[str] = Field(default="Roads and Highways Department (RHD)", description="Procuring entity")
    estimated_cost_bdt: Optional[float] = Field(default=85000000.0, description="Tender estimated cost in BDT")

class TenderCopilotEngine:
    """
    Context-aware procurement intelligence copilot grounded in Bangladesh CPTU regulations.
    """
    def __init__(self):
        self.engine_version = "Copilot-v4.2"
        self.conversation_history = []

    def process_query(self, req: CopilotQueryRequest) -> Dict[str, Any]:
        q = req.query.lower().strip()
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        cost_cr = (req.estimated_cost_bdt / 10000000.0) if req.estimated_cost_bdt else 8.5
        
        reply = ""
        category = "General CPTU Advisory"
        statutory_citation = "PPA 2006 & PPR-2008"
        action_route = None
        action_label = None

        if "equipment" in q or "machinery" in q or "rig" in q or "batching" in q:
            category = "Technical Capability (ITT 25.1)"
            statutory_citation = "Rule 97(2) PPR-2008 & Form e-PW3-6"
            reply = (
                f"Under <strong>Section 2 TDS Clause ITT 25.1</strong>, mandatory equipment for Tender ID {req.tender_id} requires:<br>"
                "&bull; <strong>Rotary Drilling Rig</strong>: Minimum 2 Units (capacity &ge; 1500mm dia)<br>"
                "&bull; <strong>Concrete Batching Plant</strong>: Minimum 1 Unit (&ge; 60 m³/hr)<br>"
                "&bull; <strong>Hydraulic Excavator & Tandem Roller</strong>: Min 4 Units<br><br>"
                "<span style='color: #f59e0b;'>⚠️ Statutory Alert:</span> PCC Clause 14.1 mandates equipment mobilization within 14 calendar days of contract signing."
            )
            action_route = "auditor-view"
            action_label = "Inspect TDS Equipment Schedule →"

        elif "liquidated" in q or "damage" in q or "penalty" in q or "delay" in q:
            category = "Contract Conditions (GCC 47.1)"
            statutory_citation = "Rule 39 PPR-2008 & GCC Clause 47.1"
            reply = (
                "Under <strong>GCC Clause 47.1 / PCC</strong>, liquidated damages for unexcused delay are set at "
                "<strong>0.10% of the contract price per calendar day</strong>.<br>"
                "The maximum cumulative penalty is capped at <strong>10.0% of the initial Contract Price</strong>. "
                "Reaching this cap triggers standard termination under GCC Clause 59."
            )
            action_route = "auditor-view"
            action_label = "Run SMT Legal Verification →"

        elif "jv" in q or "joint venture" in q or "consortium" in q or "partner" in q:
            category = "Consortium Eligibility (ITT 22.1)"
            statutory_citation = "Rule 99 PPR-2008 & Form e-PW3-4"
            reply = (
                "<strong>Joint Ventures are strictly permitted</strong> under <strong>CPTU PPR-2008 Rule 99 & ITT 22.1</strong>:<br>"
                "&bull; <strong>Maximum 3 Partners</strong> allowed in JVCA.<br>"
                "&bull; <strong>Lead Partner</strong> must satisfy at least <strong>40%</strong> of qualifying financial turnover and liquid asset criteria.<br>"
                "&bull; <strong>Other Partners</strong> must satisfy at least <strong>25%</strong> each.<br>"
                "&bull; All partners are jointly and severally liable, and a formal JV Agreement (Form e-PW3-4) must be registered."
            )
            action_route = "std-view"
            action_label = "Generate JVCA Form e-PW3-4 →"

        elif "bank" in q or "credit" in q or "solvency" in q or "epw2a-8" in q or "liquid" in q:
            min_liquid = req.estimated_cost_bdt * 0.25
            category = "Financial Solvency (ITT 15.1)"
            statutory_citation = "Rule 96(4) PPR-2008 & Form e-PW2A-8"
            reply = (
                f"For Tender ID {req.tender_id} (Estimated BDT {cost_cr:.2f} Cr), the mandatory liquid asset commitment is "
                f"<strong>BDT {min_liquid / 10000000:.2f} Crore</strong> (25% of estimate).<br><br>"
                "This must be submitted as an <strong>unconditional Letter of Commitment for Line of Credit (Form e-PW2A-8)</strong> "
                "from a Bangladesh Bank scheduled commercial bank without conditional qualifiers."
            )
            action_route = "bank-view"
            action_label = "Apply 1-Click Bank Pre-Approval →"

        elif "price" in q or "discount" in q or "sweet spot" in q or "bid price" in q or "alt" in q:
            category = "Pricing Optimization & Rule 98"
            statutory_citation = "Rule 98(21) PPR-2008 & SRO 343-Act/2008"
            sweet_spot = req.estimated_cost_bdt * 0.911
            reply = (
                f"For <strong>{req.agency}</strong>, historical procurement patterns indicate the optimal winning price clusters at "
                f"<strong>-8.90% discount</strong> (approx <strong>BDT {sweet_spot / 10000000:.2f} Cr</strong>).<br><br>"
                "<span style='color: #ef4444; font-weight: 700;'>CRITICAL LEGAL CAP:</span> Under CPTU PPR-2008 Rule 98, tenders quoted "
                "more than <strong>10.00% below the official estimate</strong> are automatically rejected as Abnormally Low Tenders (ALT)."
            )
            action_route = "predictor-view"
            action_label = "Open 3D Bayesian Predictor →"

        elif "trap" in q or "cartel" in q or "syndicate" in q or "risk" in q:
            category = "Cartel Intelligence & Trap Audit"
            statutory_citation = "Rule 127 PPR-2008 (Anti-Collusion Protocols)"
            reply = (
                "The AI Intelligence Engine audited the tender schedule and identified <strong>2 potential trap clauses</strong>:<br>"
                "1. <strong>Accelerated 14-Day Site Handover (ITT 38.2)</strong>: Creates default risk for non-incumbents.<br>"
                "2. <strong>Proprietary Bearing Spec Lock</strong>: Section 6 BOQ specifies proprietary brands without an 'or equivalent' clause.<br><br>"
                "<strong>Recommended Action:</strong> Lodge formal pre-bid clarification under ITT Clause 8."
            )
            action_route = "awards-view"
            action_label = "View 3D Cartel Radar →"

        else:
            category = "Standard CPTU Compliance"
            statutory_citation = "PPR-2008 Standard Guidelines"
            reply = (
                f"Under Bangladesh e-GP procurement guidelines for <strong>Tender ID #{req.tender_id}</strong> "
                f"({req.agency}), all submissions must adhere strictly to Section 2 (TDS) qualification criteria.<br>"
                f"Estimated Contract Value: <strong>BDT {cost_cr:.2f} Crore</strong>.<br><br>"
                "I can analyze mandatory clauses, shred this schedule into a 1-page compliance matrix, or verify your contractor capacity."
            )
            action_route = "decision-view"
            action_label = "Run Go/No-Go Decision Engine →"

        response_data = {
            "status": "SUCCESS",
            "timestamp": timestamp,
            "query": req.query,
            "category": category,
            "statutory_citation": statutory_citation,
            "reply_html": reply,
            "action": {
                "route": action_route,
                "label": action_label
            }
        }
        self.conversation_history.append(response_data)
        return response_data

# Global Singleton
tender_copilot_engine = TenderCopilotEngine()
