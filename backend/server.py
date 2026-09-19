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
import csv
import hashlib
import re
import uuid
import tempfile
import zipfile
from io import StringIO
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends, BackgroundTasks
from fastapi.websockets import WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.background import BackgroundTask
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVIDENCE_DIR = os.getenv("BID_EVIDENCE_DIR", os.path.join(ROOT_DIR, "private_evidence"))
EVIDENCE_FILE_TYPES = {
    ".pdf": "application/pdf", ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xls": "application/vnd.ms-excel",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
}

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
from backend.live_ingestion import live_broadcaster
from backend.report_exporter import (
    generate_cartel_excel_report,
    generate_cartel_pdf_report,
    generate_smt_pdf_certificate,
    generate_smt_excel_matrix
)
from backend.database import init_db, SessionLocal, get_db
from backend.settings import get_settings
from backend.observability import RequestLoggingMiddleware, configure_structured_logging
from backend.provenance import annotate_tender, provenance_summary
from backend.opportunity_scoring import rank_tenders
import backend.crud as crud
from backend.models import TenderModel, UserModel, BiddingSyndicateModel, CorrigendumModel, CorrigendumReviewModel, AlertPreferenceModel, TeamAlertPolicyModel, BidPipelineItemModel, BidReadinessProfileModel, BidPreparationTaskModel, BidActivityEventModel, BidTaskAttachmentModel, BidSubmissionApprovalModel, BidOutcomeModel, ExecutiveKpiSummaryModel, AuditRetentionPolicyModel, DocumentRequirementReviewModel
from backend.executive_reporting import ensure_daily_executive_summary, serialize_executive_summary, _as_datetime
from backend.document_requirements import extract_explicit_requirements
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

settings = get_settings()
configure_structured_logging()

app = FastAPI(
    title="TenderPulse 4IR AI Backend",
    description="Autonomous e-GP Data Mining & Neuro-Symbolic Procurement Intelligence API",
    version="2.8.0"
)


@app.on_event("startup")
async def _on_startup():
    """Auto-start the live e-GP tender broadcast stream on server startup."""
    live_broadcaster.start()


@app.on_event("shutdown")
async def _on_shutdown():
    """Gracefully stop the live broadcast stream."""
    live_broadcaster.stop()

# CORS is opt-in in production.  Same-origin dashboard traffic needs no CORS.
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=bool(settings.cors_origins and settings.cors_origins != ("*",)),
    allow_methods=["*"],
    allow_headers=["*"],
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add baseline browser protections without blocking the existing SPA."""

    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        return response


app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware)

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


class CorrigendumReviewRequest(BaseModel):
    status: str
    note: Optional[str] = None


class AlertPreferenceRequest(BaseModel):
    agencies: List[str] = []
    alert_types: List[str] = ["closing_date", "tender_security"]
    deadline_window_hours: int = 72
    requested_external_channel: str = "in_app"


class BidPipelineItemRequest(BaseModel):
    tender_id: str
    tender_title: str
    agency: Optional[str] = None
    owner_email: Optional[str] = None
    stage: str = "review"
    internal_due_date: Optional[str] = None
    decision: Optional[str] = None
    next_action: Optional[str] = None
    notes: Optional[str] = None


class BidPreparationTaskRequest(BaseModel):
    title: str
    owner_email: Optional[str] = None
    due_date: Optional[str] = None
    is_required: bool = True
    status: str = "open"
    blocker: Optional[str] = None


class BidPreparationTaskUpdateRequest(BaseModel):
    title: Optional[str] = None
    owner_email: Optional[str] = None
    due_date: Optional[str] = None
    is_required: Optional[bool] = None
    status: Optional[str] = None
    blocker: Optional[str] = None


class BidSubmissionApprovalRequest(BaseModel):
    status: str
    note: Optional[str] = None


class BidOutcomeRequest(BaseModel):
    status: str = "submitted"
    submission_reference: Optional[str] = None
    submitted_at: Optional[str] = None
    outcome_date: Optional[str] = None
    awarded_contract_value: Optional[float] = None
    lessons_learned: Optional[str] = None


class BidReadinessProfileRequest(BaseModel):
    contractor_name: str
    peak_turnover_bdt: float = 0
    active_commitments_bdt: float = 0
    available_credit_bdt: float = 0
    past_similar_max_bdt: float = 0
    engineers_count: int = 0


class AuditRetentionPolicyRequest(BaseModel):
    retention_days: int


class DocumentRequirementTaskRequest(BaseModel):
    title: str
    source_excerpt: str
    owner_email: Optional[str] = None
    due_date: Optional[str] = None

class DocumentRequirementReviewRequest(BaseModel):
    status: str


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
    except PermissionError as pe:
        raise HTTPException(status_code=403, detail=str(pe))
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


@app.get("/api/health/ready")
def readiness_check():
    """Readiness check used by Compose and external uptime monitors."""
    from sqlalchemy import text
    from backend.database import engine
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database readiness check failed") from exc
    return {"status": "READY", "database": "reachable"}


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
            if len(content) > settings.max_upload_bytes:
                raise HTTPException(status_code=413, detail="Uploaded file exceeds the configured size limit.")
            return pdf_parser.parse_pdf_bytes(content, filename=file.filename)
        elif text_content:
            return pdf_parser.parse_text_stream(text_content)
        else:
            # Return demo parsed e-PW3 BOQ schedule
            return pdf_parser.parse_text_stream("", filename="Demo_ePW3_Schedule.pdf")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF Parser exception: {str(e)}")


@app.post("/api/bid-pipeline/{tender_id}/document-requirements")
async def extract_document_requirements(
    tender_id: str,
    file: Optional[UploadFile] = File(None),
    text_content: Optional[str] = Form(None),
    current_user: Dict[str, Any] = Depends(require_roles([ROLE_ANALYST, ROLE_EXECUTIVE, ROLE_ADMIN])),
):
    """Extract source-backed clauses from pasted tender text or an uploaded PDF."""
    db = SessionLocal()
    try:
        if not db.query(BidPipelineItemModel.id).filter(BidPipelineItemModel.tender_id == tender_id).first():
            raise HTTPException(status_code=404, detail="Pipeline tender not found")
        page_texts = []
        if file:
            if not (file.filename or "").lower().endswith(".pdf"):
                raise HTTPException(status_code=415, detail="Document review accepts PDF files only")
            content = await file.read(settings.max_upload_bytes + 1)
            if len(content) > settings.max_upload_bytes:
                raise HTTPException(status_code=413, detail="Uploaded file exceeds the configured size limit")
            parsed = pdf_parser.parse_pdf_bytes(content, filename=file.filename or "tender.pdf")
            page_texts = parsed.get("page_texts", [])
            source_text = "\n".join(item.get("text", "") for item in page_texts)
            if not source_text.strip():
                raise HTTPException(status_code=422, detail="No extractable text was found in the uploaded PDF")
        else:
            source_text = (text_content or "").strip()
            if not source_text:
                raise HTTPException(status_code=400, detail="Paste tender text or upload a PDF")
            if len(source_text) > 200000:
                raise HTTPException(status_code=413, detail="Document text exceeds the review limit")

        requirements = extract_explicit_requirements(source_text, page_texts)
        persisted = []
        for item in requirements:
            row = DocumentRequirementReviewModel(
                tender_id=tender_id,
                requirement_key=item["key"],
                source_excerpt=item["source_excerpt"],
                source_page=item.get("source_page"),
            )
            db.add(row)
            persisted.append(row)
        db.commit()
        return {"status": "SUCCESS", "tender_id": tender_id, "requirements": [{"id": item.id, "key": item.requirement_key, "source_excerpt": item.source_excerpt, "source_page": item.source_page, "status": item.status} for item in persisted], "extraction_note": "Only explicit text matches are returned; each item requires team review before use."}
    finally:
        db.close()

@app.get("/api/bid-pipeline/{tender_id}/document-requirements")
def list_document_requirement_reviews(tender_id: str, current_user: Dict[str, Any] = Depends(require_roles([ROLE_ANALYST, ROLE_EXECUTIVE, ROLE_AUDITOR, ROLE_ADMIN]))):
    db=SessionLocal()
    try:
        rows=db.query(DocumentRequirementReviewModel).filter(DocumentRequirementReviewModel.tender_id==tender_id).order_by(DocumentRequirementReviewModel.id.desc()).all()
        return {"status":"SUCCESS","requirements":[{"id":r.id,"key":r.requirement_key,"source_excerpt":r.source_excerpt,"source_page":r.source_page,"status":r.status,"reviewed_by":r.reviewed_by,"reviewed_at":r.reviewed_at.isoformat() if r.reviewed_at else None} for r in rows]}
    finally: db.close()

@app.patch("/api/document-requirements/{requirement_id}/review")
def review_document_requirement(requirement_id:int, request:DocumentRequirementReviewRequest, current_user:Dict[str,Any]=Depends(require_roles([ROLE_EXECUTIVE,ROLE_ADMIN]))):
    if request.status not in {"approved","rejected"}: raise HTTPException(status_code=400,detail="status must be approved or rejected")
    db=SessionLocal()
    try:
        row=db.get(DocumentRequirementReviewModel,requirement_id)
        if not row: raise HTTPException(status_code=404,detail="Requirement not found")
        row.status,row.reviewed_by,row.reviewed_at=request.status,current_user.get("email",""),datetime.utcnow();db.commit()
        return {"status":"SUCCESS","requirement_id":row.id,"review_status":row.status}
    finally: db.close()


@app.post("/api/bid-pipeline/{tender_id}/document-requirements/create-task")
def create_task_from_document_requirement(tender_id: str, request: DocumentRequirementTaskRequest, current_user: Dict[str, Any] = Depends(require_roles([ROLE_ANALYST, ROLE_EXECUTIVE, ROLE_ADMIN]))):
    """Turn a human-reviewed, explicitly extracted clause into a traceable preparation task."""
    if not request.title.strip() or not request.source_excerpt.strip():
        raise HTTPException(status_code=400, detail="title and source_excerpt are required")
    if len(request.title) > 512 or len(request.source_excerpt) > 300:
        raise HTTPException(status_code=400, detail="Requirement text exceeds the allowed length")
    db = SessionLocal()
    try:
        if not db.query(BidPipelineItemModel.id).filter(BidPipelineItemModel.tender_id == tender_id).first():
            raise HTTPException(status_code=404, detail="Pipeline tender not found")
        review = db.query(DocumentRequirementReviewModel).filter(DocumentRequirementReviewModel.tender_id == tender_id, DocumentRequirementReviewModel.source_excerpt == request.source_excerpt.strip(), DocumentRequirementReviewModel.status == "approved").first()
        if not review:
            raise HTTPException(status_code=409, detail="Approve the matching document requirement before creating a required task")
        task = BidPreparationTaskModel(tender_id=tender_id, title=request.title.strip(), owner_email=request.owner_email, due_date=request.due_date, is_required=True, status="open", blocker=f"Document source: {request.source_excerpt.strip()}", created_by=current_user.get("email", ""))
        db.add(task); db.flush()
        _record_bid_activity(db, tender_id, "document_requirement", task.id, "requirement_task_created", "Created required preparation task from reviewed document clause", current_user.get("email", ""))
        db.commit(); db.refresh(task)
        return {"status": "SUCCESS", "task": _serialize_preparation_task(task), "source_trace": request.source_excerpt.strip()}
    finally:
        db.close()


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
                result.append(annotate_tender(item, transport="database"))
            total = crud.count_tenders(db, agency=agency)
            return {"count": len(result), "total_count": total, "source": "database", "provenance_summary": provenance_summary(result), "tenders": result}
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
                result = [annotate_tender(item, transport="json_cache") for item in data]
                return {"count": len(result), "total_count": len(result), "source": "json_cache", "provenance_summary": provenance_summary(result), "tenders": result}
        except Exception:
            pass
    return {"count": 0, "total_count": 0, "source": "empty", "tenders": []}


@app.get("/api/opportunities/ranked")
def get_ranked_opportunities(
    agency: Optional[str] = None,
    limit: int = 25,
    current_user: Dict[str, Any] = Depends(require_roles([ROLE_ANALYST, ROLE_EXECUTIVE, ROLE_AUDITOR, ROLE_ADMIN])),
):
    """Rank live notices for review using published tender signals only."""
    from sqlalchemy import func

    db = SessionLocal()
    try:
        tenders = crud.get_tenders(db, limit=min(max(limit, 1), 100), agency=agency)
        tender_ids = [t.tender_id for t in tenders]
        corrigenda_by_tender = {}
        if tender_ids:
            rows = db.query(CorrigendumModel.tender_id, func.count(CorrigendumModel.id)).filter(
                CorrigendumModel.tender_id.in_(tender_ids)
            ).group_by(CorrigendumModel.tender_id).all()
            corrigenda_by_tender = {tender_id: count for tender_id, count in rows}
        ranked = rank_tenders(tenders, corrigenda_by_tender)
        return {
            "status": "SUCCESS",
            "count": len(ranked),
            "ranking_basis": "published tender data only",
            "opportunities": ranked,
        }
    finally:
        db.close()


PIPELINE_STAGES = {"review", "go_no_go", "preparation", "submitted", "won", "lost"}
PIPELINE_DECISIONS = {"go", "no_go", "pending"}
PREPARATION_TASK_STATUSES = {"open", "in_progress", "blocked", "done"}


def _serialize_pipeline_item(item: BidPipelineItemModel) -> Dict[str, Any]:
    return {"id": item.id, "tender_id": item.tender_id, "tender_title": item.tender_title, "agency": item.agency,
            "owner_email": item.owner_email, "stage": item.stage, "internal_due_date": item.internal_due_date,
            "decision": item.decision, "next_action": item.next_action, "notes": item.notes, "created_by": item.created_by,
            "updated_at": item.updated_at.isoformat() if item.updated_at else None}


def _record_bid_activity(db, tender_id: str, entity_type: str, entity_id: Optional[int], action: str, summary: str, actor_email: str) -> None:
    db.add(BidActivityEventModel(tender_id=tender_id, entity_type=entity_type, entity_id=entity_id,
                                 action=action, summary=summary[:1000], actor_email=actor_email))


def _serialize_bid_activity(event: BidActivityEventModel) -> Dict[str, Any]:
    return {"id": event.id, "tender_id": event.tender_id, "entity_type": event.entity_type,
            "entity_id": event.entity_id, "action": event.action, "summary": event.summary,
            "actor_email": event.actor_email,
            "created_at": event.created_at.isoformat() if event.created_at else None}


@app.get("/api/bid-pipeline")
def list_bid_pipeline(current_user: Dict[str, Any] = Depends(require_roles([ROLE_ANALYST, ROLE_EXECUTIVE, ROLE_AUDITOR, ROLE_ADMIN]))):
    db = SessionLocal()
    try:
        items = db.query(BidPipelineItemModel).order_by(BidPipelineItemModel.updated_at.desc()).all()
        return {"status": "SUCCESS", "count": len(items), "items": [_serialize_pipeline_item(item) for item in items]}
    finally:
        db.close()


@app.get("/api/bid-pipeline/activity")
def list_bid_activity(tender_id: Optional[str] = None, limit: int = 50, current_user: Dict[str, Any] = Depends(require_roles([ROLE_ANALYST, ROLE_EXECUTIVE, ROLE_AUDITOR, ROLE_ADMIN]))):
    db = SessionLocal()
    try:
        query = db.query(BidActivityEventModel)
        if tender_id:
            query = query.filter(BidActivityEventModel.tender_id == tender_id)
        events = query.order_by(BidActivityEventModel.created_at.desc()).limit(min(max(limit, 1), 200)).all()
        return {"status": "SUCCESS", "count": len(events), "events": [_serialize_bid_activity(event) for event in events]}
    finally:
        db.close()


@app.post("/api/bid-pipeline")
def save_bid_pipeline_item(request: BidPipelineItemRequest, current_user: Dict[str, Any] = Depends(require_roles([ROLE_ANALYST, ROLE_EXECUTIVE, ROLE_ADMIN]))):
    if not request.tender_id.strip() or not request.tender_title.strip():
        raise HTTPException(status_code=400, detail="tender_id and tender_title are required")
    if request.stage not in PIPELINE_STAGES:
        raise HTTPException(status_code=400, detail="invalid pipeline stage")
    if request.decision and request.decision not in PIPELINE_DECISIONS:
        raise HTTPException(status_code=400, detail="invalid go/no-go decision")
    if (request.notes and len(request.notes) > 4000) or (request.next_action and len(request.next_action) > 1000):
        raise HTTPException(status_code=400, detail="notes must be 4000 characters or fewer")
    db = SessionLocal()
    try:
        item = db.query(BidPipelineItemModel).filter(BidPipelineItemModel.tender_id == request.tender_id.strip()).first()
        if request.stage == "submitted":
            readiness = _full_submission_readiness(db, request.tender_id.strip(), item)
            if not readiness["ready"]:
                raise HTTPException(status_code=409, detail={"message": "Submission gate is not satisfied", "readiness": readiness})
        actor_email = current_user.get("email", "")
        if not item:
            item = BidPipelineItemModel(tender_id=request.tender_id.strip(), tender_title=request.tender_title.strip(), created_by=actor_email)
            db.add(item)
            activity_summary = "Added tender to the shared bid pipeline"
            activity_action = "pipeline_created"
        else:
            proposed = {"owner_email": request.owner_email, "stage": request.stage, "internal_due_date": request.internal_due_date,
                        "decision": request.decision, "next_action": request.next_action, "notes": request.notes}
            labels = {"owner_email": "Owner", "stage": "Stage", "internal_due_date": "Internal due date", "decision": "Go/No-Go decision", "next_action": "Next action", "notes": "Notes"}
            changed = [labels[key] for key, value in proposed.items() if getattr(item, key) != value]
            activity_summary = f"Updated {', '.join(changed)}" if changed else "Reviewed pipeline item"
            activity_action = "pipeline_updated"
        item.tender_title, item.agency, item.owner_email = request.tender_title.strip(), request.agency, request.owner_email
        item.stage, item.internal_due_date, item.decision, item.next_action, item.notes = request.stage, request.internal_due_date, request.decision, request.next_action, request.notes
        db.flush()
        _record_bid_activity(db, item.tender_id, "pipeline", item.id, activity_action, activity_summary, actor_email)
        db.commit(); db.refresh(item)
        return {"status": "SUCCESS", "item": _serialize_pipeline_item(item)}
    finally:
        db.close()


def _serialize_preparation_task(task: BidPreparationTaskModel) -> Dict[str, Any]:
    return {"id": task.id, "tender_id": task.tender_id, "title": task.title, "owner_email": task.owner_email,
            "due_date": task.due_date, "is_required": task.is_required, "status": task.status, "blocker": task.blocker, "created_by": task.created_by,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "updated_at": task.updated_at.isoformat() if task.updated_at else None}


def _serialize_task_attachment(attachment: BidTaskAttachmentModel) -> Dict[str, Any]:
    return {"id": attachment.id, "task_id": attachment.task_id, "original_name": attachment.original_name,
            "content_type": attachment.content_type, "size_bytes": attachment.size_bytes,
            "sha256": attachment.sha256, "uploaded_by": attachment.uploaded_by,
            "created_at": attachment.created_at.isoformat() if attachment.created_at else None}


def _submission_readiness(db, tender_id: str, pipeline: Optional[BidPipelineItemModel] = None) -> Dict[str, Any]:
    pipeline = pipeline or db.query(BidPipelineItemModel).filter(BidPipelineItemModel.tender_id == tender_id).first()
    tasks = db.query(BidPreparationTaskModel).filter(BidPreparationTaskModel.tender_id == tender_id).all()
    required_tasks = [task for task in tasks if task.is_required]
    required_ids = [task.id for task in required_tasks]
    attachment_task_ids = {row[0] for row in db.query(BidTaskAttachmentModel.task_id).filter(BidTaskAttachmentModel.task_id.in_(required_ids or [-1])).distinct().all()}
    incomplete_required = [task.title for task in required_tasks if task.status != "done"]
    missing_evidence = [task.title for task in required_tasks if task.id not in attachment_task_ids]
    blocked_tasks = [task.title for task in tasks if task.status == "blocked"]
    approved_requirements = db.query(DocumentRequirementReviewModel).filter(DocumentRequirementReviewModel.tender_id == tender_id, DocumentRequirementReviewModel.status == "approved").all()
    task_sources = {task.blocker or "" for task in tasks if task.status == "done"}
    unmet_requirements = [item.requirement_key for item in approved_requirements if f"Document source: {item.source_excerpt}" not in task_sources]
    checks = [
        {"key": "go_decision", "label": "Recorded Go decision", "passed": bool(pipeline and pipeline.decision == "go")},
        {"key": "required_tasks", "label": "At least one required task", "passed": bool(required_tasks)},
        {"key": "completed_required", "label": "Required tasks completed", "passed": not incomplete_required, "items": incomplete_required},
        {"key": "evidence_required", "label": "Evidence attached to every required task", "passed": not missing_evidence, "items": missing_evidence},
        {"key": "no_blockers", "label": "No blocked preparation tasks", "passed": not blocked_tasks, "items": blocked_tasks},
        {"key": "approved_document_requirements", "label": "Approved document requirements completed", "passed": not unmet_requirements, "items": unmet_requirements},
    ]
    return {"tender_id": tender_id, "ready": bool(pipeline) and all(check["passed"] for check in checks), "checks": checks,
            "required_task_count": len(required_tasks), "attachment_count": len(attachment_task_ids)}


def _submission_fingerprint(db, tender_id: str, pipeline: Optional[BidPipelineItemModel] = None) -> str:
    pipeline = pipeline or db.query(BidPipelineItemModel).filter(BidPipelineItemModel.tender_id == tender_id).first()
    tasks = db.query(BidPreparationTaskModel).filter(BidPreparationTaskModel.tender_id == tender_id).order_by(BidPreparationTaskModel.id).all()
    attachment_task_ids = {row[0] for row in db.query(BidTaskAttachmentModel.task_id).filter(BidTaskAttachmentModel.task_id.in_([task.id for task in tasks] or [-1])).distinct().all()}
    payload = {"decision": pipeline.decision if pipeline else None, "tasks": [
        {"id": task.id, "required": task.is_required, "status": task.status, "has_evidence": task.id in attachment_task_ids}
        for task in tasks
    ]}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _serialize_submission_approval(approval: Optional[BidSubmissionApprovalModel], valid: bool = False) -> Dict[str, Any]:
    if not approval:
        return {"status": "pending", "valid": False, "note": None, "signed_by": None, "signed_at": None}
    return {"status": approval.status, "valid": valid, "note": approval.note, "signed_by": approval.signed_by,
            "signed_at": approval.signed_at.isoformat() if approval.signed_at else None,
            "updated_at": approval.updated_at.isoformat() if approval.updated_at else None}


def _full_submission_readiness(db, tender_id: str, pipeline: Optional[BidPipelineItemModel] = None) -> Dict[str, Any]:
    readiness = _submission_readiness(db, tender_id, pipeline)
    approval = db.query(BidSubmissionApprovalModel).filter(BidSubmissionApprovalModel.tender_id == tender_id).first()
    fingerprint = _submission_fingerprint(db, tender_id, pipeline)
    approval_valid = bool(approval and approval.status == "approved" and approval.readiness_fingerprint == fingerprint)
    readiness["checks"].append({"key": "executive_approval", "label": "Current Executive or Admin approval", "passed": approval_valid})
    readiness["ready"] = readiness["ready"] and approval_valid
    readiness["approval"] = _serialize_submission_approval(approval, approval_valid)
    return readiness


@app.get("/api/bid-pipeline/{tender_id}/submission-readiness")
def get_submission_readiness(tender_id: str, current_user: Dict[str, Any] = Depends(require_roles([ROLE_ANALYST, ROLE_EXECUTIVE, ROLE_AUDITOR, ROLE_ADMIN]))):
    db = SessionLocal()
    try:
        pipeline = db.query(BidPipelineItemModel).filter(BidPipelineItemModel.tender_id == tender_id).first()
        if not pipeline:
            raise HTTPException(status_code=404, detail="Pipeline tender not found")
        return {"status": "SUCCESS", "readiness": _full_submission_readiness(db, tender_id, pipeline)}
    finally:
        db.close()


@app.get("/api/bid-pipeline/{tender_id}/submission-approval")
def get_submission_approval(tender_id: str, current_user: Dict[str, Any] = Depends(require_roles([ROLE_ANALYST, ROLE_EXECUTIVE, ROLE_AUDITOR, ROLE_ADMIN]))):
    db = SessionLocal()
    try:
        pipeline = db.query(BidPipelineItemModel).filter(BidPipelineItemModel.tender_id == tender_id).first()
        if not pipeline:
            raise HTTPException(status_code=404, detail="Pipeline tender not found")
        readiness = _full_submission_readiness(db, tender_id, pipeline)
        return {"status": "SUCCESS", "approval": readiness["approval"], "base_ready": all(check["passed"] for check in readiness["checks"] if check["key"] != "executive_approval"),
                "can_sign": current_user.get("role") in {ROLE_EXECUTIVE, ROLE_ADMIN}}
    finally:
        db.close()


@app.put("/api/bid-pipeline/{tender_id}/submission-approval")
def save_submission_approval(tender_id: str, request: BidSubmissionApprovalRequest, current_user: Dict[str, Any] = Depends(require_roles([ROLE_EXECUTIVE, ROLE_ADMIN]))):
    if request.status not in {"approved", "rejected"}:
        raise HTTPException(status_code=400, detail="approval status must be approved or rejected")
    if request.note and len(request.note) > 1000:
        raise HTTPException(status_code=400, detail="approval note must be 1000 characters or fewer")
    db = SessionLocal()
    try:
        pipeline = db.query(BidPipelineItemModel).filter(BidPipelineItemModel.tender_id == tender_id).first()
        if not pipeline:
            raise HTTPException(status_code=404, detail="Pipeline tender not found")
        base_readiness = _submission_readiness(db, tender_id, pipeline)
        if request.status == "approved" and not base_readiness["ready"]:
            raise HTTPException(status_code=409, detail="Resolve all submission readiness checks before approving")
        approval = db.query(BidSubmissionApprovalModel).filter(BidSubmissionApprovalModel.tender_id == tender_id).first()
        if not approval:
            approval = BidSubmissionApprovalModel(tender_id=tender_id)
            db.add(approval)
        approval.status, approval.note, approval.signed_by, approval.signed_at = request.status, request.note.strip() if request.note else None, current_user.get("email", ""), datetime.utcnow()
        approval.readiness_fingerprint = _submission_fingerprint(db, tender_id, pipeline) if request.status == "approved" else None
        db.flush()
        _record_bid_activity(db, tender_id, "submission_approval", approval.id, f"submission_{request.status}", f"Submission {request.status} by authorized sign-off", current_user.get("email", ""))
        db.commit(); db.refresh(approval)
        return {"status": "SUCCESS", "approval": _serialize_submission_approval(approval, request.status == "approved")}
    finally:
        db.close()


OUTCOME_STATUSES = {"submitted", "won", "lost"}


def _serialize_bid_outcome(outcome: Optional[BidOutcomeModel]) -> Dict[str, Any]:
    if not outcome:
        return {"status": "not_recorded"}
    return {"status": outcome.status, "submission_reference": outcome.submission_reference,
            "submitted_at": outcome.submitted_at, "outcome_date": outcome.outcome_date,
            "awarded_contract_value": outcome.awarded_contract_value, "lessons_learned": outcome.lessons_learned,
            "recorded_by": outcome.recorded_by,
            "updated_at": outcome.updated_at.isoformat() if outcome.updated_at else None}


@app.get("/api/bid-pipeline/{tender_id}/outcome")
def get_bid_outcome(tender_id: str, current_user: Dict[str, Any] = Depends(require_roles([ROLE_ANALYST, ROLE_EXECUTIVE, ROLE_AUDITOR, ROLE_ADMIN]))):
    db = SessionLocal()
    try:
        if not db.query(BidPipelineItemModel.id).filter(BidPipelineItemModel.tender_id == tender_id).first():
            raise HTTPException(status_code=404, detail="Pipeline tender not found")
        outcome = db.query(BidOutcomeModel).filter(BidOutcomeModel.tender_id == tender_id).first()
        return {"status": "SUCCESS", "outcome": _serialize_bid_outcome(outcome), "can_record": current_user.get("role") in {ROLE_ANALYST, ROLE_EXECUTIVE, ROLE_ADMIN}}
    finally:
        db.close()


@app.put("/api/bid-pipeline/{tender_id}/outcome")
def save_bid_outcome(tender_id: str, request: BidOutcomeRequest, current_user: Dict[str, Any] = Depends(require_roles([ROLE_ANALYST, ROLE_EXECUTIVE, ROLE_ADMIN]))):
    if request.status not in OUTCOME_STATUSES:
        raise HTTPException(status_code=400, detail="outcome status must be submitted, won, or lost")
    if (request.submission_reference and len(request.submission_reference) > 256) or (request.lessons_learned and len(request.lessons_learned) > 4000):
        raise HTTPException(status_code=400, detail="Outcome text exceeds the allowed length")
    if request.awarded_contract_value is not None and request.awarded_contract_value < 0:
        raise HTTPException(status_code=400, detail="Awarded contract value cannot be negative")
    db = SessionLocal()
    try:
        pipeline = db.query(BidPipelineItemModel).filter(BidPipelineItemModel.tender_id == tender_id).first()
        if not pipeline:
            raise HTTPException(status_code=404, detail="Pipeline tender not found")
        existing = db.query(BidOutcomeModel).filter(BidOutcomeModel.tender_id == tender_id).first()
        reference = request.submission_reference.strip() if request.submission_reference else (existing.submission_reference if existing else None)
        if request.status == "submitted":
            if not reference:
                raise HTTPException(status_code=400, detail="Submission reference is required when recording a submission")
            if not _full_submission_readiness(db, tender_id, pipeline)["ready"]:
                raise HTTPException(status_code=409, detail="Current readiness and approval are required before recording submission")
        if request.status in {"won", "lost"} and not reference:
            raise HTTPException(status_code=400, detail="Record a submission reference before recording an outcome")
        if request.status == "won" and not request.awarded_contract_value and not (existing and existing.awarded_contract_value):
            raise HTTPException(status_code=400, detail="Awarded contract value is required for a win")
        outcome = existing or BidOutcomeModel(tender_id=tender_id, recorded_by=current_user.get("email", ""))
        if not existing:
            db.add(outcome)
        outcome.status, outcome.submission_reference = request.status, reference
        outcome.submitted_at = request.submitted_at or (existing.submitted_at if existing else None)
        outcome.outcome_date = request.outcome_date or (existing.outcome_date if existing else None)
        outcome.awarded_contract_value = request.awarded_contract_value if request.awarded_contract_value is not None else (existing.awarded_contract_value if existing else None)
        outcome.lessons_learned = request.lessons_learned.strip() if request.lessons_learned else None
        outcome.recorded_by = current_user.get("email", "")
        pipeline.stage = request.status
        db.flush()
        _record_bid_activity(db, tender_id, "bid_outcome", outcome.id, f"outcome_{request.status}", f"Recorded bid outcome: {request.status}", current_user.get("email", ""))
        db.commit(); db.refresh(outcome)
        return {"status": "SUCCESS", "outcome": _serialize_bid_outcome(outcome)}
    finally:
        db.close()


def _build_bid_outcome_learning_dashboard(db) -> Dict[str, Any]:
    """Summarize deliberately recorded outcomes; never infer missing award results."""
    rows = db.query(BidOutcomeModel, BidPipelineItemModel).outerjoin(
        BidPipelineItemModel, BidPipelineItemModel.tender_id == BidOutcomeModel.tender_id
    ).order_by(BidOutcomeModel.updated_at.desc()).all()
    outcomes: List[Dict[str, Any]] = []
    agencies: Dict[str, Dict[str, Any]] = {}
    total_awarded_value = 0.0
    won = lost = submitted = 0
    for outcome, pipeline in rows:
        agency = (pipeline.agency if pipeline and pipeline.agency else "Unspecified agency").strip()
        tender_title = pipeline.tender_title if pipeline and pipeline.tender_title else outcome.tender_id
        value = float(outcome.awarded_contract_value) if outcome.awarded_contract_value is not None else None
        record = {"tender_id": outcome.tender_id, "tender_title": tender_title, "agency": agency, **_serialize_bid_outcome(outcome)}
        outcomes.append(record)
        summary = agencies.setdefault(agency, {"agency": agency, "recorded_outcomes": 0, "submitted": 0, "won": 0, "lost": 0, "awarded_contract_value": 0.0})
        summary["recorded_outcomes"] += 1
        summary[outcome.status] += 1
        if outcome.status == "won" and value is not None:
            summary["awarded_contract_value"] += value
            total_awarded_value += value
        if outcome.status == "won":
            won += 1
        elif outcome.status == "lost":
            lost += 1
        else:
            submitted += 1
    decisioned = won + lost
    agency_summaries = []
    for summary in agencies.values():
        agency_decisioned = summary["won"] + summary["lost"]
        summary["decisioned"] = agency_decisioned
        summary["win_rate_pct"] = round(summary["won"] / agency_decisioned * 100, 1) if agency_decisioned else None
        summary["awarded_contract_value"] = round(summary["awarded_contract_value"], 2)
        agency_summaries.append(summary)
    agency_summaries.sort(key=lambda item: (-item["decisioned"], item["agency"].lower()))
    lessons = [record for record in outcomes if record.get("lessons_learned")]
    return {"status": "SUCCESS", "source": "Recorded bid outcomes", "totals": {
        "recorded_outcomes": len(outcomes), "submitted": submitted, "won": won, "lost": lost,
        "decisioned": decisioned, "win_rate_pct": round(won / decisioned * 100, 1) if decisioned else None,
        "awarded_contract_value": round(total_awarded_value, 2),
    }, "by_agency": agency_summaries, "lessons": lessons, "outcomes": outcomes}


@app.get("/api/bid-outcomes/learning-dashboard")
def get_bid_outcome_learning_dashboard(current_user: Dict[str, Any] = Depends(require_roles([ROLE_ANALYST, ROLE_EXECUTIVE, ROLE_AUDITOR, ROLE_ADMIN]))):
    db = SessionLocal()
    try:
        return _build_bid_outcome_learning_dashboard(db)
    finally:
        db.close()


@app.get("/api/bid-outcomes/learning-report.csv")
def download_bid_outcome_learning_report(current_user: Dict[str, Any] = Depends(require_roles([ROLE_ANALYST, ROLE_EXECUTIVE, ROLE_AUDITOR, ROLE_ADMIN]))):
    """Export the inspected outcome records behind the learning dashboard as CSV."""
    db = SessionLocal()
    try:
        dashboard = _build_bid_outcome_learning_dashboard(db)
        output = StringIO(newline="")
        writer = csv.writer(output)
        writer.writerow(["TenderPulse win/loss report", "Source: recorded bid outcomes", "Win rate denominator: won + lost only"])
        writer.writerow(["Tender ID", "Tender title", "Agency", "Outcome status", "Submission reference", "Submitted at", "Outcome date", "Awarded contract value (BDT)", "Lessons learned", "Recorded by", "Updated at"])
        for outcome in dashboard["outcomes"]:
            writer.writerow([outcome.get("tender_id"), outcome.get("tender_title"), outcome.get("agency"), outcome.get("status"), outcome.get("submission_reference"), outcome.get("submitted_at"), outcome.get("outcome_date"), outcome.get("awarded_contract_value"), outcome.get("lessons_learned"), outcome.get("recorded_by"), outcome.get("updated_at")])
        filename = f"tenderpulse-win-loss-report-{datetime.utcnow():%Y%m%d}.csv"
        return StreamingResponse(iter([output.getvalue()]), media_type="text/csv; charset=utf-8", headers={"Content-Disposition": f'attachment; filename="{filename}"'})
    finally:
        db.close()


@app.get("/api/executive-kpis/daily-summary")
def get_daily_executive_summary(current_user: Dict[str, Any] = Depends(require_roles([ROLE_EXECUTIVE, ROLE_AUDITOR, ROLE_ADMIN]))):
    """Return the durable daily briefing generated by the background worker."""
    db = SessionLocal()
    try:
        summary = db.query(ExecutiveKpiSummaryModel).order_by(ExecutiveKpiSummaryModel.summary_date.desc()).first()
        return {"status": "SUCCESS", "summary": serialize_executive_summary(summary), "delivery": "in_app_daily", "can_generate": current_user.get("role") in {ROLE_EXECUTIVE, ROLE_ADMIN}}
    finally:
        db.close()


@app.post("/api/executive-kpis/daily-summary/generate")
def generate_daily_executive_summary(current_user: Dict[str, Any] = Depends(require_roles([ROLE_EXECUTIVE, ROLE_ADMIN]))):
    """Allow authorized leadership to regenerate today's stored briefing on demand."""
    db = SessionLocal()
    try:
        summary, _ = ensure_daily_executive_summary(db, generated_by=current_user.get("email", ""), force=True)
        db.commit(); db.refresh(summary)
        return {"status": "SUCCESS", "summary": serialize_executive_summary(summary), "delivery": "in_app_daily"}
    finally:
        db.close()


def _audit_retention_policy(db) -> AuditRetentionPolicyModel:
    policy = db.query(AuditRetentionPolicyModel).filter(AuditRetentionPolicyModel.id == 1).first()
    if not policy:
        policy = AuditRetentionPolicyModel(id=1, retention_days=2555)
        db.add(policy); db.flush()
    return policy


def _serialize_audit_retention_policy(policy: AuditRetentionPolicyModel) -> Dict[str, Any]:
    return {"retention_days": policy.retention_days, "automatic_purge": False, "updated_by": policy.updated_by,
            "updated_at": policy.updated_at.isoformat() if policy.updated_at else None}


@app.get("/api/governance/audit-report")
def get_bid_audit_report(current_user: Dict[str, Any] = Depends(require_roles([ROLE_EXECUTIVE, ROLE_AUDITOR, ROLE_ADMIN]))):
    db = SessionLocal()
    try:
        policy = _audit_retention_policy(db)
        events = db.query(BidActivityEventModel).order_by(BidActivityEventModel.created_at.desc()).limit(200).all()
        return {"status": "SUCCESS", "scope": "shared bid workflow activity", "retention_policy": _serialize_audit_retention_policy(policy),
                "event_count": len(events), "events": [_serialize_bid_activity(event) for event in events]}
    finally:
        db.close()


@app.put("/api/governance/audit-retention-policy")
def update_audit_retention_policy(request: AuditRetentionPolicyRequest, current_user: Dict[str, Any] = Depends(require_roles([ROLE_ADMIN]))):
    if not 365 <= request.retention_days <= 3650:
        raise HTTPException(status_code=400, detail="retention_days must be between 365 and 3650")
    db = SessionLocal()
    try:
        policy = _audit_retention_policy(db)
        policy.retention_days = request.retention_days
        policy.updated_by = current_user.get("email", "")
        db.commit(); db.refresh(policy)
        return {"status": "SUCCESS", "retention_policy": _serialize_audit_retention_policy(policy)}
    finally:
        db.close()


@app.get("/api/governance/audit-report.csv")
def download_bid_audit_report(current_user: Dict[str, Any] = Depends(require_roles([ROLE_EXECUTIVE, ROLE_AUDITOR, ROLE_ADMIN]))):
    db = SessionLocal()
    try:
        policy = _audit_retention_policy(db)
        events = db.query(BidActivityEventModel).order_by(BidActivityEventModel.created_at.desc()).limit(10000).all()
        output = StringIO(newline=""); writer = csv.writer(output)
        writer.writerow(["TenderPulse bid workflow audit report", f"Retention policy: {policy.retention_days} days", "Automatic purge: disabled"])
        writer.writerow(["Event ID", "Created at", "Tender ID", "Entity type", "Action", "Summary", "Actor email"])
        for event in events:
            writer.writerow([event.id, event.created_at.isoformat() if event.created_at else None, event.tender_id, event.entity_type, event.action, event.summary, event.actor_email])
        return StreamingResponse(iter([output.getvalue()]), media_type="text/csv; charset=utf-8", headers={"Content-Disposition": f'attachment; filename="tenderpulse-bid-audit-{datetime.utcnow():%Y%m%d}.csv"'})
    finally:
        db.close()


@app.get("/api/team-workload")
def get_team_workload(current_user: Dict[str, Any] = Depends(require_roles([ROLE_EXECUTIVE, ROLE_AUDITOR, ROLE_ADMIN]))):
    """Task ownership and delivery-risk view from the shared preparation checklist."""
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        tasks = db.query(BidPreparationTaskModel).all()
        members: Dict[str, Dict[str, Any]] = {}
        for task in tasks:
            owner = (task.owner_email or "Unassigned").strip() or "Unassigned"
            item = members.setdefault(owner, {"owner_email": owner, "total": 0, "open": 0, "in_progress": 0, "blocked": 0, "done": 0, "overdue": 0})
            item["total"] += 1
            item[task.status] = item.get(task.status, 0) + 1
            due = _as_datetime(task.due_date)
            if task.status != "done" and due and due < now:
                item["overdue"] += 1
        workload = sorted(members.values(), key=lambda item: (-(item["open"] + item["in_progress"] + item["blocked"]), item["owner_email"].lower()))
        return {"status": "SUCCESS", "source": "shared preparation tasks", "totals": {"tasks": len(tasks), "open": sum(item["open"] for item in workload), "in_progress": sum(item["in_progress"] for item in workload), "blocked": sum(item["blocked"] for item in workload), "overdue": sum(item["overdue"] for item in workload), "unassigned": next((item["total"] for item in workload if item["owner_email"] == "Unassigned"), 0)}, "members": workload}
    finally:
        db.close()


@app.get("/api/bid-pipeline/{tender_id}/submission-pack")
def download_submission_pack(tender_id: str, current_user: Dict[str, Any] = Depends(require_roles([ROLE_ANALYST, ROLE_EXECUTIVE, ROLE_AUDITOR, ROLE_ADMIN]))):
    """Create a private, integrity-checked archive for a currently approved submission."""
    db = SessionLocal()
    pack_path: Optional[str] = None
    try:
        pipeline = db.query(BidPipelineItemModel).filter(BidPipelineItemModel.tender_id == tender_id).first()
        if not pipeline:
            raise HTTPException(status_code=404, detail="Pipeline tender not found")
        readiness = _full_submission_readiness(db, tender_id, pipeline)
        if not readiness["ready"]:
            raise HTTPException(status_code=409, detail="A current submission approval is required before exporting the final pack")
        evidence_rows = db.query(BidTaskAttachmentModel, BidPreparationTaskModel).join(
            BidPreparationTaskModel, BidPreparationTaskModel.id == BidTaskAttachmentModel.task_id
        ).filter(BidPreparationTaskModel.tender_id == tender_id, BidPreparationTaskModel.is_required.is_(True)).order_by(BidTaskAttachmentModel.id).all()
        max_pack_bytes = min(settings.max_upload_bytes * 10, 250 * 1024 * 1024)
        if sum(attachment.size_bytes for attachment, _ in evidence_rows) > max_pack_bytes:
            raise HTTPException(status_code=413, detail="Approved evidence exceeds the final submission pack size limit")
        os.makedirs(EVIDENCE_DIR, mode=0o700, exist_ok=True)
        with tempfile.NamedTemporaryFile(prefix="submission-pack-", suffix=".zip", dir=EVIDENCE_DIR, delete=False) as pack_file:
            pack_path = pack_file.name
        _record_bid_activity(db, tender_id, "submission_pack", None, "submission_pack_exported", "Exported approved final submission pack", current_user.get("email", ""))
        db.flush()
        events = db.query(BidActivityEventModel).filter(BidActivityEventModel.tender_id == tender_id).order_by(BidActivityEventModel.created_at.asc()).all()
        evidence_index = []
        with zipfile.ZipFile(pack_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
            for attachment, task in evidence_rows:
                source_path = os.path.join(EVIDENCE_DIR, attachment.storage_key)
                if not os.path.isfile(source_path):
                    raise HTTPException(status_code=410, detail=f"Required evidence is unavailable: {attachment.original_name}")
                archive_name = f"evidence/{attachment.id}_{re.sub(r'[^A-Za-z0-9._-]', '_', attachment.original_name)}"
                digest = hashlib.sha256()
                with open(source_path, "rb") as source, archive.open(archive_name, "w") as destination:
                    while chunk := source.read(1024 * 1024):
                        digest.update(chunk)
                        destination.write(chunk)
                if digest.hexdigest() != attachment.sha256:
                    raise HTTPException(status_code=409, detail=f"Evidence integrity verification failed: {attachment.original_name}")
                evidence_index.append({"task_id": task.id, "task_title": task.title, "archive_path": archive_name,
                                       "original_name": attachment.original_name, "sha256": attachment.sha256,
                                       "size_bytes": attachment.size_bytes, "uploaded_by": attachment.uploaded_by})
            manifest = {"format": "TenderPulse approved submission pack v1", "generated_at": datetime.utcnow().isoformat() + "Z",
                        "generated_by": current_user.get("email", ""), "pipeline": _serialize_pipeline_item(pipeline),
                        "readiness": readiness, "approval": readiness["approval"], "evidence": evidence_index,
                        "integrity": "Each evidence file SHA-256 was verified during archive creation."}
            archive.writestr("submission-manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False))
            archive.writestr("activity-timeline.json", json.dumps([_serialize_bid_activity(event) for event in events], indent=2, ensure_ascii=False))
            archive.writestr("evidence-index.json", json.dumps(evidence_index, indent=2, ensure_ascii=False))
        db.commit()
        safe_tender_id = re.sub(r"[^A-Za-z0-9._-]", "_", tender_id)[:64] or "tender"
        return FileResponse(pack_path, media_type="application/zip", filename=f"{safe_tender_id}-submission-pack.zip",
                            headers={"Cache-Control": "private, no-store"}, background=BackgroundTask(os.remove, pack_path))
    except HTTPException:
        if pack_path and os.path.isfile(pack_path):
            os.remove(pack_path)
        raise
    except Exception:
        db.rollback()
        if pack_path and os.path.isfile(pack_path):
            os.remove(pack_path)
        raise HTTPException(status_code=500, detail="Unable to create final submission pack")
    finally:
        db.close()


@app.get("/api/bid-pipeline/{tender_id}/tasks")
def list_bid_preparation_tasks(tender_id: str, current_user: Dict[str, Any] = Depends(require_roles([ROLE_ANALYST, ROLE_EXECUTIVE, ROLE_AUDITOR, ROLE_ADMIN]))):
    db = SessionLocal()
    try:
        tasks = db.query(BidPreparationTaskModel).filter(BidPreparationTaskModel.tender_id == tender_id).order_by(BidPreparationTaskModel.created_at.asc()).all()
        task_ids = [task.id for task in tasks]
        attachments_by_task: Dict[int, List[Dict[str, Any]]] = {task_id: [] for task_id in task_ids}
        if task_ids:
            for attachment in db.query(BidTaskAttachmentModel).filter(BidTaskAttachmentModel.task_id.in_(task_ids)).order_by(BidTaskAttachmentModel.created_at.desc()).all():
                attachments_by_task[attachment.task_id].append(_serialize_task_attachment(attachment))
        items = []
        for task in tasks:
            item = _serialize_preparation_task(task)
            item["attachments"] = attachments_by_task[task.id]
            items.append(item)
        return {"status": "SUCCESS", "count": len(items), "items": items}
    finally:
        db.close()


@app.post("/api/bid-pipeline/{tender_id}/tasks")
def create_bid_preparation_task(tender_id: str, request: BidPreparationTaskRequest, current_user: Dict[str, Any] = Depends(require_roles([ROLE_ANALYST, ROLE_EXECUTIVE, ROLE_ADMIN]))):
    if not tender_id.strip() or not request.title.strip() or len(request.title.strip()) > 512:
        raise HTTPException(status_code=400, detail="Provide a task title of 512 characters or fewer")
    if request.status not in PREPARATION_TASK_STATUSES:
        raise HTTPException(status_code=400, detail="invalid preparation task status")
    if request.blocker and len(request.blocker) > 4000:
        raise HTTPException(status_code=400, detail="blocker must be 4000 characters or fewer")
    db = SessionLocal()
    try:
        task = BidPreparationTaskModel(tender_id=tender_id.strip(), title=request.title.strip(), owner_email=request.owner_email, due_date=request.due_date, is_required=request.is_required,
                                       status=request.status, blocker=request.blocker, created_by=current_user.get("email", ""))
        db.add(task); db.flush()
        _record_bid_activity(db, task.tender_id, "preparation_task", task.id, "task_created", f"Created preparation task: {task.title}", current_user.get("email", ""))
        db.commit(); db.refresh(task)
        return {"status": "SUCCESS", "item": _serialize_preparation_task(task)}
    finally:
        db.close()


@app.post("/api/bid-pipeline/tasks/{task_id}/attachments")
async def upload_bid_task_attachment(task_id: int, file: UploadFile = File(...), current_user: Dict[str, Any] = Depends(require_roles([ROLE_ANALYST, ROLE_EXECUTIVE, ROLE_ADMIN]))):
    """Store approved bid evidence privately, outside the static web root."""
    original_name = os.path.basename(file.filename or "")
    extension = os.path.splitext(original_name)[1].lower()
    if not original_name or extension not in EVIDENCE_FILE_TYPES:
        raise HTTPException(status_code=400, detail="Allowed evidence types: PDF, Word, Excel, PNG, and JPEG")
    safe_name = re.sub(r"[^A-Za-z0-9._ -]", "_", original_name).strip(" .")[:255]
    if not safe_name:
        raise HTTPException(status_code=400, detail="Invalid evidence filename")
    content = await file.read(settings.max_upload_bytes + 1)
    if not content:
        raise HTTPException(status_code=400, detail="Evidence file is empty")
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail="Evidence file exceeds the configured size limit")
    storage_key = f"{uuid.uuid4().hex}{extension}"
    final_path = os.path.join(EVIDENCE_DIR, storage_key)
    temp_path = f"{final_path}.uploading"
    db = SessionLocal()
    try:
        task = db.get(BidPreparationTaskModel, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Preparation task not found")
        os.makedirs(EVIDENCE_DIR, mode=0o700, exist_ok=True)
        with open(temp_path, "xb") as stored_file:
            stored_file.write(content)
        os.replace(temp_path, final_path)
        attachment = BidTaskAttachmentModel(task_id=task.id, original_name=safe_name, storage_key=storage_key,
                                            content_type=EVIDENCE_FILE_TYPES[extension], size_bytes=len(content),
                                            sha256=hashlib.sha256(content).hexdigest(), uploaded_by=current_user.get("email", ""))
        db.add(attachment); db.flush()
        _record_bid_activity(db, task.tender_id, "attachment", attachment.id, "evidence_uploaded", f"Uploaded evidence: {safe_name}", current_user.get("email", ""))
        db.commit(); db.refresh(attachment)
        return {"status": "SUCCESS", "attachment": _serialize_task_attachment(attachment)}
    except HTTPException:
        raise
    except Exception:
        db.rollback()
        if os.path.isfile(final_path):
            os.remove(final_path)
        if os.path.isfile(temp_path):
            os.remove(temp_path)
        raise HTTPException(status_code=500, detail="Unable to store evidence attachment")
    finally:
        db.close()
        await file.close()


@app.get("/api/bid-pipeline/task-attachments/{attachment_id}/download")
def download_bid_task_attachment(attachment_id: int, current_user: Dict[str, Any] = Depends(require_roles([ROLE_ANALYST, ROLE_EXECUTIVE, ROLE_AUDITOR, ROLE_ADMIN]))):
    """Download a private evidence file after authentication and authorization."""
    db = SessionLocal()
    try:
        attachment = db.get(BidTaskAttachmentModel, attachment_id)
        if not attachment:
            raise HTTPException(status_code=404, detail="Evidence attachment not found")
        file_path = os.path.join(EVIDENCE_DIR, attachment.storage_key)
        if not os.path.isfile(file_path):
            raise HTTPException(status_code=410, detail="Evidence attachment is no longer available")
        return FileResponse(file_path, media_type=attachment.content_type, filename=attachment.original_name,
                            headers={"Cache-Control": "private, no-store"})
    finally:
        db.close()


@app.patch("/api/bid-pipeline/tasks/{task_id}")
def update_bid_preparation_task(task_id: int, request: BidPreparationTaskUpdateRequest, current_user: Dict[str, Any] = Depends(require_roles([ROLE_ANALYST, ROLE_EXECUTIVE, ROLE_ADMIN]))):
    if request.status is not None and request.status not in PREPARATION_TASK_STATUSES:
        raise HTTPException(status_code=400, detail="invalid preparation task status")
    if request.title is not None and (not request.title.strip() or len(request.title.strip()) > 512):
        raise HTTPException(status_code=400, detail="Provide a task title of 512 characters or fewer")
    if request.blocker is not None and len(request.blocker) > 4000:
        raise HTTPException(status_code=400, detail="blocker must be 4000 characters or fewer")
    db = SessionLocal()
    try:
        task = db.get(BidPreparationTaskModel, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Preparation task not found")
        proposed = {"title": request.title.strip() if request.title is not None else task.title,
                    "owner_email": request.owner_email.strip() or None if request.owner_email is not None else task.owner_email,
                    "due_date": request.due_date.strip() or None if request.due_date is not None else task.due_date,
                    "is_required": request.is_required if request.is_required is not None else task.is_required,
                    "status": request.status if request.status is not None else task.status,
                    "blocker": request.blocker.strip() or None if request.blocker is not None else task.blocker}
        labels = {"title": "Task title", "owner_email": "Owner", "due_date": "Due date", "is_required": "Submission requirement", "status": "Status", "blocker": "Blocker"}
        changed = [labels[key] for key, value in proposed.items() if getattr(task, key) != value]
        if request.title is not None: task.title = request.title.strip()
        if request.owner_email is not None: task.owner_email = request.owner_email.strip() or None
        if request.due_date is not None: task.due_date = request.due_date.strip() or None
        if request.is_required is not None: task.is_required = request.is_required
        if request.status is not None: task.status = request.status
        if request.blocker is not None: task.blocker = request.blocker.strip() or None
        if changed:
            _record_bid_activity(db, task.tender_id, "preparation_task", task.id, "task_updated", f"Updated {', '.join(changed)} for task: {task.title}", current_user.get("email", ""))
        db.commit(); db.refresh(task)
        return {"status": "SUCCESS", "item": _serialize_preparation_task(task)}
    finally:
        db.close()


def _preparation_task_due_is_overdue(due_date: Optional[str]) -> bool:
    if not due_date:
        return False
    try:
        return datetime.fromisoformat(due_date.replace("Z", "+00:00")).replace(tzinfo=None) < datetime.utcnow()
    except ValueError:
        return False


@app.get("/api/bid-pipeline/task-reminders")
def list_bid_preparation_task_reminders(current_user: Dict[str, Any] = Depends(require_roles([ROLE_ANALYST, ROLE_EXECUTIVE, ROLE_AUDITOR, ROLE_ADMIN]))):
    """Generate current in-app reminders for active shared preparation tasks."""
    db = SessionLocal()
    try:
        rows = db.query(BidPreparationTaskModel, BidPipelineItemModel).outerjoin(
            BidPipelineItemModel, BidPipelineItemModel.tender_id == BidPreparationTaskModel.tender_id
        ).filter(BidPreparationTaskModel.status != "done").order_by(BidPreparationTaskModel.updated_at.desc()).all()
        reminders = []
        for task, pipeline in rows:
            reasons = []
            if task.status == "blocked": reasons.append("Blocked")
            if not task.owner_email: reasons.append("Unassigned")
            if _preparation_task_due_is_overdue(task.due_date): reasons.append("Overdue")
            if not reasons:
                continue
            reminders.append({"id": task.id, "kind": "preparation_task", "tender_id": task.tender_id,
                              "tender_title": pipeline.tender_title if pipeline else task.tender_id,
                              "agency": pipeline.agency if pipeline else None, "task_title": task.title,
                              "owner_email": task.owner_email, "due_date": task.due_date, "status": task.status,
                              "reasons": reasons, "severity": "HIGH" if "Blocked" in reasons or "Overdue" in reasons else "MEDIUM",
                              "updated_at": task.updated_at.isoformat() if task.updated_at else None})
        return {"status": "SUCCESS", "count": len(reminders), "reminders": reminders}
    finally:
        db.close()


def _readiness_profile_payload(profile: BidReadinessProfileModel) -> Dict[str, Any]:
    return {"contractor_name": profile.contractor_name, "peak_turnover_bdt": profile.peak_turnover_bdt,
            "active_commitments_bdt": profile.active_commitments_bdt, "available_credit_bdt": profile.available_credit_bdt,
            "past_similar_max_bdt": profile.past_similar_max_bdt, "engineers_count": profile.engineers_count,
            "updated_by": profile.updated_by, "updated_at": profile.updated_at.isoformat() if profile.updated_at else None}


@app.get("/api/bid-readiness/profile")
def get_bid_readiness_profile(current_user: Dict[str, Any] = Depends(require_roles([ROLE_ANALYST, ROLE_EXECUTIVE, ROLE_AUDITOR, ROLE_ADMIN]))):
    db = SessionLocal()
    try:
        profile = db.get(BidReadinessProfileModel, 1)
        if not profile:
            profile = BidReadinessProfileModel(id=1)
            db.add(profile); db.commit(); db.refresh(profile)
        return {"status": "SUCCESS", "profile": _readiness_profile_payload(profile)}
    finally: db.close()


@app.put("/api/bid-readiness/profile")
def save_bid_readiness_profile(request: BidReadinessProfileRequest, current_user: Dict[str, Any] = Depends(require_roles([ROLE_EXECUTIVE, ROLE_ADMIN]))):
    numeric_values = [request.peak_turnover_bdt, request.active_commitments_bdt, request.available_credit_bdt, request.past_similar_max_bdt]
    if not request.contractor_name.strip() or any(value < 0 for value in numeric_values) or request.engineers_count < 0:
        raise HTTPException(status_code=400, detail="Provide a company name and non-negative capacity values")
    db = SessionLocal()
    try:
        profile = db.get(BidReadinessProfileModel, 1) or BidReadinessProfileModel(id=1)
        if not db.get(BidReadinessProfileModel, 1): db.add(profile)
        profile.contractor_name, profile.peak_turnover_bdt, profile.active_commitments_bdt = request.contractor_name.strip(), request.peak_turnover_bdt, request.active_commitments_bdt
        profile.available_credit_bdt, profile.past_similar_max_bdt, profile.engineers_count = request.available_credit_bdt, request.past_similar_max_bdt, request.engineers_count
        profile.updated_by = current_user.get("email", "")
        db.commit(); db.refresh(profile)
        return {"status": "SUCCESS", "profile": _readiness_profile_payload(profile)}
    finally: db.close()


@app.post("/api/opportunities/{tender_id}/go-no-go")
def assess_tender_go_no_go(tender_id: str, current_user: Dict[str, Any] = Depends(require_roles([ROLE_ANALYST, ROLE_EXECUTIVE, ROLE_ADMIN]))):
    """Evaluate a live tender against the shared company readiness profile."""
    db = SessionLocal()
    try:
        tender = db.query(TenderModel).filter(TenderModel.tender_id == tender_id).first()
        if not tender:
            raise HTTPException(status_code=404, detail="Tender not found")
        profile = db.get(BidReadinessProfileModel, 1)
        if not profile or profile.peak_turnover_bdt <= 0:
            raise HTTPException(status_code=409, detail="Complete the shared bid readiness profile before running Go/No-Go.")
        request = DecisionEvaluationRequest(
            tender_id=tender.tender_id, tender_title=tender.title, agency=tender.agency,
            estimated_cost_bdt=tender.estimated_cost or 0, contractor_name=profile.contractor_name,
            peak_turnover_bdt=profile.peak_turnover_bdt, active_commitments_bdt=profile.active_commitments_bdt,
            available_credit_bdt=profile.available_credit_bdt, past_similar_max_bdt=profile.past_similar_max_bdt,
            engineers_count=profile.engineers_count,
        )
        result = decision_engine.evaluate_bid(request)
        result["profile_updated_at"] = profile.updated_at.isoformat() if profile.updated_at else None
        result["assessment_basis"] = "shared bid readiness profile and published tender data"
        return result
    finally:
        db.close()


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
    status_file = os.path.join(ROOT_DIR, "data", "harvester_status.json")
    if os.path.exists(status_file):
        try:
            with open(status_file, "r", encoding="utf-8") as f:
                file_state = json.load(f)
                return {"status": "SUCCESS", "telemetry": file_state}
        except Exception:
            pass
    # Development fallback only. In production the independent worker owns the
    # status file and must never be instantiated by this API read path.
    return {"status": "SUCCESS", "telemetry": get_daemon_instance().get_status()}


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
    if settings.is_production:
        raise HTTPException(
            status_code=409,
            detail="Manual harvest triggers are disabled while the independent production worker is active.",
        )
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


def _corrigendum_severity(field_changed: str) -> str:
    """Map known amendment classes to operator-review priority."""
    return "HIGH" if field_changed == "closing_date" else "MEDIUM"


@app.get("/api/corrigenda/review-queue")
def corrigendum_review_queue(
    status: str = "open",
    agency: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = 100,
    current_user: Dict[str, Any] = Depends(require_roles([ROLE_ANALYST, ROLE_EXECUTIVE, ROLE_AUDITOR, ROLE_ADMIN])),
):
    """Return the signed-in operator's actionable corrigendum queue."""
    normalized_status = status.lower()
    if normalized_status not in {"open", "acknowledged", "reviewed", "all"}:
        raise HTTPException(status_code=400, detail="status must be open, acknowledged, reviewed, or all")
    normalized_severity = severity.upper() if severity else None
    if normalized_severity and normalized_severity not in {"HIGH", "MEDIUM"}:
        raise HTTPException(status_code=400, detail="severity must be HIGH or MEDIUM")

    db = SessionLocal()
    try:
        reviewer_email = current_user.get("email", "").lower()
        query = db.query(CorrigendumModel, TenderModel, CorrigendumReviewModel).join(
            TenderModel, TenderModel.tender_id == CorrigendumModel.tender_id
        ).outerjoin(
            CorrigendumReviewModel,
            (CorrigendumReviewModel.corrigendum_id == CorrigendumModel.id)
            & (CorrigendumReviewModel.reviewer_email == reviewer_email),
        )
        if agency:
            query = query.filter(TenderModel.agency.ilike(f"%{agency}%"))

        results = []
        for corrigendum, tender, review in query.order_by(CorrigendumModel.detected_at.desc()).limit(min(max(limit, 1), 200)).all():
            item_status = review.status if review else "open"
            item_severity = _corrigendum_severity(corrigendum.field_changed)
            if normalized_status != "all" and item_status != normalized_status:
                continue
            if normalized_severity and item_severity != normalized_severity:
                continue
            results.append({
                "id": corrigendum.id,
                "tender_id": corrigendum.tender_id,
                "tender_title": tender.title,
                "agency": tender.agency,
                "field_changed": corrigendum.field_changed,
                "old_value": corrigendum.old_value,
                "new_value": corrigendum.new_value,
                "reason": corrigendum.reason,
                "detected_at": corrigendum.detected_at.isoformat() if corrigendum.detected_at else None,
                "severity": item_severity,
                "review_status": item_status,
                "review_note": review.note if review else None,
                "reviewed_at": review.updated_at.isoformat() if review else None,
            })
        return {"status": "SUCCESS", "count": len(results), "alerts": results}
    finally:
        db.close()


@app.post("/api/corrigenda/{corrigendum_id}/review")
def review_corrigendum(
    corrigendum_id: int,
    request: CorrigendumReviewRequest,
    current_user: Dict[str, Any] = Depends(require_roles([ROLE_ANALYST, ROLE_EXECUTIVE, ROLE_AUDITOR, ROLE_ADMIN])),
):
    """Acknowledge or complete review of a corrigendum for the current user."""
    normalized_status = request.status.lower()
    if normalized_status not in {"acknowledged", "reviewed"}:
        raise HTTPException(status_code=400, detail="status must be acknowledged or reviewed")
    if request.note and len(request.note) > 1000:
        raise HTTPException(status_code=400, detail="review note must be 1000 characters or fewer")

    db = SessionLocal()
    try:
        if not db.get(CorrigendumModel, corrigendum_id):
            raise HTTPException(status_code=404, detail="Corrigendum alert not found")
        review = crud.save_corrigendum_review(
            db=db,
            corrigendum_id=corrigendum_id,
            reviewer_email=current_user.get("email", "").lower(),
            status=normalized_status,
            note=request.note.strip() if request.note else None,
        )
        return {
            "status": "SUCCESS",
            "review": {
                "corrigendum_id": review.corrigendum_id,
                "review_status": review.status,
                "review_note": review.note,
                "reviewed_at": review.updated_at.isoformat(),
            },
        }
    finally:
        db.close()


def _serialize_alert_preferences(preferences: Any) -> Dict[str, Any]:
    """Expose preferences without claiming an unconfigured external route is live."""
    try:
        agencies = json.loads(preferences.agencies_json)
        alert_types = json.loads(preferences.alert_types_json)
    except (TypeError, json.JSONDecodeError):
        agencies, alert_types = [], ["closing_date", "tender_security"]
    return {
        "agencies": agencies,
        "alert_types": alert_types,
        "deadline_window_hours": preferences.deadline_window_hours,
        "requested_external_channel": preferences.requested_external_channel,
        "external_delivery_active": False,
    }


def _validate_alert_preference_request(request: AlertPreferenceRequest) -> Dict[str, Any]:
    if request.deadline_window_hours not in {24, 48, 72}:
        raise HTTPException(status_code=400, detail="deadline_window_hours must be 24, 48, or 72")
    allowed_types = {"closing_date", "tender_security"}
    alert_types = sorted(set(request.alert_types))
    if not alert_types or not set(alert_types).issubset(allowed_types):
        raise HTTPException(status_code=400, detail="alert_types must contain closing_date and/or tender_security")
    requested_channel = request.requested_external_channel.lower()
    if requested_channel not in {"in_app", "email", "webhook"}:
        raise HTTPException(status_code=400, detail="requested_external_channel must be in_app, email, or webhook")
    agencies = sorted({agency.strip() for agency in request.agencies if agency and agency.strip()})
    if len(agencies) > 20 or any(len(agency) > 128 for agency in agencies):
        raise HTTPException(status_code=400, detail="select at most 20 agencies with names up to 128 characters")
    return {"agencies": agencies, "alert_types": alert_types, "requested_channel": requested_channel}


@app.get("/api/alerts/preferences")
def get_alert_preferences(
    current_user: Dict[str, Any] = Depends(require_roles([ROLE_ANALYST, ROLE_EXECUTIVE, ROLE_AUDITOR, ROLE_ADMIN])),
):
    """Return the current operator's in-app alert filtering preferences."""
    db = SessionLocal()
    try:
        preferences = crud.get_alert_preferences(db, current_user.get("email", "").lower())
        team_policy = crud.get_team_alert_policy(db)
        effective = preferences if preferences.is_customized else team_policy
        serialized = _serialize_alert_preferences(effective)
        serialized["source"] = "personal" if preferences.is_customized else "team_default"
        return {"status": "SUCCESS", "preferences": serialized}
    finally:
        db.close()


@app.put("/api/alerts/preferences")
def update_alert_preferences(
    request: AlertPreferenceRequest,
    current_user: Dict[str, Any] = Depends(require_roles([ROLE_ANALYST, ROLE_EXECUTIVE, ROLE_AUDITOR, ROLE_ADMIN])),
):
    """Persist validated alert preferences for the signed-in operator."""
    validated = _validate_alert_preference_request(request)

    db = SessionLocal()
    try:
        preferences = crud.save_alert_preferences(
            db=db,
            user_email=current_user.get("email", "").lower(),
            agencies_json=json.dumps(validated["agencies"]),
            alert_types_json=json.dumps(validated["alert_types"]),
            deadline_window_hours=request.deadline_window_hours,
            requested_external_channel=validated["requested_channel"],
        )
        return {
            "status": "SUCCESS",
            "preferences": _serialize_alert_preferences(preferences),
            "message": "In-app preferences saved. External delivery remains disabled until a provider is configured.",
        }
    finally:
        db.close()


@app.get("/api/alerts/team-policy")
def get_team_alert_policy(
    current_user: Dict[str, Any] = Depends(require_roles([ROLE_ANALYST, ROLE_EXECUTIVE, ROLE_AUDITOR, ROLE_ADMIN])),
):
    """Expose the shared policy and whether the current operator can administer it."""
    db = SessionLocal()
    try:
        policy = crud.get_team_alert_policy(db)
        return {
            "status": "SUCCESS",
            "policy": _serialize_alert_preferences(policy),
            "can_manage": current_user.get("role") == ROLE_ADMIN,
            "updated_by": policy.updated_by,
            "updated_at": policy.updated_at.isoformat() if policy.updated_at else None,
        }
    finally:
        db.close()


@app.put("/api/alerts/team-policy")
def update_team_alert_policy(
    request: AlertPreferenceRequest,
    current_user: Dict[str, Any] = Depends(require_roles([ROLE_ADMIN])),
):
    """Set shared defaults for operators who have not saved personal preferences."""
    validated = _validate_alert_preference_request(request)
    db = SessionLocal()
    try:
        policy = crud.save_team_alert_policy(
            db=db,
            agencies_json=json.dumps(validated["agencies"]),
            alert_types_json=json.dumps(validated["alert_types"]),
            deadline_window_hours=request.deadline_window_hours,
            requested_external_channel=validated["requested_channel"],
            updated_by=current_user.get("email", "").lower(),
        )
        return {
            "status": "SUCCESS",
            "policy": _serialize_alert_preferences(policy),
            "message": "Team defaults saved for operators using team-managed alert settings.",
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


# ---------------------------------------------------------------------------
# Real-Time Live e-GP Tender Ingestion & WebSocket Endpoints
# ---------------------------------------------------------------------------

@app.websocket("/api/ws/cartel/live")
async def ws_cartel_live(websocket: WebSocket):
    """
    WebSocket endpoint streaming live e-GP tender award events with instant
    GAT Cartel Radar classification to all connected GIS canvas clients.
    """
    if settings.strict_auth:
        token = websocket.query_params.get("access_token")
        try:
            from backend.auth_jwt import decode_token
            payload = decode_token(token or "")
            if payload.get("type") != "access":
                raise HTTPException(status_code=401, detail="Invalid access token")
        except Exception:
            await websocket.close(code=1008, reason="Authentication required")
            return

    await live_broadcaster.connect(websocket)
    try:
        # Keep connection alive; client can send pings/control messages
        while True:
            try:
                msg = await websocket.receive_text()
                # Echo back control acknowledgements
                if msg == "PING":
                    await websocket.send_text('{"event_type":"PONG"}')
                elif msg == "STATUS":
                    await websocket.send_text(
                        json.dumps({"event_type": "STATUS", **live_broadcaster.get_status()})
                    )
            except WebSocketDisconnect:
                break
            except Exception:
                break
    finally:
        live_broadcaster.disconnect(websocket)


@app.post("/api/cartel/live/toggle")
async def toggle_live_stream(
    current_user: Dict[str, Any] = Depends(require_roles([ROLE_AUDITOR, ROLE_ANALYST, ROLE_EXECUTIVE, ROLE_ADMIN]))
):
    """Pause or resume the background live e-GP tender ingestion stream."""
    new_state = live_broadcaster.toggle()
    return {"stream_state": new_state, **live_broadcaster.get_status()}


@app.get("/api/cartel/live/status")
async def get_live_stream_status(
    current_user: Dict[str, Any] = Depends(require_roles([ROLE_AUDITOR, ROLE_ANALYST, ROLE_EXECUTIVE, ROLE_ADMIN]))
):
    """Return current live stream health, connected client count, and recent events."""
    return live_broadcaster.get_status()


class LiveInjectRequest(BaseModel):
    district: str = "Dhaka"
    division: str = "Dhaka"
    agency: str = "RHD"
    estimated_cost_cr: float = 50.0
    work_type: str = "Road Pavement & Embankment"
    latitude: float = 23.8103
    longitude: float = 90.4125
    is_collusive: Optional[bool] = None
    syndicate: Optional[str] = None
    threat_tier: Optional[str] = None


@app.post("/api/cartel/live/inject")
async def inject_live_tender(
    payload: LiveInjectRequest,
    current_user: Dict[str, Any] = Depends(require_roles([ROLE_AUDITOR, ROLE_ADMIN, ROLE_ANALYST, ROLE_EXECUTIVE]))
):
    """
    Inject a custom tender award event into the live stream immediately.
    Useful for testing canvas sonar blips, collusion arc flares, and QA.
    """
    override = payload.dict(exclude_none=True)
    event = await live_broadcaster.inject(override)
    return {"injected": True, "event": event}


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
