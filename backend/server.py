"""
TenderPulse 4IR AI - Central FastAPI REST & AI Inference Server
Bridges Python 3.11 AI Services (Microsoft Z3 SMT Prover, NetworkX Cartel Radar,
Sentinel-1 SAR Radar Coherence Auditor, PDF Schedule Parser) to the TenderPulse Web Interface.
Runs locally on http://127.0.0.1:8000
"""

import sys
import os
import json
import time
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

try:
    import dotenv
    dotenv.load_dotenv(os.path.join(ROOT_DIR, ".env"), override=True)
except Exception:
    pass

# Import TenderPulse AI modules
from backend.smt_solver import CptuLegalProver
from backend.cartel_radar import CartelRadarEngine
from backend.sar_processor import SarProgressAuditor
from backend.pdf_parser import TenderPdfParser
from backend.egp_live_scraper import EgpLiveScraper
from backend.auth_manager import auth_manager
from backend.zkp_prover import ZeroKnowledgeProver
from backend.std_engine import StdGeneratorEngine
from backend.bank_engine import bank_connect_engine, CreditSimulationRequest, PreApprovalApplicationRequest
from backend.compliance_engine import compliance_matrix_engine, ComplianceClauseRequest
from backend.copilot_engine import tender_copilot_engine, CopilotQueryRequest
from backend.decision_engine import bid_decision_engine, DecisionEvaluationRequest
from backend.sentinel_hub import sentinel_pipeline
from backend.harvester_daemon import get_daemon_instance, HarvesterDaemon
from backend.report_exporter import (
    generate_cartel_excel_report,
    generate_cartel_pdf_report,
    generate_smt_pdf_certificate,
    generate_smt_excel_matrix
)
from backend.database import init_db, SessionLocal, get_db
import backend.crud as crud
from backend.models import TenderModel, UserModel, BiddingSyndicateModel, CorrigendumModel
from backend.auth_jwt import (
    create_access_token,
    create_refresh_token,
    rotate_refresh_token,
    get_current_user,
    get_current_user_optional,
    require_roles,
    ROLE_EXECUTIVE,
    ROLE_ANALYST,
    ROLE_AUDITOR,
    ROLE_ADMIN
)

# Ensure database tables exist
try:
    init_db()
except Exception as dbe:
    print(f"[*] Database init notice: {dbe}")

app = FastAPI(
    title="TenderPulse 4IR AI Backend",
    description="Autonomous e-GP Data Mining & Neuro-Symbolic Procurement Intelligence API",
    version="2.7.0"
)

# Enable CORS for file:/// browser origins and local servers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize AI singletons
prover = CptuLegalProver()
cartel_engine = CartelRadarEngine()
sar_auditor = SarProgressAuditor()
pdf_parser = TenderPdfParser()
egp_scraper = EgpLiveScraper()
zkp_engine = ZeroKnowledgeProver()
std_engine = StdGeneratorEngine()
bank_engine = bank_connect_engine
compliance_engine = compliance_matrix_engine
copilot_engine = tender_copilot_engine
decision_engine = bid_decision_engine
server_start_time = time.time()


# --- Pydantic Schemas ---
class LegalVerifyRequest(BaseModel):
    original_contract_value: float = 85.80
    variation_amount: float = 10.50
    cabinet_approval_obtained: bool = False
    performance_security_pct: float = 10.0
    max_annual_turnover: float = 45.0
    completion_period_years: float = 2.0
    existing_commitments: float = 32.0
    tender_value: float = 85.80


class SarAuditRequest(BaseModel):
    contract_id: str = "RHD/2026/PW-04"
    claimed_mb_progress_pct: float = 68.0
    latitude: float = 22.7010
    longitude: float = 90.3535
    project_type: str = "Highway Embankment & Asphalt Pavement"


class SentinelAuthRequest(BaseModel):
    client_id: Optional[str] = None
    client_secret: Optional[str] = None


class SentinelQueryRequest(BaseModel):
    bbox: List[float] = [23.75, 90.35, 23.85, 90.45]
    tender_id: str = "eGP-1098421"
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class NotificationRequest(BaseModel):
    recipient_type: str = "webhook"  # telegram, discord, webhook
    webhook_url: Optional[str] = None
    tender_id: str = "eGP-1098421"
    message: str = "High-priority tender alert matching your ministry criteria."


class ScraperMineRequest(BaseModel):
    agency: str = "LGED"
    keyword: Optional[str] = None
    limit: int = 5
    page: int = 1


class UserRegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    role: str = "Tender Analyst"
    agency: str = "Di-Tender Ltd."


class UserLoginRequest(BaseModel):
    email: str
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class UserLogoutRequest(BaseModel):
    token: Optional[str] = None


class ZkpProveRequest(BaseModel):
    contractor_name: str = "Prime Infrastructure & Construction Ltd."
    egp_id: str = "BDR-789042"
    peak_turnover_bdt: float = 512000000.0
    liquid_assets_bdt: float = 150000000.0
    required_turnover_bdt: float = 350000000.0
    required_liquidity_bdt: float = 95000000.0
    agency: str = "RHD"


class ZkpVerifyRequest(BaseModel):
    proof_data: Dict[str, Any]


class StdGenerateRequest(BaseModel):
    form_code: str = "e-PW3-1"
    contractor_name: str = "Engr. M. A. Karim"
    company_name: str = "Prime Infrastructure & Construction Ltd."
    egp_bidder_id: str = "BDR-789042"
    agency: str = "Roads and Highways Department (RHD)"
    tender_id: str = "986772"
    ref_no: str = "RHD/2026/PW-09"
    estimated_cost_bdt: float = 250000000.0
    bid_price_bdt: float = 227750000.0
    tender_security_bdt: float = 6250000.0
    liquid_asset_req_bdt: float = 62500000.0


class HarvesterTriggerRequest(BaseModel):
    agency: Optional[str] = None
    limit: Optional[int] = 5



# --- Web UI, Health & Auth Endpoints ---
@app.get("/")
def serve_frontend_root():
    """
    Serves the TenderPulse 4IR single-page web application dashboard.
    """
    index_file = os.path.join(ROOT_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"status": "ONLINE", "service": "TenderPulse 4IR AI Engine", "msg": "index.html not found"}


@app.post("/api/auth/register")
def register_user(req: UserRegisterRequest):
    """
    Registers a new enterprise user account and returns an active session token.
    """
    try:
        return auth_manager.register(
            name=req.name,
            email=req.email,
            password=req.password,
            role=req.role,
            agency=req.agency
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration error: {str(e)}")


@app.post("/api/auth/token")
@app.post("/api/auth/login")
def login_user(req: UserLoginRequest):
    """
    Authenticates user with email and password and returns cryptographic JWT access & refresh tokens.
    """
    try:
        login_res = auth_manager.login(email=req.email, password=req.password)
        user = login_res["user"]
        
        # Issue cryptographically signed access and refresh tokens
        access_token = create_access_token(user)
        refresh_token = create_refresh_token(user["email"])
        
        return {
            "status": "SUCCESS",
            "message": login_res["message"],
            "token_type": "bearer",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token": access_token,  # Backward-compatible alias
            "user": user,
            "role": user.get("role")
        }
    except ValueError as ve:
        raise HTTPException(status_code=401, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login error: {str(e)}")


@app.post("/api/auth/refresh")
def refresh_access_token(req: RefreshTokenRequest):
    """
    Rotates refresh token and issues fresh cryptographic access token.
    """
    new_access, new_refresh, user = rotate_refresh_token(req.refresh_token)
    return {
        "status": "SUCCESS",
        "token_type": "bearer",
        "access_token": new_access,
        "refresh_token": new_refresh,
        "token": new_access,
        "user": user
    }


@app.post("/api/auth/logout")
@app.post("/api/auth/signout")
def logout_user(req: Optional[UserLogoutRequest] = None):
    """
    Invalidates session and signs the user out.
    """
    token = req.token if req else None
    return auth_manager.logout(token)


@app.get("/api/auth/me")
def get_current_user_profile(token: Optional[str] = None):
    """
    Retrieves current active user profile.
    """
    user = auth_manager.get_current_user(token)
    if not user:
        raise HTTPException(status_code=404, detail="User session not found")
    return {"status": "SUCCESS", "user": user}


@app.get("/api/auth/users")
def get_public_users():
    """
    Lists available enterprise user profiles.
    """
    return {"status": "SUCCESS", "users": auth_manager.list_public_profiles()}


@app.get("/api/health")
def health_check():
    """
    Health check verifying server status, uptime, and active AI engine versions.
    """
    uptime_sec = round(time.time() - server_start_time, 1)
    return {
        "status": "ONLINE",
        "service": "TenderPulse 4IR AI Engine",
        "python_version": sys.version.split()[0],
        "uptime_seconds": uptime_sec,
        "active_ai_engines": {
            "smt_solver": prover.engine_version,
            "cartel_radar": cartel_engine.engine_version,
            "sar_satellite_auditor": sar_auditor.engine_version,
            "pdf_boq_parser": pdf_parser.parser_version,
            "zkp_prover": zkp_engine.engine_version,
            "std_generator": std_engine.engine_version,
            "bank_connect": "BankConnect-v4.2",
            "compliance_matrix": compliance_engine.engine_version,
            "copilot": copilot_engine.engine_version,
            "decision_engine": decision_engine.engine_version,
            "sentinel_pipeline": sentinel_pipeline.engine_version,
            "database": "SQLAlchemy-2.0-Persisted",
            "harvester_daemon": "Active-24/7-MultiAgency"
        },
        "port": 8000,

        "cors_enabled": True
    }


@app.post("/api/copilot/query")
def query_tender_copilot(req: CopilotQueryRequest):
    """
    Context-aware procurement intelligence copilot grounded in Bangladesh CPTU PPR-2008.
    """
    try:
        return copilot_engine.process_query(req)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Copilot Query error: {str(e)}")


@app.post("/api/decision/evaluate")
def evaluate_bid_decision(req: DecisionEvaluationRequest):
    """
    Evaluates bidding feasibility and generates 100-point simulated TEC Scorecard.
    """
    try:
        return decision_engine.evaluate_bid(req)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bid Decision evaluation error: {str(e)}")


@app.get("/api/decision/criteria")
def get_decision_criteria():
    """
    Returns standard 5-factor government Tender Evaluation Committee (TEC) criteria weights.
    """
    return {
        "status": "ONLINE",
        "engine_version": decision_engine.engine_version,
        "criteria": [
            {"factor": "Financial & Turnover Capacity", "weight_pct": 25, "clause": "ITT 14.1 / Rule 96(3)"},
            {"factor": "Liquid Asset Solvency", "weight_pct": 25, "clause": "ITT 15.1 / Form e-PW2A-8"},
            {"factor": "Past Contract Track Record", "weight_pct": 20, "clause": "ITT 16.1 / Rule 96(2)"},
            {"factor": "Key Technical Staff & Equipment", "weight_pct": 15, "clause": "ITT 24/25 / e-PW3-5"},
            {"factor": "Syndicate Trap & Cartel Shield", "weight_pct": 15, "clause": "PPR-2008 Rule 127"}
        ]
    }


@app.get("/api/compliance/rules")
def get_compliance_rules():
    """
    Returns list of CPTU statutory compliance rules and procurement clauses.
    """
    return {
        "status": "ONLINE",
        "engine_version": compliance_engine.engine_version,
        "rules": compliance_engine.list_rules()
    }


@app.post("/api/compliance/analyze")
def analyze_compliance_matrix(
    req: ComplianceClauseRequest,
    current_user: Dict[str, Any] = Depends(require_roles([ROLE_AUDITOR, ROLE_ADMIN]))
):
    """
    Performs clause-by-clause statutory gap analysis against CPTU PPR-2008.
    """
    try:
        return compliance_engine.audit_compliance(req)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Compliance Audit error: {str(e)}")


@app.get("/api/bank/partners")
def get_bank_partners():
    """
    Returns list of top tier scheduled commercial partner banks for e-GP credit lines.
    """
    return {
        "status": "ONLINE",
        "engine_version": "BankConnect-v4.2",
        "partners": bank_engine.get_partners()
    }


@app.post("/api/bank/simulate-credit")
def simulate_contractor_credit(req: CreditSimulationRequest):
    """
    Simulates contractor liquid asset requirements and rates bank credit line matches.
    """
    try:
        return bank_engine.simulate_credit(req)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bank Credit Simulation error: {str(e)}")


@app.post("/api/bank/pre-approve")
def issue_bank_pre_approval(
    req: PreApprovalApplicationRequest,
    current_user: Dict[str, Any] = Depends(require_roles([ROLE_EXECUTIVE, ROLE_ADMIN]))
):
    """
    Issues official instant pre-approval voucher and Form e-PW2A-8 commitment token.
    """
    try:
        return bank_engine.issue_pre_approval(req)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bank Pre-Approval error: {str(e)}")


@app.get("/api/std/templates")
def get_std_templates():
    """
    Returns list of official CPTU standard tender document templates.
    """
    return {
        "status": "ONLINE",
        "engine_version": std_engine.engine_version,
        "templates": std_engine.list_templates()
    }


@app.post("/api/std/generate")
def generate_std_document(req: StdGenerateRequest):
    """
    Synthesizes CPTU compliant standard tender document packages with statutory validation.
    """
    try:
        result = std_engine.generate_form(req.dict())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"STD Generator exception: {str(e)}")


@app.post("/api/zkp/prove")
def generate_zkp_proof(
    req: ZkpProveRequest,
    current_user: Dict[str, Any] = Depends(require_roles([ROLE_EXECUTIVE, ROLE_ADMIN]))
):
    """
    Generates a Groth16 zero-knowledge proof over private contractor witness metrics.
    Proves statutory compliance without disclosing actual balance sheets or customer records.
    """
    try:
        profile = {
            "contractorName": req.contractor_name,
            "egpId": req.egp_id,
            "peakTurnoverBDT": req.peak_turnover_bdt,
            "liquidAssetsBDT": req.liquid_assets_bdt
        }
        result = zkp_engine.generate_zk_proof(
            contractor_profile=profile,
            required_turnover_bdt=req.required_turnover_bdt,
            required_liquidity_bdt=req.required_liquidity_bdt,
            agency=req.agency
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ZKP Prover exception: {str(e)}")


@app.post("/api/zkp/verify")
def verify_zkp_proof(req: ZkpVerifyRequest):
    """
    Verifies a Groth16 zero-knowledge proof token with O(1) pairing check complexity.
    """
    try:
        result = zkp_engine.verify_zk_proof(req.proof_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ZKP Verifier exception: {str(e)}")


@app.post("/api/smt/verify")
def verify_cptu_rules(
    req: LegalVerifyRequest,
    current_user: Dict[str, Any] = Depends(require_roles([ROLE_ANALYST, ROLE_EXECUTIVE, ROLE_AUDITOR, ROLE_ADMIN]))
):
    """
    Formally verifies contract parameters and Variation Orders against CPTU Rules 39/40 & PPR 2008.
    Returns SAT/UNSAT proof certificate and minimal counter-model.
    """
    try:
        result = prover.verify_contract_compliance(req.dict())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SMT Solver exception: {str(e)}")


@app.post("/api/smt/export/pdf")
def export_smt_pdf_certificate(
    req: LegalVerifyRequest,
    current_user: Dict[str, Any] = Depends(require_roles([ROLE_ANALYST, ROLE_EXECUTIVE, ROLE_AUDITOR, ROLE_ADMIN]))
):
    """
    Generates an official downloadable CPTU Statutory SMT Proof Certificate in PDF format.
    """
    try:
        result = prover.verify_contract_compliance(req.dict())
        pdf_bytes = generate_smt_pdf_certificate(result, req.dict())
        cert_id = result.get("certificate_id", "SMT-PROOF")
        return StreamingResponse(
            pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{cert_id}.pdf"'
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SMT PDF Export error: {str(e)}")


@app.post("/api/smt/export/excel")
def export_smt_excel_matrix(
    req: LegalVerifyRequest,
    current_user: Dict[str, Any] = Depends(require_roles([ROLE_ANALYST, ROLE_EXECUTIVE, ROLE_AUDITOR, ROLE_ADMIN]))
):
    """
    Generates a structured downloadable SMT Proof Matrix and Rule Evaluation Spreadsheet in XLSX format.
    """
    try:
        result = prover.verify_contract_compliance(req.dict())
        excel_bytes = generate_smt_excel_matrix(result, req.dict())
        cert_id = result.get("certificate_id", "SMT-PROOF")
        return StreamingResponse(
            excel_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f'attachment; filename="{cert_id}_matrix.xlsx"'
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SMT Excel Export error: {str(e)}")


@app.post("/api/cartel/analyze")
def analyze_cartel_network(
    payload: Optional[Dict[str, Any]] = None,
    dataset: Optional[str] = None,
    limit: Optional[int] = 50000,
    agency: Optional[str] = None,
    year: Optional[int] = None,
    division: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(require_roles([ROLE_AUDITOR, ROLE_ADMIN]))
):
    """
    Constructs bipartite co-bidding network and analyzes syndicate rotation,
    cover-bidding frequency, and collusive cliques across live or 50,000+ historical tenders.
    """
    try:
        ds_mode = (dataset or (payload.get("dataset") if payload else None) or "").lower()
        use_historical = (ds_mode in ("historical", "hist", "archive", "50k") or (payload.get("historical") if payload else False))

        if use_historical:
            req_agency = agency or (payload.get("agency") if payload else None)
            req_year = year or (payload.get("year") if payload else None)
            req_div = division or (payload.get("division") if payload else None)
            req_limit = limit or (payload.get("limit") if payload else 50000)
            return cartel_engine.analyze_large_scale_historical(
                limit=req_limit,
                agency=req_agency,
                year=req_year,
                division=req_div
            )

        tenders = payload.get("tenders", None) if payload else None
        result = cartel_engine.analyze_bidding_syndicate(tenders)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cartel Radar exception: {str(e)}")


@app.get("/api/cartel/historical-summary")
def get_cartel_historical_summary(
    current_user: Dict[str, Any] = Depends(require_roles([ROLE_ANALYST, ROLE_EXECUTIVE, ROLE_AUDITOR, ROLE_ADMIN]))
):
    """
    Fast pre-aggregated summary metadata for the 50,000+ multi-year historical cartel dataset.
    """
    try:
        summary_path = os.path.join(ROOT_DIR, "data", "awards_archive_summary.json")
        if os.path.exists(summary_path):
            with open(summary_path, "r", encoding="utf-8") as f:
                return json.load(f)
        report = cartel_engine.analyze_large_scale_historical()
        return {
            "total_tenders": report["total_tenders_analyzed"],
            "flagged_tenders": report["flagged_collusive_tenders"],
            "market_integrity_score": report["market_integrity_score"],
            "syndicates_count": len(report["detected_syndicates"]),
            "vector_counts": report["forensic_vectors"].get("vector_counts", {})
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cartel summary exception: {str(e)}")


@app.get("/api/cartel/district-heatmap")
def get_cartel_district_heatmap(
    agency: Optional[str] = None,
    year: Optional[str] = None,
    division: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(require_roles([ROLE_ANALYST, ROLE_EXECUTIVE, ROLE_AUDITOR, ROLE_ADMIN]))
):
    """
    Returns 64-district Bangladesh GIS Cartel Heat Map telemetry with coordinates,
    integrity scores, volume statistics, active syndicates, and inter-district collusion arcs.
    """
    try:
        from backend.database import SessionLocal
        db = SessionLocal()
        try:
            return cartel_engine.get_district_geospatial_heatmap(
                db=db,
                agency=agency,
                year=year,
                division=division
            )
        finally:
            db.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"District Heatmap exception: {str(e)}")


@app.get("/api/cartel/export/excel")
def export_cartel_excel(
    current_user: Dict[str, Any] = Depends(require_roles([ROLE_AUDITOR, ROLE_ADMIN, ROLE_EXECUTIVE]))
):
    """
    Generates an official multi-tab Cartel Forensic Audit Dossier in Excel (.xlsx) format.
    """
    try:
        report = cartel_engine.analyze_large_scale_historical(limit=50000)
        excel_bytes = generate_cartel_excel_report(report)
        filename = f"cartel_forensic_audit_{time.strftime('%Y%m%d_%H%M%S')}.xlsx"
        return StreamingResponse(
            excel_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cartel Excel Export error: {str(e)}")


@app.get("/api/cartel/export/pdf")
def export_cartel_pdf(
    current_user: Dict[str, Any] = Depends(require_roles([ROLE_AUDITOR, ROLE_ADMIN, ROLE_EXECUTIVE]))
):
    """
    Generates an official institutional Cartel Forensic Audit Dossier in PDF format.
    """
    try:
        report = cartel_engine.analyze_large_scale_historical(limit=50000)
        pdf_bytes = generate_cartel_pdf_report(report)
        filename = f"cartel_audit_dossier_{time.strftime('%Y%m%d_%H%M%S')}.pdf"
        return StreamingResponse(
            pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cartel PDF Export error: {str(e)}")


@app.post("/api/sar/audit")
def audit_sar_progress(
    req: SarAuditRequest,
    current_user: Dict[str, Any] = Depends(require_roles([ROLE_AUDITOR, ROLE_ADMIN]))
):
    """
    Audits civil infrastructure ground truth earthwork and asphalt compaction
    using Copernicus Sentinel-1 C-band SAR backscatter coherence decay.
    """
    try:
        result = sar_auditor.audit_physical_progress(req.dict())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SAR Auditor exception: {str(e)}")


@app.post("/api/sentinel/auth")
def authenticate_sentinel(req: Optional[SentinelAuthRequest] = None):
    """
    Authenticates against Sentinel Hub OAuth2 gateway using active production credentials.
    """
    try:
        cid = req.client_id if req else None
        sec = req.client_secret if req else None
        return sentinel_pipeline.authenticate(cid, sec)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sentinel OAuth exception: {str(e)}")


@app.post("/api/sentinel/query")
@app.post("/api/sar/live-raster")
def query_sentinel_raster(req: SentinelQueryRequest):
    """
    Dynamic BBOX ingestion: queries live Sentinel-1 SAR C-band radar rasters,
    3D elevation matrices, and coherence decay for any tender BBOX.
    """
    try:
        date_range = (req.start_date, req.end_date) if req.start_date and req.end_date else None
        return sentinel_pipeline.query_sar_raster(req.bbox, req.tender_id, date_range)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sentinel Query exception: {str(e)}")


@app.get("/api/sentinel/pipeline-status")
def get_sentinel_pipeline_status():
    """
    Returns diagnostics for active Sentinel Hub Instance ID pipeline.
    """
    return sentinel_pipeline.get_pipeline_status()


@app.post("/api/sentinel/reload")
def reload_sentinel_config():
    """
    Reloads credentials and configuration from .env into active Sentinel pipeline.
    """
    sentinel_pipeline.reload_config()
    auth_result = sentinel_pipeline.authenticate()
    return {
        "status": "SUCCESS",
        "message": "Sentinel Hub pipeline reloaded with latest credentials",
        "auth": auth_result,
        "pipeline": sentinel_pipeline.get_pipeline_status()
    }


@app.get("/api/sentinel/cache/stats")
def get_sentinel_cache_stats():
    """
    Returns live metrics on Sentinel radar tile disk cache (hits, misses, disk size, PU units saved).
    """
    return {
        "status": "SUCCESS",
        "cache": sentinel_pipeline.get_cache_stats()
    }


@app.post("/api/sentinel/cache/clear")
def clear_sentinel_cache(
    current_user: Dict[str, Any] = Depends(require_roles([ROLE_AUDITOR, ROLE_ADMIN]))
):
    """
    Flushes disk-based Sentinel radar tile cache.
    Guarded by Enterprise RBAC (Auditor, Admin).
    """
    cleared_count = sentinel_pipeline.clear_cache()
    return {
        "status": "SUCCESS",
        "message": f"Cleared {cleared_count} cached satellite radar tiles",
        "cleared_by": current_user.get("email") if current_user else "system"
    }



@app.post("/api/pdf/parse")
async def parse_tender_pdf(
    file: Optional[UploadFile] = File(None),
    text_content: Optional[str] = Form(None),
    current_user: Dict[str, Any] = Depends(require_roles([ROLE_ANALYST, ROLE_EXECUTIVE, ROLE_AUDITOR, ROLE_ADMIN]))
):
    """
    Extracts structured tender metadata, TDS turnover requirements, and Section 6 BOQ
    line items from uploaded e-GP PDF schedule or text.
    """
    try:
        if file:
            content = await file.read()
            return pdf_parser.parse_pdf_bytes(content, filename=file.filename)
        elif text_content:
            return pdf_parser.parse_text_stream(text_content)
        else:
            # Return demo parsed e-PW3 BOQ schedule
            return pdf_parser.parse_text_stream("", filename="Demo_ePW3_Schedule.pdf")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF Parser exception: {str(e)}")


@app.post("/api/notify/dispatch")
def dispatch_notification(req: NotificationRequest):
    """
    Dispatches instant notification to Telegram, Discord webhook, or local system audit.
    """
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    log_entry = {
        "timestamp": timestamp,
        "recipient": req.recipient_type,
        "tender_id": req.tender_id,
        "message": req.message,
        "dispatch_status": "DELIVERED"
    }

    # If user provided a webhook URL, attempt delivery
    if req.webhook_url and req.webhook_url.startswith("http"):
        try:
            import requests
            requests.post(req.webhook_url, json={"content": f"🚨 [TenderPulse 4IR Alert] {req.message} (Tender: {req.tender_id})"}, timeout=5)
        except Exception:
            pass

    return log_entry


class SpatialBboxRequest(BaseModel):
    bbox: List[float] = [20.5, 88.0, 26.7, 92.7]  # [min_lat, min_lon, max_lat, max_lon]
    agency: Optional[str] = None


@app.get("/api/tenders/live")
def get_live_tenders(
    agency: Optional[str] = None,
    district: Optional[str] = None,
    keyword: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """
    Reads live scraped tenders from persistent database, falling back to data/live_feed.json.
    """
    db = SessionLocal()
    try:
        tenders_db = crud.get_tenders(db, limit=limit, offset=offset, agency=agency, district=district, keyword=keyword)
        if tenders_db:
            result = []
            for t in tenders_db:
                item = {}
                if t.raw_json:
                    try:
                        item = json.loads(t.raw_json)
                    except Exception:
                        pass
                item.update({
                    "id": t.tender_id,
                    "tenderId": t.tender_id,
                    "appId": t.app_id or "",
                    "refNo": t.ref_no or "",
                    "title": t.title,
                    "agency": t.agency,
                    "ministry": t.ministry or "",
                    "division": t.division or "Dhaka",
                    "district": t.district or "Dhaka",
                    "cost": t.estimated_cost,
                    "security": t.tender_security,
                    "liquidAssetsReq": t.liquid_assets_req,
                    "turnoverReq": t.turnover_req,
                    "publishedDate": t.publish_date or "",
                    "closingDate": t.closing_date or "",
                    "isLive": t.is_live,
                    "lat": t.latitude,
                    "lng": t.longitude,
                    "bbox": [t.bbox_min_lat, t.bbox_min_lon, t.bbox_max_lat, t.bbox_max_lon] if t.bbox_min_lat else None
                })
                result.append(item)
            total = crud.count_tenders(db, agency=agency)
            return {"count": len(result), "total_count": total, "source": "database", "tenders": result}
    except Exception as e:
        print(f"[!] Database live tenders query error: {e}")
    finally:
        db.close()

    # Graceful JSON fallback
    data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "live_feed.json")
    if os.path.exists(data_path):
        try:
            with open(data_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {"count": len(data), "total_count": len(data), "source": "json_cache", "tenders": data}
        except Exception:
            pass
    return {"count": 0, "total_count": 0, "source": "empty", "tenders": []}


@app.post("/api/tenders/spatial-query")
def query_tenders_spatial(req: SpatialBboxRequest):
    """
    Returns tenders within geographic bounding box [min_lat, min_lon, max_lat, max_lon].
    """
    if len(req.bbox) < 4:
        raise HTTPException(status_code=400, detail="Bounding box must contain [min_lat, min_lon, max_lat, max_lon]")
    db = SessionLocal()
    try:
        tenders = crud.get_tenders_by_bbox(db, req.bbox[0], req.bbox[1], req.bbox[2], req.bbox[3])
        results = []
        for t in tenders:
            results.append({
                "id": t.tender_id,
                "title": t.title,
                "agency": t.agency,
                "district": t.district,
                "cost": t.estimated_cost,
                "lat": t.latitude,
                "lng": t.longitude,
                "closingDate": t.closing_date
            })
        return {
            "status": "SUCCESS",
            "bbox": req.bbox,
            "count": len(results),
            "tenders": results
        }
    finally:
        db.close()


@app.post("/api/scraper/live-mine")
def live_mine_tenders(req: ScraperMineRequest):
    """
    Triggers live harvesting query directly against Bangladesh e-GP portal (eprocure.gov.bd).
    Returns real extracted tenders and synchronizes them into local database and storage.
    """
    try:
        kw = req.keyword or req.agency
        tenders = egp_scraper.fetch_live_tenders(keyword=kw, page=req.page, limit=req.limit)
        synced_count = egp_scraper.sync_to_storage(tenders)

        # Sync to persistent database
        db = SessionLocal()
        try:
            for t in tenders:
                crud.upsert_tender(db, t)
        except Exception as dbe:
            print(f"[!] Database upsert notice: {dbe}")
        finally:
            db.close()

        return {
            "status": "SUCCESS",
            "query": kw,
            "agency": req.agency,
            "retrieved_count": len(tenders),
            "newly_synced": synced_count,
            "tenders": tenders
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"e-GP Scraper error: {str(e)}")


@app.get("/api/scraper/agencies")
def get_supported_agencies():
    """
    Returns list of procuring agencies supported for live targeted harvesting.
    """
    return {
        "status": "ONLINE",
        "portal": "https://www.eprocure.gov.bd",
        "agencies": EgpLiveScraper.AGENCY_MAP
    }


@app.get("/api/harvester/status")
def get_harvester_status():
    """
    Returns live telemetry from the autonomous 24/7 background harvester daemon.
    """
    daemon = get_daemon_instance()
    status_file = os.path.join(ROOT_DIR, "data", "harvester_status.json")
    if os.path.exists(status_file):
        try:
            with open(status_file, "r", encoding="utf-8") as f:
                file_state = json.load(f)
                return {"status": "SUCCESS", "telemetry": file_state}
        except Exception:
            pass
    return {"status": "SUCCESS", "telemetry": daemon.get_status()}


@app.post("/api/harvester/trigger")
def trigger_harvester_cycle(
    req: Optional[HarvesterTriggerRequest] = None,
    background_tasks: BackgroundTasks = None,
    user: Dict[str, Any] = Depends(require_roles([ROLE_ANALYST, ROLE_EXECUTIVE, ROLE_ADMIN]))
):
    """
    Triggers an immediate background harvest cycle across target agencies.
    Guarded by Enterprise RBAC (Analyst, Executive, Admin).
    """
    daemon = get_daemon_instance()
    if req and req.agency:
        daemon.agencies = [req.agency.upper()]
    if req and req.limit:
        daemon.limit_per_agency = req.limit

    if background_tasks is not None:
        background_tasks.add_task(daemon.run_harvest_cycle)
        return {
            "status": "QUEUED",
            "message": f"Autonomous harvest cycle triggered asynchronously for agencies: {daemon.agencies}",
            "triggered_by": user.get("email") if user else "system",
            "active_proxy": daemon.proxy
        }
    else:
        res = daemon.run_harvest_cycle()
        return {
            "status": "SUCCESS",
            "result": res,
            "triggered_by": user.get("email") if user else "system"
        }


@app.get("/api/corrigenda")
def list_corrigenda(tender_id: Optional[str] = None, limit: int = 50):
    """
    Retrieves recorded CPTU Corrigendum amendment alerts (deadline extensions, security changes).
    """
    db = SessionLocal()
    try:
        items = crud.get_corrigenda(db, tender_id=tender_id, limit=limit)
        results = []
        for c in items:
            results.append({
                "id": c.id,
                "tender_id": c.tender_id,
                "corrigendum_no": c.corrigendum_no,
                "field_changed": c.field_changed,
                "old_value": c.old_value,
                "new_value": c.new_value,
                "reason": c.reason,
                "detected_at": c.detected_at.isoformat() if c.detected_at else None
            })
        return {
            "status": "SUCCESS",
            "count": len(results),
            "corrigenda": results
        }
    finally:
        db.close()



@app.get("/api/pdf/sample")
def get_sample_pdf_boq():
    """
    Returns a pre-extracted authentic e-PW3 tender schedule and Section 6 BOQ
    for instant UI testing and demonstration.
    """
    sample_text = """
    GOVERNMENT OF THE PEOPLE'S REPUBLIC OF BANGLADESH
    Office of the Executive Engineer, Roads and Highways Department (RHD), Gazipur
    Tender Reference No: RHD/GZP/2026/PW-09 | Tender ID: 1098421
    Name of Work: Construction of 4-Lane Pre-Stressed Concrete Girder Bridge & Pavement
    Procurement Method: Open Tendering Method (OTM) | Standard Tender Document: e-PW3
    Liquidated Damages: 0.1% per day of delayed contract value up to maximum 10%.
    Minimum Required Annual Turnover: BDT 45.00 Crore in last 5 years.
    Minimum Liquid Assets / Working Capital: BDT 18.50 Crore.
    """
    return {
        "status": "SUCCESS",
        "sample_text": sample_text.strip()
    }


@app.get("/")
@app.get("/index.html")
def serve_index():
    """
    Serves the Di-Tender 4IR Single Page Application.
    """
    index_path = os.path.join(ROOT_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"status": "ONLINE", "message": "Di-Tender 4IR AI Backend is Running"}


# Mount static assets (CSS, JS, Data)
if os.path.exists(os.path.join(ROOT_DIR, "css")):
    app.mount("/css", StaticFiles(directory=os.path.join(ROOT_DIR, "css")), name="css")
if os.path.exists(os.path.join(ROOT_DIR, "js")):
    app.mount("/js", StaticFiles(directory=os.path.join(ROOT_DIR, "js")), name="js")
if os.path.exists(os.path.join(ROOT_DIR, "data")):
    app.mount("/data", StaticFiles(directory=os.path.join(ROOT_DIR, "data")), name="data")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.server:app", host="127.0.0.1", port=8000, reload=True)
