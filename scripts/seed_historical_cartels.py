"""
TenderPulse 4IR AI - 50,000+ Multi-Year Historical Tender Awards & Cartel Seeder
Generates and seeds 50,000+ realistic procurement awards (2021-2026) across 8 major
Bangladeshi agencies, 8 divisions, and 64 districts.
Embeds 16 distinct cartel syndicates (~5,500 flagged records) with all 4 forensic vectors:
1. Shared/Consecutive Bank Guarantees
2. Corporate Address & Co-Location Clustering
3. Artificial Cover-Bidding Spreads (+2.5% to +8.5%)
4. Rotational Winning Reciprocity Matrices
"""

import os
import sys
import json
import time
import random
from typing import List, Dict, Any

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

from backend.database import SessionLocal, init_db, engine
from backend.models import HistoricalAwardModel, BiddingSyndicateModel

# ----------------------------------------------------------------------
# Geography Reference: 8 Divisions and all 64 Districts of Bangladesh
# ----------------------------------------------------------------------
DIVISIONS_AND_DISTRICTS = {
    "Dhaka": ["Dhaka", "Gazipur", "Narayanganj", "Tangail", "Faridpur", "Manikganj", "Munshiganj", "Narsingdi", "Gopalganj", "Madaripur", "Rajbari", "Shariatpur", "Kishoreganj"],
    "Chattogram": ["Chattogram", "Cox's Bazar", "Cumilla", "Feni", "Brahmanbaria", "Noakhali", "Chandpur", "Lakshmipur", "Khagrachhari", "Rangamati", "Bandarban"],
    "Rajshahi": ["Rajshahi", "Bogura", "Pabna", "Sirajganj", "Naogaon", "Natore", "Chapai Nawabganj", "Joypurhat"],
    "Khulna": ["Khulna", "Jashore", "Kushtia", "Satkhira", "Bagerhat", "Jhenaidah", "Chuadanga", "Magura", "Meherpur", "Narail"],
    "Barishal": ["Barishal", "Patuakhali", "Bhola", "Pirojpur", "Barguna", "Jhalokati"],
    "Sylhet": ["Sylhet", "Sunamganj", "Moulvibazar", "Habiganj"],
    "Rangpur": ["Rangpur", "Dinajpur", "Kurigram", "Gaibandha", "Nilphamari", "Lalmonirhat", "Thakurgaon", "Panchagarh"],
    "Mymensingh": ["Mymensingh", "Jamalpur", "Netrokona", "Sherpur"]
}

AGENCIES = [
    "Roads and Highways Department (RHD)",
    "Local Government Engineering Department (LGED)",
    "Bangladesh Water Development Board (BWDB)",
    "Public Works Department (PWD)",
    "Department of Public Health Engineering (DPHE)",
    "Power Grid Company of Bangladesh (PGCB)",
    "Bangladesh Rural Electrification Board (BREB)",
    "Education Engineering Department (EED)"
]

BANKS = [
    ("Sonali Bank PLC", "SONALI"),
    ("Janata Bank PLC", "JANATA"),
    ("Agrani Bank PLC", "AGRANI"),
    ("Pubali Bank PLC", "PUB"),
    ("Eastern Bank PLC", "EBL"),
    ("City Bank PLC", "CITY"),
    ("Prime Bank PLC", "PRIME"),
    ("Islami Bank Bangladesh PLC", "ISLAMI"),
    ("Dutch-Bangla Bank PLC", "DBBL"),
    ("BRAC Bank PLC", "BRAC"),
    ("Uttara Bank PLC", "UTTARA"),
    ("Mutual Trust Bank PLC", "MTB")
]

CLEAN_CONTRACTOR_PREFIXES = [
    "Apex", "Bengal", "Delta", "National", "Shurjo", "Progressive", "Concord",
    "United", "Standard", "Evergreen", "Pacific", "Pioneer", "Horizon", "Sunrise",
    " Meghna", "Padma", "Jamuna", "Karnaphuli", "Teesta", "Brahmaputra", "Surma",
    "Kushiara", "Daffodil", "Navana", "Mir", "Spectra", "Abdul Monem", "Max",
    "Tama", "DCL", "Cosmo", "Confidence", "Orion", "Trust", "Prime", "Classic"
]
CLEAN_CONTRACTOR_SUFFIXES = [
    "Constructions Ltd", "Builders & Engineers", "Engineering Works",
    "Infra Projects Ltd", "Civil Tech Ltd", "Development Consortium",
    "Enterprise Ltd", "Holdings Ltd", "Trading & Contracting", "Associates Ltd"
]

CLEAN_CONTRACTORS = [
    f"{p.strip()} {s}" for p in CLEAN_CONTRACTOR_PREFIXES for s in CLEAN_CONTRACTOR_SUFFIXES[:7]
]

# ----------------------------------------------------------------------
# 16 Forensic Cartel Syndicates Specification
# ----------------------------------------------------------------------
CARTEL_SYNDICATES = [
    {
        "name": "Padma-Jamuna Highway Syndicate",
        "lead": "Bengal Infra Ltd",
        "members": ["Bengal Infra Ltd", "Shurjo Consortium", "Padma Builders"],
        "agency": "Roads and Highways Department (RHD)",
        "division": "Dhaka",
        "districts": ["Dhaka", "Faridpur", "Manikganj"],
        "address": "Suite 804, Sena Kalyan Bhaban, Motijheel, Dhaka",
        "bg_bank": "PRIME",
        "bg_branch": "MOT",
        "vector": "GUARANTEE",
        "risk": 94.8,
        "category": "CARTEL_RING_IDENTIFIED",
        "spread_range": (3.5, 6.5),
        "citation": "PPR-2008 Rule 127(1)(a) & Sec 15 Competition Act"
    },
    {
        "name": "Northern Road Sector Ring",
        "lead": "Barind Highway Construction",
        "members": ["Barind Highway Construction", "Teesta Engineers", "Rangpur Civil Works"],
        "agency": "Local Government Engineering Department (LGED)",
        "division": "Rangpur",
        "districts": ["Rangpur", "Dinajpur", "Bogura"],
        "address": "Holding 12, Station Road, Rangpur Sadar",
        "bg_bank": "SONALI",
        "bg_branch": "RNG",
        "vector": "GUARANTEE",
        "risk": 89.5,
        "category": "CARTEL_RING_IDENTIFIED",
        "spread_range": (3.2, 5.8),
        "citation": "PPR-2008 Rule 127(1)(b) & Section 64 PPA 2006"
    },
    {
        "name": "Chittagong Coastal Embankment Cartel",
        "lead": "Karnaphuli Dredging & Marine",
        "members": ["Karnaphuli Dredging & Marine", "Bay Polder Builders", "Chattogram Infra"],
        "agency": "Bangladesh Water Development Board (BWDB)",
        "division": "Chattogram",
        "districts": ["Chattogram", "Cox's Bazar"],
        "address": "Level 5, Agrabad Commercial Area, Chittagong",
        "bg_bank": "EBL",
        "bg_branch": "AGR",
        "vector": "ADDRESS",
        "risk": 92.4,
        "category": "CARTEL_RING_IDENTIFIED",
        "spread_range": (4.0, 7.2),
        "citation": "PPR-2008 Rule 127(1)(c) - Corporate Co-location"
    },
    {
        "name": "Sylhet Haor Flood Protection Guild",
        "lead": "Surma River Protection Ltd",
        "members": ["Surma River Protection Ltd", "Kushiara Earthworks", "Haor Dredging Consortium"],
        "agency": "Bangladesh Water Development Board (BWDB)",
        "division": "Sylhet",
        "districts": ["Sylhet", "Sunamganj", "Moulvibazar"],
        "address": "Holding 44, Jail Road, Sylhet Sadar",
        "bg_bank": "PUB",
        "bg_branch": "SYL",
        "vector": "COVER_BID",
        "risk": 88.7,
        "category": "SUSPECTED_COLLUSION",
        "spread_range": (4.5, 7.8),
        "citation": "PPR-2008 Rule 127(2) - Artificial Price Cover"
    },
    {
        "name": "Barisal River Dredging Alliance",
        "lead": "Kirtankhola Marine Works",
        "members": ["Kirtankhola Marine Works", "Payra Dredgers Ltd", "Baleshwar Marine Builders"],
        "agency": "Bangladesh Water Development Board (BWDB)",
        "division": "Barishal",
        "districts": ["Barishal", "Patuakhali", "Bhola"],
        "address": "River Port Road, Barishal Sadar",
        "bg_bank": "AGRANI",
        "bg_branch": "BAR",
        "vector": "ROTATIONAL",
        "risk": 91.0,
        "category": "CARTEL_RING_IDENTIFIED",
        "spread_range": (3.8, 6.2),
        "citation": "PPR-2008 Rule 127(1) - Reciprocal Bid Rotation"
    },
    {
        "name": "Rajshahi Urban Infrastructure Syndicate",
        "lead": "Barendra Construction Co",
        "members": ["Barendra Construction Co", "Padma Civil Engineering", "Rajshahi Builders Alliance"],
        "agency": "Public Works Department (PWD)",
        "division": "Rajshahi",
        "districts": ["Rajshahi", "Naogaon", "Natore"],
        "address": "Shaheb Bazar, Rajshahi Sadar",
        "bg_bank": "JANATA",
        "bg_branch": "RAJ",
        "vector": "COVER_BID",
        "risk": 86.5,
        "category": "SUSPECTED_COLLUSION",
        "spread_range": (4.8, 7.5),
        "citation": "PPR-2008 Rule 127 & Competition Act 2012"
    },
    {
        "name": "Khulna Coastal Salinity Treatment Circle",
        "lead": "Rupsha Water Systems Ltd",
        "members": ["Rupsha Water Systems Ltd", "Bhairab Environmental Works", "Sundarban Filtration Ltd"],
        "agency": "Department of Public Health Engineering (DPHE)",
        "division": "Khulna",
        "districts": ["Khulna", "Satkhira", "Bagerhat"],
        "address": "KDA Commercial Area, Khulna Sadar",
        "bg_bank": "ISLAMI",
        "bg_branch": "KHU",
        "vector": "GUARANTEE",
        "risk": 90.3,
        "category": "CARTEL_RING_IDENTIFIED",
        "spread_range": (3.0, 6.0),
        "citation": "PPR-2008 Rule 127(1)(a)"
    },
    {
        "name": "Dhaka South Metro Building Cartel",
        "lead": "Capital Heights Ltd",
        "members": ["Capital Heights Ltd", "Metropolitan Engineering", "Nagarik Housing Infra"],
        "agency": "Public Works Department (PWD)",
        "division": "Dhaka",
        "districts": ["Dhaka", "Narayanganj"],
        "address": "Level 9, Jiban Bima Bhaban, Dilkusha, Dhaka",
        "bg_bank": "PUB",
        "bg_branch": "DIL",
        "vector": "ADDRESS",
        "risk": 93.6,
        "category": "CARTEL_RING_IDENTIFIED",
        "spread_range": (4.2, 7.0),
        "citation": "PPR-2008 Rule 127(1)(c)"
    },
    {
        "name": "PGCB High-Voltage Grid Syndicate",
        "lead": "ElectroGrid Powerlines Ltd",
        "members": ["ElectroGrid Powerlines Ltd", "Substation Infra Works", "Megawatt Transmission Ltd"],
        "agency": "Power Grid Company of Bangladesh (PGCB)",
        "division": "Chattogram",
        "districts": ["Cumilla", "Feni", "Noakhali"],
        "address": "Station Road, Cumilla Sadar",
        "bg_bank": "CITY",
        "bg_branch": "COM",
        "vector": "COVER_BID",
        "risk": 87.8,
        "category": "SUSPECTED_COLLUSION",
        "spread_range": (5.0, 8.2),
        "citation": "PPR-2008 Rule 127(2)"
    },
    {
        "name": "BREB Rural Electrification Ring",
        "lead": "Palli Power Grid Builders",
        "members": ["Palli Power Grid Builders", "Rural Line Distribution Ltd", "Brahmaputra Power Consortium"],
        "agency": "Bangladesh Rural Electrification Board (BREB)",
        "division": "Mymensingh",
        "districts": ["Mymensingh", "Jamalpur", "Netrokona"],
        "address": "Kashor, Mymensingh Sadar",
        "bg_bank": "DBBL",
        "bg_branch": "MYM",
        "vector": "ROTATIONAL",
        "risk": 89.2,
        "category": "CARTEL_RING_IDENTIFIED",
        "spread_range": (3.5, 6.8),
        "citation": "PPR-2008 Rule 127(1)"
    },
    {
        "name": "EED Model College & School Ring",
        "lead": "Bikrampur Educational Builders",
        "members": ["Bikrampur Educational Builders", "Shiksha Bhaban Engineering", "Meghna Model Schools Ltd"],
        "agency": "Education Engineering Department (EED)",
        "division": "Dhaka",
        "districts": ["Tangail", "Gazipur", "Narsingdi"],
        "address": "College Road, Tangail Sadar",
        "bg_bank": "JANATA",
        "bg_branch": "TGL",
        "vector": "GUARANTEE",
        "risk": 88.0,
        "category": "SUSPECTED_COLLUSION",
        "spread_range": (4.0, 7.5),
        "citation": "PPR-2008 Rule 127(1)(a)"
    },
    {
        "name": "Cox's Bazar Marine Drive Consortium",
        "lead": "Bay Marine Roadways",
        "members": ["Bay Marine Roadways", "Oceanic Highway Infra", "Himchari Civil Contractors"],
        "agency": "Roads and Highways Department (RHD)",
        "division": "Chattogram",
        "districts": ["Cox's Bazar"],
        "address": "Hotel Motel Zone Road, Cox's Bazar",
        "bg_bank": "BRAC",
        "bg_branch": "CXB",
        "vector": "COVER_BID",
        "risk": 91.5,
        "category": "CARTEL_RING_IDENTIFIED",
        "spread_range": (4.5, 8.0),
        "citation": "PPR-2008 Rule 127(2)"
    },
    {
        "name": "Kushtia-Jessore Highway Circle",
        "lead": "Gorai Infrastructure Ltd",
        "members": ["Gorai Infrastructure Ltd", "Bhairab Road Developers", "Southwest Asphalt Works"],
        "agency": "Local Government Engineering Department (LGED)",
        "division": "Khulna",
        "districts": ["Jashore", "Kushtia", "Jhenaidah"],
        "address": "Mujib Sarak, Jashore Sadar",
        "bg_bank": "SONALI",
        "bg_branch": "JSH",
        "vector": "ROTATIONAL",
        "risk": 88.5,
        "category": "CARTEL_RING_IDENTIFIED",
        "spread_range": (3.2, 6.0),
        "citation": "PPR-2008 Rule 127(1)"
    },
    {
        "name": "North Bengal Deep Tube Well Ring",
        "lead": "Barind Aqua Systems",
        "members": ["Barind Aqua Systems", "Teesta Water Works", "Uttara Drilling Consortium"],
        "agency": "Department of Public Health Engineering (DPHE)",
        "division": "Rangpur",
        "districts": ["Dinajpur", "Kurigram", "Gaibandha"],
        "address": "Court Road, Dinajpur Sadar",
        "bg_bank": "PUB",
        "bg_branch": "DIN",
        "vector": "ADDRESS",
        "risk": 89.0,
        "category": "SUSPECTED_COLLUSION",
        "spread_range": (3.6, 6.4),
        "citation": "PPR-2008 Rule 127(1)(c)"
    },
    {
        "name": "Meghna Bridge Approach Syndicate",
        "lead": "Padma Meghna Bridge Infra",
        "members": ["Padma Meghna Bridge Infra", "Munshiganj Civil Engineering", "Chandpur Riverbank Builders"],
        "agency": "Roads and Highways Department (RHD)",
        "division": "Dhaka",
        "districts": ["Munshiganj", "Chandpur"],
        "address": "Sena Kalyan Bhaban, Motijheel, Dhaka",
        "bg_bank": "CITY",
        "bg_branch": "MOT",
        "vector": "GUARANTEE",
        "risk": 93.0,
        "category": "CARTEL_RING_IDENTIFIED",
        "spread_range": (4.2, 7.8),
        "citation": "PPR-2008 Rule 127(1)(a)"
    },
    {
        "name": "Sundarbans Polder Restoration Ring",
        "lead": "Mangrove Coastal Protection",
        "members": ["Mangrove Coastal Protection", "Satkhira Embankment Works", "Coastal Delta Engineering"],
        "agency": "Bangladesh Water Development Board (BWDB)",
        "division": "Khulna",
        "districts": ["Satkhira", "Bagerhat"],
        "address": "Post Office Road, Satkhira Sadar",
        "bg_bank": "AGRANI",
        "bg_branch": "STK",
        "vector": "ROTATIONAL",
        "risk": 90.5,
        "category": "CARTEL_RING_IDENTIFIED",
        "spread_range": (3.5, 6.5),
        "citation": "PPR-2008 Rule 127(1)"
    }
]


def seed_50k_historical_awards(target_count: int = 50200, batch_size: int = 5000):
    print("=================================================================")
    print(f"  TenderPulse 4IR - 50,000+ Historical Cartel Telemetry Seeder")
    print(f"  Target: {target_count:,} records (2021-2026 across 64 Districts)")
    print("=================================================================")

    init_db()
    db = SessionLocal()

    start_time = time.time()
    try:
        current_count = db.query(HistoricalAwardModel).count()
        if current_count >= target_count:
            print(f"[!] Database already has {current_count:,} historical award records.")
            print("[*] Re-verifying syndicate profiles and summary artifacts...")
            _seed_syndicate_models(db)
            _generate_summary_archive(db)
            return

        # If partial records exist, truncate to ensure clean deterministic seeding
        if current_count > 0:
            print(f"[*] Clearing existing {current_count:,} partial historical records...")
            db.query(HistoricalAwardModel).delete()
            db.commit()

        # Seed the 16 BiddingSyndicateModel profiles first
        _seed_syndicate_models(db)

        # Plan allocation: ~11% collusive (5,500 records), ~89% clean (44,700 records)
        collusive_target = 5500
        clean_target = target_count - collusive_target
        records_per_syndicate = collusive_target // len(CARTEL_SYNDICATES)

        print(f"[*] Generating {collusive_target:,} collusive packages across 16 syndicates...")
        print(f"[*] Generating {clean_target:,} clean competitive procurement packages...")

        inserted_total = 0
        batch = []
        tender_counter = 1000000

        # -------------------------------------------------------------
        # 1. Generate Collusive Packages (Vector Embedded)
        # -------------------------------------------------------------
        for syn_idx, syn in enumerate(CARTEL_SYNDICATES):
            members = syn["members"]
            lead = syn["lead"]
            vector = syn["vector"]
            base_bg_serial = 8000 + (syn_idx * 500)

            for i in range(records_per_syndicate):
                tender_counter += 1
                t_id = f"eGP-{tender_counter}"
                year = random.choice([2021, 2022, 2023, 2024, 2025, 2026])
                district = random.choice(syn["districts"])
                est_cost = round(random.uniform(15000000.0, 250000000.0), -4)

                # Determine winner: Rotational syndicates cycle through members
                if vector == "ROTATIONAL":
                    winner = members[i % len(members)]
                else:
                    # In non-rotational rings, lead wins 75% of time, others take turn
                    winner = lead if random.random() < 0.75 else random.choice(members[1:])

                winner_price = round(est_cost * random.uniform(0.94, 0.98), -3)

                # Build bidder list with forensic vector signatures
                bidders = []
                bg_seq = base_bg_serial + (i * 3)

                for m_idx, m in enumerate(members):
                    is_win = (m == winner)
                    if is_win:
                        b_price = winner_price
                    else:
                        # Vector 3: Artificial cover bidding spread (+2.5% to +8.5%)
                        spread_pct = random.uniform(*syn["spread_range"])
                        b_price = round(winner_price * (1.0 + (spread_pct / 100.0)), -3)

                    # Vector 1: Consecutive / shared bank guarantee serial
                    if vector == "GUARANTEE" or random.random() < 0.8:
                        bg_num = f"BG-{syn['bg_bank']}-{syn['bg_branch']}-{bg_seq + m_idx}"
                    else:
                        bg_num = f"BG-{syn['bg_bank']}-{syn['bg_branch']}-{random.randint(1000, 9999)}"

                    # Vector 2: Corporate address co-location
                    if vector == "ADDRESS" or random.random() < 0.7:
                        # Slight suite suffix variation or identical
                        if m_idx == 0:
                            addr = syn["address"]
                        else:
                            addr = syn["address"].replace("Suite 804,", "Suite 804 (Wing B),").replace("Level 5,", "5th Floor,")
                    else:
                        addr = f"Holding {random.randint(10, 99)}, Main Road, {district}"

                    bidders.append({
                        "name": m,
                        "contractor_name": m,
                        "bid_price": b_price,
                        "price": b_price,
                        "bank_guarantee_no": bg_num,
                        "guarantee": bg_num,
                        "registered_address": addr,
                        "address": addr,
                        "is_winner": is_win
                    })

                record = {
                    "tender_id": t_id,
                    "agency": syn["agency"],
                    "division": syn["division"],
                    "district": district,
                    "year": year,
                    "procurement_type": "Works",
                    "title": f"{syn['agency'].split('(')[-1].replace(')', '')} Infrastructure Package {district}-{year}-{random.randint(100, 999)}",
                    "estimated_cost": est_cost,
                    "winning_contractor": winner,
                    "winning_price": winner_price,
                    "bidders_count": len(bidders),
                    "bidders_json": json.dumps(bidders),
                    "has_collusion_flag": True,
                    "collusion_vector": vector,
                    "syndicate_name": syn["name"]
                }
                batch.append(record)

                if len(batch) >= batch_size:
                    db.bulk_insert_mappings(HistoricalAwardModel, batch)
                    db.commit()
                    inserted_total += len(batch)
                    batch = []
                    print(f"  [+] Seeded {inserted_total:,} / {target_count:,} records...")

        # -------------------------------------------------------------
        # 2. Generate Clean Competitive Packages
        # -------------------------------------------------------------
        remaining = target_count - (inserted_total + len(batch))
        print(f"[*] Generating {remaining:,} clean competitive packages across 64 districts...")

        divisions_keys = list(DIVISIONS_AND_DISTRICTS.keys())

        for _ in range(remaining):
            tender_counter += 1
            t_id = f"eGP-{tender_counter}"
            agency = random.choice(AGENCIES)
            div = random.choice(divisions_keys)
            dist = random.choice(DIVISIONS_AND_DISTRICTS[div])
            year = random.choice([2021, 2022, 2023, 2024, 2025, 2026])
            est_cost = round(random.uniform(8000000.0, 320000000.0), -4)

            # Pick 3 to 5 distinct clean contractors
            b_count = random.choice([3, 3, 3, 4, 5])
            selected_contractors = random.sample(CLEAN_CONTRACTORS, b_count)
            winner = selected_contractors[0]
            winner_price = round(est_cost * random.uniform(0.88, 0.96), -3)

            bidders = []
            for idx, c_name in enumerate(selected_contractors):
                is_win = (c_name == winner)
                if is_win:
                    p = winner_price
                else:
                    # Realistic healthy competitive spreads (-5% to +15%)
                    margin = random.uniform(1.02, 1.15)
                    p = round(winner_price * margin, -3)

                b_bank, b_prefix = random.choice(BANKS)
                bg_num = f"BG-{b_prefix}-{random.choice(['DHK', 'CTG', 'RAJ', 'KHU', 'BAR', 'SYL', 'RNG', 'MYM'])}-{random.randint(10000, 99999)}"
                addr = f"Holding {random.randint(1, 150)}, Road {random.randint(1, 30)}, {dist}"

                bidders.append({
                    "name": c_name,
                    "contractor_name": c_name,
                    "bid_price": p,
                    "price": p,
                    "bank_guarantee_no": bg_num,
                    "guarantee": bg_num,
                    "registered_address": addr,
                    "address": addr,
                    "is_winner": is_win
                })

            record = {
                "tender_id": t_id,
                "agency": agency,
                "division": div,
                "district": dist,
                "year": year,
                "procurement_type": "Works",
                "title": f"Procurement of Works: {dist} Sector Improvement ({year})",
                "estimated_cost": est_cost,
                "winning_contractor": winner,
                "winning_price": winner_price,
                "bidders_count": len(bidders),
                "bidders_json": json.dumps(bidders),
                "has_collusion_flag": False,
                "collusion_vector": "CLEAN",
                "syndicate_name": None
            }
            batch.append(record)

            if len(batch) >= batch_size:
                db.bulk_insert_mappings(HistoricalAwardModel, batch)
                db.commit()
                inserted_total += len(batch)
                batch = []
                print(f"  [+] Seeded {inserted_total:,} / {target_count:,} records...")

        if batch:
            db.bulk_insert_mappings(HistoricalAwardModel, batch)
            db.commit()
            inserted_total += len(batch)
            batch = []

        elapsed = time.time() - start_time
        final_count = db.query(HistoricalAwardModel).count()
        print(f"\n[+] Bulk Seeding Completed in {elapsed:.2f} seconds!")
        print(f"    Total Historical Records: {final_count:,}")
        print(f"    Flagged Collusive Awards: {collusive_count:,} ({collusive_count / final_count * 100:.1f}%)")

        _generate_summary_archive(db)

    finally:
        db.close()


def _seed_syndicate_models(db):
    """
    Upserts BiddingSyndicateModel records for all 16 cartel rings.
    """
    inserted = 0
    for s in CARTEL_SYNDICATES:
        existing = db.query(BiddingSyndicateModel).filter(
            BiddingSyndicateModel.syndicate_name == s["name"]
        ).first()

        if not existing:
            syn_rec = BiddingSyndicateModel(
                tender_id=f"HIST-{s['bg_bank']}-{random.randint(1000, 9999)}",
                lead_contractor=s["lead"],
                syndicate_name=s["name"],
                co_bidders_json=json.dumps(s["members"]),
                shared_guarantee_no=f"BG-{s['bg_bank']}-{s['bg_branch']}-8812",
                risk_score=s["risk"] / 100.0,
                risk_category=s["category"]
            )
            db.add(syn_rec)
            inserted += 1

    db.commit()
    print(f"[+] Verified {len(CARTEL_SYNDICATES)} cartel syndicate profiles in BiddingSyndicateModel.")


def _generate_summary_archive(db):
    """
    Generates data/awards_archive_summary.json and data/awards_archive.json.
    """
    print("[*] Generating forensic summaries and sample archive files...")
    total_count = db.query(HistoricalAwardModel).count()
    collusive_count = db.query(HistoricalAwardModel).filter(HistoricalAwardModel.has_collusion_flag == True).count()

    # Query top 200 flagged records for data/awards_archive.json (lightweight reader)
    sample_rows = db.query(HistoricalAwardModel).filter(
        HistoricalAwardModel.has_collusion_flag == True
    ).limit(250).all()

    archive_records = []
    for r in sample_rows:
        bidders = json.loads(r.bidders_json)
        archive_records.append({
            "id": r.tender_id,
            "tenderId": r.tender_id,
            "agency": r.agency,
            "division": r.division,
            "district": r.district,
            "year": r.year,
            "winner": r.winning_contractor,
            "leadContractor": r.winning_contractor,
            "estimatedCost": r.estimated_cost,
            "winningPrice": r.winning_price,
            "bidders": bidders,
            "collusionRisk": 0.94 if r.has_collusion_flag else 0.15,
            "collusionVector": r.collusion_vector,
            "syndicateName": r.syndicate_name,
            "riskCategory": "CARTEL_RING_IDENTIFIED" if r.has_collusion_flag else "CLEAN",
            "sharedGuarantee": bidders[0].get("bank_guarantee_no", "")
        })

    archive_path = os.path.join(ROOT_DIR, "data", "awards_archive.json")
    with open(archive_path, "w", encoding="utf-8") as f:
        json.dump(archive_records, f, indent=2)
    print(f"[+] Saved sample archive with {len(archive_records)} packages to {archive_path}")

    # Summary metadata file
    summary_path = os.path.join(ROOT_DIR, "data", "awards_archive_summary.json")
    summary = {
        "dataset_version": "50K-Historical-Collusion-Telemetry-v2.0",
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "total_tenders": total_count,
        "flagged_tenders": collusive_count,
        "clean_tenders": total_count - collusive_count,
        "collusion_rate_pct": round((collusive_count / total_count) * 100, 2) if total_count > 0 else 0,
        "year_range": [2021, 2026],
        "agencies_covered": AGENCIES,
        "divisions_covered": list(DIVISIONS_AND_DISTRICTS.keys()),
        "districts_count": 64,
        "syndicates_injected": len(CARTEL_SYNDICATES),
        "syndicate_names": [s["name"] for s in CARTEL_SYNDICATES]
    }
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"[+] Saved summary telemetry to {summary_path}")


if __name__ == "__main__":
    seed_50k_historical_awards(50200)
