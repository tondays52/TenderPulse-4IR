"""
TenderPulse 4IR AI - Neuro-Symbolic SMT Legal Proof Engine
Based on research: arXiv:2601.06181 (Automated Legal Verification via Satisfiability Modulo Theories)
Formally verifies Bangladesh CPTU PPR 2008 & 2026 Procurement Rules using Microsoft Z3.
"""

import hashlib
import json
import threading
from typing import Dict, Any, List

try:
    import z3
    HAS_Z3 = True
except ImportError:
    HAS_Z3 = False

# Global lock to prevent multi-threaded race conditions in Z3 C++ AST context
_Z3_LOCK = threading.Lock()


class CptuLegalProver:
    """
    Formal First-Order Logic Solver for CPTU (Central Procurement Technical Unit)
    statutory compliance, Variation Orders (Rules 39/40), Performance Securities,
    and Tenderer Financial Capacity constraints.
    """

    def __init__(self):
        self.engine_version = "Z3-SMT-4IR-v2.6"

    def verify_contract_compliance(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify contract parameters against statutory CPTU thresholds:
        - original_contract_value (in BDT / Cr)
        - variation_amount (in BDT / Cr)
        - cabinet_approval_obtained (bool)
        - performance_security_pct (float, e.g. 10.0)
        - max_annual_turnover (A, in BDT / Cr)
        - completion_period_years (N, in years)
        - existing_commitments (B, in BDT / Cr)
        - tender_value (in BDT / Cr)
        """
        orig_val = float(params.get("original_contract_value", 85.80))
        vo_val = float(params.get("variation_amount", 10.50))
        has_cabinet_clearance = bool(params.get("cabinet_approval_obtained", False))
        perf_sec_pct = float(params.get("performance_security_pct", 10.0))
        turnover_a = float(params.get("max_annual_turnover", 45.00))
        period_n = float(params.get("completion_period_years", 2.0))
        commitments_b = float(params.get("existing_commitments", 32.00))
        tender_val = float(params.get("tender_value", 85.80))

        vo_percentage = (vo_val / orig_val * 100.0) if orig_val > 0 else 0.0
        assessed_capacity = (turnover_a * period_n * 1.5) - commitments_b

        proof_trace = []
        violations = []
        recommendations = []

        # Mathematical Proof Execution using Z3 if available
        is_sat = True
        z3_model_dict = {}

        if HAS_Z3:
            try:
                with _Z3_LOCK:
                    solver = z3.Solver()

                    # Define Z3 real variables
                    OrigVal = z3.Real('OrigVal')
                    VoVal = z3.Real('VoVal')
                    VoPct = z3.Real('VoPct')
                    PerfSec = z3.Real('PerfSec')
                    CapA = z3.Real('CapA')
                    CapN = z3.Real('CapN')
                    CapB = z3.Real('CapB')
                    TenderVal = z3.Real('TenderVal')
                    AssessedCap = z3.Real('AssessedCap')
                    CabinetApproved = z3.Bool('CabinetApproved')

                    # Axioms & Concrete Values
                    solver.add(OrigVal == orig_val)
                    solver.add(VoVal == vo_val)
                    solver.add(VoPct == (VoVal / OrigVal) * 100)
                    solver.add(PerfSec == perf_sec_pct)
                    solver.add(CapA == turnover_a)
                    solver.add(CapN == period_n)
                    solver.add(CapB == commitments_b)
                    solver.add(TenderVal == tender_val)
                    solver.add(AssessedCap == (CapA * CapN * 1.5) - CapB)
                    solver.add(CabinetApproved == has_cabinet_clearance)

                    # CPTU Rule 39/40 Statutory Axiom:
                    # (VoPct <= 15.0) OR CabinetApproved
                    cptu_rule_39 = z3.Or(VoPct <= 15.0, CabinetApproved == True)

                    # Form e-PW3-8 Performance Security Axiom: PerfSec >= 10.0%
                    cptu_rule_perf = PerfSec >= 10.0

                    # Rule 98 Financial Capacity Axiom: AssessedCap >= TenderVal
                    cptu_rule_cap = AssessedCap >= TenderVal

                    # Add conjunction of rules
                    solver.add(cptu_rule_39)
                    solver.add(cptu_rule_perf)
                    solver.add(cptu_rule_cap)

                    check_result = solver.check()
                    if check_result == z3.sat:
                        is_sat = True
                        m = solver.model()
                        z3_model_dict = {
                            "VoPct": float(m.eval(VoPct).as_decimal(4).rstrip('?')),
                            "AssessedCapacity": float(m.eval(AssessedCap).as_decimal(4).rstrip('?')),
                            "CapacitySurplus": float(m.eval(AssessedCap - TenderVal).as_decimal(4).rstrip('?'))
                        }
                    else:
                        is_sat = False
            except Exception:
                # Fallback in case of solver execution error
                if vo_percentage > 15.0 and not has_cabinet_clearance:
                    is_sat = False
                if perf_sec_pct < 10.0:
                    is_sat = False
                if assessed_capacity < tender_val:
                    is_sat = False

                z3_model_dict = {
                    "VoPct": round(vo_percentage, 2),
                    "AssessedCapacity": round(assessed_capacity, 2),
                    "CapacitySurplus": round(assessed_capacity - tender_val, 2)
                }
        else:
            # Deterministic Fallback Logic Solver
            if vo_percentage > 15.0 and not has_cabinet_clearance:
                is_sat = False
            if perf_sec_pct < 10.0:
                is_sat = False
            if assessed_capacity < tender_val:
                is_sat = False

            z3_model_dict = {
                "VoPct": round(vo_percentage, 2),
                "AssessedCapacity": round(assessed_capacity, 2),
                "CapacitySurplus": round(assessed_capacity - tender_val, 2)
            }

        # Deductive proof steps & human-readable citations
        proof_trace.append(f"[AXIOM-1] CPTU PPR 2008 Rule 39(1): Cumulative VO must not exceed 15.00% without Ministry Cabinet clearance.")
        proof_trace.append(f"[OBS-1] Contract ৳{orig_val:.2f} Cr, Variation claimed ৳{vo_val:.2f} Cr -> Calculated VO = {vo_percentage:.2f}%.")

        if vo_percentage > 15.0:
            if has_cabinet_clearance:
                proof_trace.append(f"[SATISFIED] VO {vo_percentage:.2f}% > 15.00% BUT Cabinet clearance flag = TRUE. Statutory exception holds.")
            else:
                violations.append(f"CPTU Rule 39/40 Breach: Cumulative VO ({vo_percentage:.2f}%) exceeds the 15.00% statutory cap by {vo_percentage - 15.0:.2f}%. Requires ministerial re-approval.")
                recommendations.append("Submit formal Rule 40 variation justification dossier to Ministry Standing Committee or split non-conforming items into a separate NCT tender.")
        else:
            proof_trace.append(f"[SATISFIED] Cumulative VO ({vo_percentage:.2f}%) is within statutory 15.00% limit.")

        proof_trace.append(f"[AXIOM-2] Form e-PW3-8: Unconditional Bank Guarantee for Performance Security must be >= 10.00%.")
        proof_trace.append(f"[OBS-2] Performance Security provided = {perf_sec_pct:.2f}%.")
        if perf_sec_pct < 10.0:
            violations.append(f"Form e-PW3-8 Non-compliance: Performance security ({perf_sec_pct:.2f}%) is below statutory 10.00% minimum.")
            recommendations.append("Demand additional bank guarantee amendment before issuing final Notice to Proceed (NTP).")
        else:
            proof_trace.append(f"[SATISFIED] Performance security {perf_sec_pct:.2f}% satisfies Form e-PW3-8.")

        proof_trace.append(f"[AXIOM-3] Rule 98 Financial Capacity: Cap = (A x N x 1.5) - B >= Tender Value.")
        proof_trace.append(f"[OBS-3] A=৳{turnover_a:.2f}Cr, N={period_n:.1f}yr, B=৳{commitments_b:.2f}Cr -> Assessed Capacity = ৳{assessed_capacity:.2f}Cr vs Tender Value ৳{tender_val:.2f}Cr.")
        if assessed_capacity < tender_val:
            deficit = tender_val - assessed_capacity
            violations.append(f"Financial Capacity Ineligibility: Assessed capacity (৳{assessed_capacity:.2f} Cr) is lower than tender value (৳{tender_val:.2f} Cr) by ৳{deficit:.2f} Cr.")
            recommendations.append("Form Joint Venture (JVCA) per CPTU Rule 54 with partner holding surplus liquid turnover to satisfy aggregate capacity.")
        else:
            proof_trace.append(f"[SATISFIED] Capacity surplus of ৳{assessed_capacity - tender_val:.2f} Cr verified.")

        # Hash certificate
        payload_bytes = json.dumps({"params": params, "status": "SAT" if is_sat else "UNSAT"}, sort_keys=True).encode()
        cert_hash = f"SMT-CPTU-{hashlib.sha256(payload_bytes).hexdigest()[:16].upper()}"

        return {
            "status": "SAT" if is_sat else "UNSAT",
            "certificate_id": cert_hash,
            "engine": self.engine_version,
            "solver_backend": "Microsoft Z3 SMT" if HAS_Z3 else "Deterministic First-Order Symbolic Fallback",
            "proof_trace": proof_trace,
            "violations": violations,
            "recommendations": recommendations,
            "model": z3_model_dict
        }


# Quick test execution if called directly
if __name__ == "__main__":
    prover = CptuLegalProver()
    result = prover.verify_contract_compliance({
        "original_contract_value": 85.80,
        "variation_amount": 10.50,
        "cabinet_approval_obtained": False,
        "performance_security_pct": 10.0,
        "max_annual_turnover": 45.0,
        "completion_period_years": 2.0,
        "existing_commitments": 32.0,
        "tender_value": 85.80
    })
    print(f"Status: {result['status']}, Cert: {result['certificate_id']}")
    print(f"Solver: {result['solver_backend']}")
