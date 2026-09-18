"""
TenderPulse 4IR AI - Database CRUD Operations & Spatial Queries
Provides high-performance queries, spatial filtering, and upsert logic.
"""

import json
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from backend.models import TenderModel, BiddingSyndicateModel, SarAuditModel, UserModel, CorrigendumModel


DISTRICT_COORDS = {
    "Dhaka": (23.8103, 90.4125),
    "Gazipur": (23.9888, 90.3887),
    "Narayanganj": (23.6238, 90.5000),
    "Chattogram": (22.3569, 91.7832),
    "Chittagong": (22.3569, 91.7832),
    "Sylhet": (24.8949, 91.8687),
    "Rajshahi": (24.3745, 88.6042),
    "Khulna": (22.8456, 89.5403),
    "Barishal": (22.7010, 90.3535),
    "Rangpur": (25.7439, 89.2752),
    "Mymensingh": (24.7471, 90.4203),
    "Faridpur": (23.6071, 89.8429),
    "Bogura": (24.8465, 89.3777),
    "Cumilla": (23.4682, 91.1788),
    "Comilla": (23.4682, 91.1788),
    "Cox's Bazar": (21.4272, 92.0058),
    "Jessore": (23.1664, 89.2081),
    "Jashore": (23.1664, 89.2081),
    "Noakhali": (22.8696, 91.0991)
}


def upsert_tender(db: Session, data: Dict[str, Any]) -> TenderModel:
    """
    Inserts or updates a tender record by tender_id.
    """
    t_id = str(data.get("id") or data.get("tenderId") or data.get("tender_id"))
    tender = db.query(TenderModel).filter(TenderModel.tender_id == t_id).first()

    raw_json_str = json.dumps(data) if not isinstance(data.get("raw_json"), str) else data.get("raw_json")

    # District & Spatial coordinates defaults
    dist = str(data.get("district") or data.get("location") or "Dhaka").strip()
    lat = data.get("lat") or data.get("latitude")
    lon = data.get("lng") or data.get("lon") or data.get("longitude")

    if lat is None or lon is None:
        coords = DISTRICT_COORDS.get(dist.title(), DISTRICT_COORDS["Dhaka"])
        lat = coords[0]
        lon = coords[1]

    bbox = data.get("bbox") or []
    min_lat = bbox[0] if len(bbox) >= 4 else round(lat - 0.05, 4)
    min_lon = bbox[1] if len(bbox) >= 4 else round(lon - 0.05, 4)
    max_lat = bbox[2] if len(bbox) >= 4 else round(lat + 0.05, 4)
    max_lon = bbox[3] if len(bbox) >= 4 else round(lon + 0.05, 4)


    cost = float(data.get("cost") or data.get("estimated_cost") or data.get("estimatedCost") or 0.0)
    security = float(data.get("security") or data.get("tender_security") or data.get("tenderSecurity") or 0.0)
    liquid = float(data.get("liquidAssetsReq") or data.get("liquid_assets_req") or 0.0)
    turnover = float(data.get("turnoverReq") or data.get("turnover_req") or 0.0)

    if not tender:
        tender = TenderModel(
            tender_id=t_id,
            app_id=str(data.get("appId") or data.get("app_id") or ""),
            ref_no=str(data.get("refNo") or data.get("ref_no") or ""),
            title=str(data.get("title") or "Civil Works Package"),
            agency=str(data.get("agency") or "RHD"),
            ministry=str(data.get("ministry") or ""),
            division=str(data.get("division") or "Dhaka"),
            district=str(data.get("district") or data.get("location") or "Dhaka"),
            work_type=str(data.get("nature") or data.get("work_type") or "Works"),
            procurement_method=str(data.get("method") or data.get("procurement_method") or "OTM"),
            std_document=str(data.get("std") or data.get("std_document") or "e-PW3"),
            estimated_cost=cost,
            tender_security=security,
            liquid_assets_req=liquid,
            turnover_req=turnover,
            latitude=lat,
            longitude=lon,
            bbox_min_lat=min_lat,
            bbox_min_lon=min_lon,
            bbox_max_lat=max_lat,
            bbox_max_lon=max_lon,
            publish_date=str(data.get("publishedDate") or data.get("publish_date") or ""),
            closing_date=str(data.get("closingDate") or data.get("closing_date") or ""),
            is_live=bool(data.get("isLive", True)),
            raw_json=raw_json_str
        )
        db.add(tender)
    else:
        tender.title = str(data.get("title") or tender.title)
        tender.agency = str(data.get("agency") or tender.agency)
        tender.district = str(data.get("district") or data.get("location") or tender.district)
        tender.estimated_cost = cost if cost > 0 else tender.estimated_cost
        tender.closing_date = str(data.get("closingDate") or data.get("closing_date") or tender.closing_date)
        tender.raw_json = raw_json_str
        if lat: tender.latitude = lat
        if lon: tender.longitude = lon
        if min_lat: tender.bbox_min_lat = min_lat
        if min_lon: tender.bbox_min_lon = min_lon
        if max_lat: tender.bbox_max_lat = max_lat
        if max_lon: tender.bbox_max_lon = max_lon

    db.commit()
    db.refresh(tender)
    return tender


def get_tenders(
    db: Session,
    limit: int = 50,
    offset: int = 0,
    agency: Optional[str] = None,
    district: Optional[str] = None,
    keyword: Optional[str] = None
) -> List[TenderModel]:
    """
    Retrieves filtered list of tenders with pagination.
    """
    query = db.query(TenderModel)

    if agency and agency.upper() != "ALL":
        query = query.filter(or_(
            TenderModel.agency.ilike(f"%{agency}%"),
            TenderModel.ministry.ilike(f"%{agency}%")
        ))

    if district:
        query = query.filter(TenderModel.district.ilike(f"%{district}%"))

    if keyword:
        kw = f"%{keyword}%"
        query = query.filter(or_(
            TenderModel.title.ilike(kw),
            TenderModel.ref_no.ilike(kw),
            TenderModel.tender_id.ilike(kw),
            TenderModel.agency.ilike(kw)
        ))

    return query.order_by(TenderModel.id.desc()).offset(offset).limit(limit).all()


def get_tender_by_id(db: Session, tender_id: str) -> Optional[TenderModel]:
    return db.query(TenderModel).filter(TenderModel.tender_id == tender_id).first()


def get_tenders_by_bbox(db: Session, min_lat: float, min_lon: float, max_lat: float, max_lon: float) -> List[TenderModel]:
    """
    Geospatial Bounding Box query: returns tenders located within coordinate boundaries.
    """
    return db.query(TenderModel).filter(
        and_(
            TenderModel.latitude >= min_lat,
            TenderModel.latitude <= max_lat,
            TenderModel.longitude >= min_lon,
            TenderModel.longitude <= max_lon
        )
    ).all()


def count_tenders(db: Session, agency: Optional[str] = None) -> int:
    query = db.query(TenderModel)
    if agency and agency.upper() != "ALL":
        query = query.filter(TenderModel.agency.ilike(f"%{agency}%"))
    return query.count()


def upsert_user(db: Session, user_data: Dict[str, Any]) -> UserModel:
    email = user_data.get("email")
    user = db.query(UserModel).filter(UserModel.email == email).first()
    if not user:
        user = UserModel(
            email=email,
            name=user_data.get("name", "User"),
            password_hash=user_data.get("password_hash", ""),
            salt=user_data.get("salt", ""),
            role=user_data.get("role", "Tender Analyst"),
            agency=user_data.get("agency", "Di-Tender Ltd."),
            is_active=user_data.get("is_active", True)
        )
        db.add(user)
    else:
        user.name = user_data.get("name", user.name)
        user.role = user_data.get("role", user.role)
        user.agency = user_data.get("agency", user.agency)
    db.commit()
    db.refresh(user)
    return user


def get_user_by_email(db: Session, email: str) -> Optional[UserModel]:
    return db.query(UserModel).filter(UserModel.email == email).first()


def create_corrigendum(
    db: Session,
    tender_id: str,
    field_changed: str,
    old_value: str,
    new_value: str,
    reason: str = ""
) -> CorrigendumModel:
    """
    Creates and records a tender corrigendum amendment event.
    """
    count = db.query(CorrigendumModel).filter(CorrigendumModel.tender_id == tender_id).count()
    corrigendum = CorrigendumModel(
        tender_id=tender_id,
        corrigendum_no=count + 1,
        field_changed=field_changed,
        old_value=str(old_value),
        new_value=str(new_value),
        reason=reason
    )
    db.add(corrigendum)
    db.commit()
    db.refresh(corrigendum)
    return corrigendum


def get_corrigenda(
    db: Session,
    tender_id: Optional[str] = None,
    limit: int = 50
) -> List[CorrigendumModel]:
    """
    Retrieves recorded corrigenda, optionally filtered by tender_id.
    """
    query = db.query(CorrigendumModel)
    if tender_id:
        query = query.filter(CorrigendumModel.tender_id == tender_id)
    return query.order_by(CorrigendumModel.detected_at.desc()).limit(limit).all()

