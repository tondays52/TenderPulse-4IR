"""
Script to trigger live mining against e-GP portal via running backend.
"""
import sys
import requests
import json
import time

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_URL = "http://127.0.0.1:8080"

def mine_agency(agency_name: str, limit: int = 5):
    print(f"\n{'='*70}")
    print(f"[*] Triggering Live e-GP Mining for Agency: {agency_name}")
    print(f"{'='*70}")
    
    t0 = time.time()
    url = f"{BASE_URL}/api/scraper/live-mine"
    payload = {"agency": agency_name, "limit": limit, "page": 1}
    
    try:
        resp = requests.post(url, json=payload, timeout=25)
        elapsed = time.time() - t0
        print(f"HTTP Status: {resp.status_code} ({elapsed:.2f}s)")
        
        if resp.status_code == 200:
            data = resp.json()
            retrieved = data.get("retrieved_count", 0)
            synced = data.get("newly_synced", 0)
            print(f"[✓] Retrieved: {retrieved} notices | Newly Synced: {synced}")
            
            tenders = data.get("tenders", [])
            for idx, t in enumerate(tenders[:4], 1):
                tid = t.get("id") or t.get("tenderId")
                title = t.get("title", "No title")
                cost = t.get("cost", 0)
                closing = t.get("closingDate", "N/A")
                agency = t.get("agency", agency_name)
                print(f"  {idx}. [{agency}] ID #{tid} | Cost: ৳{cost} BDT")
                print(f"     Title: {title[:75]}...")
                print(f"     Closing Date: {closing}")
        else:
            print(f"[!] Error: {resp.text}")
    except Exception as e:
        print(f"[!] Request Exception: {e}")

if __name__ == "__main__":
    mine_agency("LGED", 5)
    mine_agency("RHD", 5)
    mine_agency("BWDB", 3)
    
    # Query updated live feed
    print(f"\n{'='*70}")
    print("[*] Verifying Persistent Database Total Live Tenders Count")
    print(f"{'='*70}")
    live_resp = requests.get(f"{BASE_URL}/api/tenders/live?limit=5")
    if live_resp.status_code == 200:
        ld = live_resp.json()
        print(f"[✓] Total live tenders now in database: {ld.get('total_count', len(ld.get('tenders', [])))}")
