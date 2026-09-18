"""
TenderPulse 4IR AI - Non-Destructive Data Migration Script
Migrates historical and active tender records from data/live_feed.json,
data/users.json, and data/awards_archive.json into the persistent database.
"""

import os
import sys
import json

# Ensure project root is in python path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

from backend.database import engine, init_db, SessionLocal
from backend.models import TenderModel, UserModel, BiddingSyndicateModel
from backend.crud import upsert_tender, upsert_user

def migrate_all():
    print("=================================================================")
    print("  TenderPulse 4IR - JSON to Relational Database Migration")
    print("=================================================================")
    
    # 1. Initialize Tables
    print("\n[*] Initializing database schema...")
    init_db()
    print("[+] Database schema verified and initialized.")

    db = SessionLocal()
    try:
        # 2. Migrate Live Feed Tenders
        live_feed_file = os.path.join(ROOT_DIR, "data", "live_feed.json")
        tenders_migrated = 0
        if os.path.exists(live_feed_file):
            print(f"[*] Reading tenders from {live_feed_file}...")
            with open(live_feed_file, "r", encoding="utf-8") as f:
                feed_data = json.load(f)
            
            for item in feed_data:
                try:
                    upsert_tender(db, item)
                    tenders_migrated += 1
                except Exception as e:
                    print(f"    [!] Error migrating tender {item.get('id')}: {e}")
            print(f"[+] Migrated {tenders_migrated} tender notices into database.")
        else:
            print("[!] data/live_feed.json not found, skipping tenders.")

        # 3. Migrate Users
        users_file = os.path.join(ROOT_DIR, "data", "users.json")
        users_migrated = 0
        if os.path.exists(users_file):
            print(f"[*] Reading users from {users_file}...")
            with open(users_file, "r", encoding="utf-8") as f:
                users_data = json.load(f)
            
            users_list = users_data.get("users", []) if isinstance(users_data, dict) else users_data
            for u in users_list:
                try:
                    upsert_user(db, u)
                    users_migrated += 1
                except Exception as e:
                    print(f"    [!] Error migrating user {u.get('email')}: {e}")
            print(f"[+] Migrated {users_migrated} user profiles into database.")
        else:
            print("[!] data/users.json not found, skipping users.")

        # 4. Migrate Awards & Cartel Telemetry
        awards_file = os.path.join(ROOT_DIR, "data", "awards_archive.json")
        awards_migrated = 0
        if os.path.exists(awards_file):
            print(f"[*] Reading cartel & awards telemetry from {awards_file}...")
            with open(awards_file, "r", encoding="utf-8") as f:
                awards_data = json.load(f)
            
            for a in awards_data:
                try:
                    syndicate = BiddingSyndicateModel(
                        tender_id=str(a.get("tenderId") or a.get("id") or ""),
                        lead_contractor=str(a.get("winner") or a.get("leadContractor") or "Unknown Lead"),
                        syndicate_name=str(a.get("syndicateName") or "Consortium"),
                        co_bidders_json=json.dumps(a.get("bidders") or []),
                        shared_guarantee_no=str(a.get("sharedGuarantee") or "BG-PUB-8812"),
                        risk_score=float(a.get("collusionRisk") or 0.72),
                        risk_category=str(a.get("riskCategory") or "SUSPECTED_COLLUSION")
                    )
                    db.add(syndicate)
                    awards_migrated += 1
                except Exception as e:
                    print(f"    [!] Error migrating award entry: {e}")
            db.commit()
            print(f"[+] Migrated {awards_migrated} cartel/award syndicate records.")

        total_tenders = db.query(TenderModel).count()
        total_users = db.query(UserModel).count()
        total_syndicates = db.query(BiddingSyndicateModel).count()
        
        print("\n=================================================================")
        print(f"  MIGRATION SUMMARY:")
        print(f"  Total Tenders in Database:     {total_tenders}")
        print(f"  Total Users in Database:       {total_users}")
        print(f"  Total Syndicates in Database:  {total_syndicates}")
        print("  DATABASE STATUS: ONLINE & PERSISTED")
        print("=================================================================")

    finally:
        db.close()

if __name__ == "__main__":
    migrate_all()
