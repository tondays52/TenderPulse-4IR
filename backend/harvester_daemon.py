"""
TenderPulse 4IR AI - Resilient Background Harvester & Ingestion Daemon
Production 24/7 procurement crawler with multi-agency scheduling, proxy routing,
token-bucket rate limiting, automated Corrigendum tracking, and SQLAlchemy DB persistence.
"""

import sys
import os
import time
import json
import random
import argparse
import threading
from datetime import datetime
from typing import Dict, Any, List, Optional
import requests

from backend.database import SessionLocal, init_db
from backend import crud
from backend.models import TenderModel, CorrigendumModel
from backend.executive_reporting import ensure_daily_executive_summary
from backend.egp_live_scraper import EgpLiveScraper

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT_DIR, "data")
STATUS_FILE = os.path.join(DATA_DIR, "harvester_status.json")
CORRIGENDUM_FILE = os.path.join(DATA_DIR, "corrigendum_alerts.json")


class HarvesterDaemon:
    """
    24/7 Autonomous background worker monitoring Bangladesh public procurement gazettes.
    Handles rate-limiting, proxies, database upserts, and Corrigendum delta detection.
    """

    SUPPORTED_AGENCIES = ["RHD", "LGED", "PWD", "BWDB", "BREB", "EED", "DGHS"]

    def __init__(
        self,
        agencies: Optional[List[str]] = None,
        interval: int = 300,
        proxy: Optional[str] = None,
        limit_per_agency: int = 5,
        min_delay: float = 1.5,
        max_delay: float = 3.5
    ):
        self.agencies = [a.upper() for a in (agencies or self.SUPPORTED_AGENCIES)]
        self.interval = max(10, interval)
        self.proxy = proxy or os.environ.get("HARVESTER_PROXY") or os.environ.get("HTTP_PROXY")
        self.limit_per_agency = limit_per_agency
        self.min_delay = min_delay
        self.max_delay = max_delay

        self.scraper = EgpLiveScraper()
        if self.proxy:
            self._apply_proxy(self.proxy)

        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        
        # Telemetry State
        self.state = {
            "status": "idle",
            "cycle_count": 0,
            "total_harvested_count": 0,
            "corrigendum_count": 0,
            "current_agency": None,
            "last_harvest_time": None,
            "next_scheduled_run": None,
            "last_error": None,
            "proxy_active": bool(self.proxy),
            "agencies": self.agencies,
            "recent_corrigenda": []
        }
        self._persist_status()

    def _apply_proxy(self, proxy_url: str):
        """Configures HTTP/HTTPS proxy on scraper session."""
        self.scraper.session.proxies.update({
            "http": proxy_url,
            "https": proxy_url
        })

    def _persist_status(self):
        """Thread-safely saves runtime status to data/harvester_status.json."""
        os.makedirs(DATA_DIR, exist_ok=True)
        try:
            with open(STATUS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.state, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def _record_corrigendum_alert(self, corrigendum_data: Dict[str, Any]):
        """Caches recent corrigendum alerts into data/corrigendum_alerts.json."""
        alerts = []
        if os.path.exists(CORRIGENDUM_FILE):
            try:
                with open(CORRIGENDUM_FILE, "r", encoding="utf-8") as f:
                    alerts = json.load(f)
            except Exception:
                alerts = []
        alerts.insert(0, corrigendum_data)
        alerts = alerts[:100]  # keep 100 most recent
        try:
            with open(CORRIGENDUM_FILE, "w", encoding="utf-8") as f:
                json.dump(alerts, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def run_harvest_cycle(self) -> Dict[str, Any]:
        """
        Executes a single harvest pass across all target procuring entities.
        Detects corrigenda against existing database entries and commits updates.
        """
        init_db()
        with self._lock:
            self.state["status"] = "harvesting"
            self.state["cycle_count"] += 1
            self.state["last_error"] = None
            self._persist_status()

        db = SessionLocal()
        cycle_harvested = 0
        cycle_corrigenda = 0
        cycle_errors = []

        try:
            for agency in self.agencies:
                if self._stop_event.is_set():
                    break

                with self._lock:
                    self.state["current_agency"] = agency
                    self._persist_status()

                # Rate limiting with randomized jitter
                delay = random.uniform(self.min_delay, self.max_delay)
                time.sleep(delay)

                try:
                    tenders = self.scraper.fetch_live_tenders(
                        keyword=agency,
                        page=1,
                        limit=self.limit_per_agency
                    )

                    for raw_item in tenders:
                        t_id = str(raw_item.get("tenderId") or raw_item.get("id"))
                        existing = db.query(TenderModel).filter(TenderModel.tender_id == t_id).first()

                        # --- Automated Corrigendum Detection ---
                        if existing:
                            new_close = str(raw_item.get("closingDate") or raw_item.get("closing_date") or "").strip()
                            old_close = str(existing.closing_date or "").strip()

                            if new_close and old_close and new_close != old_close:
                                corr = crud.create_corrigendum(
                                    db=db,
                                    tender_id=t_id,
                                    field_changed="closing_date",
                                    old_value=old_close,
                                    new_value=new_close,
                                    reason=f"CPTU Amendment Notice: Submission deadline rescheduled from {old_close} to {new_close}"
                                )
                                cycle_corrigenda += 1
                                alert_entry = {
                                    "tender_id": t_id,
                                    "field": "closing_date",
                                    "old": old_close,
                                    "new": new_close,
                                    "reason": corr.reason,
                                    "detected_at": datetime.utcnow().isoformat()
                                }
                                self._record_corrigendum_alert(alert_entry)
                                with self._lock:
                                    self.state["recent_corrigenda"].insert(0, alert_entry)
                                    self.state["recent_corrigenda"] = self.state["recent_corrigenda"][:20]

                            # Check tender security amendment
                            new_sec = float(raw_item.get("tenderSecurity") or raw_item.get("security") or 0.0)
                            old_sec = float(existing.tender_security or 0.0)
                            if new_sec > 0 and old_sec > 0 and abs(new_sec - old_sec) / old_sec > 0.05:
                                corr = crud.create_corrigendum(
                                    db=db,
                                    tender_id=t_id,
                                    field_changed="tender_security",
                                    old_value=str(old_sec),
                                    new_value=str(new_sec),
                                    reason=f"CPTU Corrigendum: Tender Security requirement adjusted from BDT {old_sec:,.0f} to BDT {new_sec:,.0f}"
                                )
                                cycle_corrigenda += 1

                        # Upsert tender to relational database
                        crud.upsert_tender(db, raw_item)
                        cycle_harvested += 1

                    # Also sync batch to file storage for fallback readers
                    self.scraper.sync_to_storage(tenders)

                except Exception as ex:
                    # A malformed notice must not leave the shared session in a
                    # failed transaction state for the next agency.
                    db.rollback()
                    cycle_errors.append(f"{agency}: {str(ex)}")

        finally:
            try:
                summary, created = ensure_daily_executive_summary(db)
                if created:
                    db.commit()
            except Exception as ex:
                db.rollback()
                cycle_errors.append(f"executive summary: {str(ex)}")
            db.close()

        now_str = datetime.utcnow().isoformat() + "Z"
        with self._lock:
            self.state["status"] = "idle"
            self.state["last_harvest_time"] = now_str
            self.state["total_harvested_count"] += cycle_harvested
            self.state["corrigendum_count"] += cycle_corrigenda
            self.state["current_agency"] = None
            if cycle_errors:
                self.state["last_error"] = "; ".join(cycle_errors)
            self._persist_status()

        return {
            "timestamp": now_str,
            "harvested": cycle_harvested,
            "corrigenda": cycle_corrigenda,
            "agencies_polled": len(self.agencies),
            "errors": cycle_errors
        }

    def start_daemon(self):
        """Starts 24/7 background worker loop."""
        print(f"[*] TenderPulse 4IR Harvester Daemon started. Monitoring {len(self.agencies)} agencies every {self.interval}s.")
        if self.proxy:
            print(f"[*] Active egress proxy routing: {self.proxy}")

        while not self._stop_event.is_set():
            start_time = time.time()
            try:
                print(f"\n[+] Executing scheduled procurement harvest cycle (Cycle #{self.state['cycle_count'] + 1})...")
                res = self.run_harvest_cycle()
                print(f"[✓] Harvest complete: {res['harvested']} notices ingested, {res['corrigenda']} corrigenda flagged.")
            except Exception as ex:
                print(f"[!] Critical error in harvest cycle: {ex}")
                with self._lock:
                    self.state["status"] = "error"
                    self.state["last_error"] = str(ex)
                    self._persist_status()

            elapsed = time.time() - start_time
            sleep_sec = max(5, self.interval - elapsed)
            
            with self._lock:
                self.state["status"] = "sleeping"
                self.state["next_scheduled_run"] = datetime.utcfromtimestamp(time.time() + sleep_sec).isoformat() + "Z"
                self._persist_status()

            # Responsive wait loop allowing clean shutdown
            wait_steps = int(sleep_sec)
            for _ in range(wait_steps):
                if self._stop_event.is_set():
                    break
                time.sleep(1.0)

        with self._lock:
            self.state["status"] = "stopped"
            self._persist_status()
        print("[*] Harvester Daemon gracefully terminated.")

    def stop(self):
        """Signals background daemon to gracefully shut down."""
        self._stop_event.set()

    def get_status(self) -> Dict[str, Any]:
        """Returns current daemon operational status."""
        with self._lock:
            return dict(self.state)


# Singleton instance for server-side in-process triggers
_daemon_instance: Optional[HarvesterDaemon] = None


def get_daemon_instance() -> HarvesterDaemon:
    global _daemon_instance
    if _daemon_instance is None:
        _daemon_instance = HarvesterDaemon()
    return _daemon_instance


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TenderPulse 4IR Harvester Daemon")
    parser.add_argument("--once", action="store_true", help="Run a single procurement harvest cycle and exit")
    parser.add_argument("--daemon", action="store_true", help="Run continuously as a 24/7 background worker")
    parser.add_argument("--interval", type=int, default=300, help="Interval in seconds between harvest cycles (default: 300)")
    parser.add_argument("--agency", type=str, default=None, help="Target single agency (e.g. LGED, RHD, PWD)")
    parser.add_argument("--limit", type=int, default=5, help="Number of notices to fetch per agency (default: 5)")
    parser.add_argument("--proxy", type=str, default=None, help="Optional HTTP/HTTPS/SOCKS5 proxy URI")

    args = parser.parse_args()

    target_agencies = [args.agency.upper()] if args.agency else None
    daemon = HarvesterDaemon(
        agencies=target_agencies,
        interval=args.interval,
        proxy=args.proxy,
        limit_per_agency=args.limit
    )

    if args.once or not args.daemon:
        print("[*] Executing one-off procurement harvest pass...")
        result = daemon.run_harvest_cycle()
        print(f"[+] Harvest cycle completed successfully:\n{json.dumps(result, indent=2)}")
        sys.exit(0)
    else:
        try:
            daemon.start_daemon()
        except KeyboardInterrupt:
            daemon.stop()
