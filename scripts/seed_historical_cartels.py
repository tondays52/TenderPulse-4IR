"""
TenderPulse 4IR AI - 5-Year Historical Tender Awards & Cartel Telemetry Seeder
Generates and loads multi-year historical procurement records (tenders, bidder bids,
shared guarantees, and address clusters) into the database and data/awards_archive.json.
"""

import os
import sys
import json
import random

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

from backend.database import SessionLocal, init_db
from backend.models import BiddingSyndicateModel, TenderModel
from backend.cartel_radar import CartelRadarEngine

def seed_historical_cartels():
    print("=================================================================")
    print("  TenderPulse 4IR - 5-Year Historical Cartel Telemetry Seeder")
    print("=================================================================")

    init_db()
    db = SessionLocal()
    engine = CartelRadarEngine()

    try:
        print("[*] Generating multi-year historical procurement dataset...")
        telemetry = engine._generate_enterprise_historical_dataset()

        # Generate additional regional packages
        syndicates_seed = [
            {
                "name": "Padma-Jamuna Highway Syndicate",
                "lead": "Bengal Infra Ltd",
                "members": ["Bengal Infra Ltd", "Shurjo Consortium", "Padma Builders"],
                "bg_prefix": "BG-PRIME-MOT",
                "address": "Suite 804, Sena Kalyan Bhaban, Motijheel, Dhaka",
                "risk": 94.8,
                "category": "CARTEL_RING_IDENTIFIED"
            },
            {
                "name": "Northern Road Sector Ring",
                "lead": "Barind Highway Construction",
                "members": ["Barind Highway Construction", "Teesta Engineers", "Rangpur Civil Works"],
                "bg_prefix": "BG-SONALI-RNG",
                "address": "Holding 12, Station Road, Rangpur Sadar",
                "risk": 87.5,
                "category": "SUSPECTED_COLLUSION"
            },
            {
                "name": "Chittagong Coastal Embankment Cartel",
                "lead": "Karnaphuli Dredging & Marine",
                "members": ["Karnaphuli Dredging & Marine", "Bay Polder Builders", "Chattogram Infra"],
                "bg_prefix": "BG-EBL-AGR",
                "address": "Level 5, Agrabad Commercial Area, Chittagong",
                "risk": 91.2,
                "category": "CARTEL_RING_IDENTIFIED"
            }
        ]

        # Insert or update into BiddingSyndicateModel
        inserted_syndicates = 0
        for s in syndicates_seed:
            existing = db.query(BiddingSyndicateModel).filter(
                BiddingSyndicateModel.syndicate_name == s["name"]
            ).first()

            if not existing:
                syn_rec = BiddingSyndicateModel(
                    tender_id=f"eGP-HIST-{random.randint(1000, 9999)}",
                    lead_contractor=s["lead"],
                    syndicate_name=s["name"],
                    co_bidders_json=json.dumps(s["members"]),
                    shared_guarantee_no=f"{s['bg_prefix']}-8812",
                    risk_score=s["risk"] / 100.0,
                    risk_category=s["category"]
                )
                db.add(syn_rec)
                inserted_syndicates += 1

        db.commit()
        print(f"[+] Seeded {inserted_syndicates} syndicate profiles into database.")

        # Save comprehensive telemetry to data/awards_archive.json
        archive_path = os.path.join(ROOT_DIR, "data", "awards_archive.json")
        archive_records = []
        for t in telemetry:
            archive_records.append({
                "id": t["tender_id"],
                "tenderId": t["tender_id"],
                "agency": t["agency"],
                "winner": t["winner"],
                "leadContractor": t["winner"],
                "estimatedCost": t["estimated_cost"],
                "bidders": t["bidders"],
                "collusionRisk": 0.92,
                "riskCategory": "CARTEL_RING_IDENTIFIED",
                "sharedGuarantee": t["bidders"][0].get("bank_guarantee_no", "BG-PUB-8812")
            })

        with open(archive_path, "w", encoding="utf-8") as f:
            json.dump(archive_records, f, indent=2)
        print(f"[+] Saved historical multi-vector archive to {archive_path} ({len(archive_records)} packages).")

        total_syndicates = db.query(BiddingSyndicateModel).count()
        print("\n=================================================================")
        print(f"  HISTORICAL CARTEL SEEDING COMPLETE:")
        print(f"  Total Syndicates in Database: {total_syndicates}")
        print("  Collusion Vectors Ingested:   Shared Guarantees, Address Clusters,")
        print("                                Cover-Bidding Spreads, Rotational Wins")
        print("=================================================================")

    finally:
        db.close()

if __name__ == "__main__":
    seed_historical_cartels()
