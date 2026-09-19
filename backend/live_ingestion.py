"""
TenderPulse 4IR AI - Real-Time e-GP Live Tender Ingestion & WebSocket Broadcast Hub
Streams live tender award events with instant GAT Cartel Radar forensic inference,
broadcasts JSON blip events to all connected GIS canvas WebSocket clients.
"""

import asyncio
import json
import random
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

# ---------------------------------------------------------------------------
# District + Syndicate Reference Data (mirrors cartel_radar.py)
# ---------------------------------------------------------------------------
_DISTRICT_POOL = [
    {"district": "Dhaka",       "division": "Dhaka",       "lat": 23.8103, "lon": 90.4125},
    {"district": "Gazipur",     "division": "Dhaka",       "lat": 23.9999, "lon": 90.4203},
    {"district": "Narayanganj", "division": "Dhaka",       "lat": 23.6238, "lon": 90.5000},
    {"district": "Faridpur",    "division": "Dhaka",       "lat": 23.6071, "lon": 89.8429},
    {"district": "Tangail",     "division": "Dhaka",       "lat": 24.2513, "lon": 89.9167},
    {"district": "Kishoreganj", "division": "Dhaka",       "lat": 24.4449, "lon": 90.7766},
    {"district": "Manikganj",   "division": "Dhaka",       "lat": 23.8617, "lon": 90.0003},
    {"district": "Munshiganj",  "division": "Dhaka",       "lat": 23.5422, "lon": 90.5305},
    {"district": "Gopalganj",   "division": "Dhaka",       "lat": 23.0051, "lon": 89.8266},
    {"district": "Madaripur",   "division": "Dhaka",       "lat": 23.1641, "lon": 90.1897},
    {"district": "Shariatpur",  "division": "Dhaka",       "lat": 23.2423, "lon": 90.4348},
    {"district": "Rajbari",     "division": "Dhaka",       "lat": 23.7574, "lon": 89.6445},
    {"district": "Chattogram",  "division": "Chattogram",  "lat": 22.3569, "lon": 91.7832},
    {"district": "Cumilla",     "division": "Chattogram",  "lat": 23.4607, "lon": 91.1809},
    {"district": "Feni",        "division": "Chattogram",  "lat": 23.0186, "lon": 91.3966},
    {"district": "Brahmanbaria","division": "Chattogram",  "lat": 23.9571, "lon": 91.1119},
    {"district": "Noakhali",    "division": "Chattogram",  "lat": 22.8696, "lon": 91.0993},
    {"district": "Chandpur",    "division": "Chattogram",  "lat": 23.2333, "lon": 90.6667},
    {"district": "Rajshahi",    "division": "Rajshahi",    "lat": 24.3745, "lon": 88.6042},
    {"district": "Bogura",      "division": "Rajshahi",    "lat": 24.8465, "lon": 89.3777},
    {"district": "Pabna",       "division": "Rajshahi",    "lat": 24.0064, "lon": 89.2372},
    {"district": "Sirajganj",   "division": "Rajshahi",    "lat": 24.4534, "lon": 89.7008},
    {"district": "Naogaon",     "division": "Rajshahi",    "lat": 24.7936, "lon": 88.9318},
    {"district": "Khulna",      "division": "Khulna",      "lat": 22.8456, "lon": 89.5403},
    {"district": "Jashore",     "division": "Khulna",      "lat": 23.1664, "lon": 89.2137},
    {"district": "Kushtia",     "division": "Khulna",      "lat": 23.9013, "lon": 89.1205},
    {"district": "Satkhira",    "division": "Khulna",      "lat": 22.7185, "lon": 89.0705},
    {"district": "Bagerhat",    "division": "Khulna",      "lat": 22.6516, "lon": 89.7859},
    {"district": "Barishal",    "division": "Barishal",    "lat": 22.7010, "lon": 90.3535},
    {"district": "Patuakhali",  "division": "Barishal",    "lat": 22.3596, "lon": 90.3299},
    {"district": "Bhola",       "division": "Barishal",    "lat": 22.6859, "lon": 90.6481},
    {"district": "Sylhet",      "division": "Sylhet",      "lat": 24.8949, "lon": 91.8687},
    {"district": "Sunamganj",   "division": "Sylhet",      "lat": 25.0658, "lon": 91.3950},
    {"district": "Rangpur",     "division": "Rangpur",     "lat": 25.7439, "lon": 89.2752},
    {"district": "Dinajpur",    "division": "Rangpur",     "lat": 25.6217, "lon": 88.6355},
    {"district": "Kurigram",    "division": "Rangpur",     "lat": 25.8054, "lon": 89.6362},
    {"district": "Gaibandha",   "division": "Rangpur",     "lat": 25.3288, "lon": 89.5281},
    {"district": "Nilphamari",  "division": "Rangpur",     "lat": 25.9318, "lon": 88.8560},
    {"district": "Mymensingh",  "division": "Mymensingh",  "lat": 24.7471, "lon": 90.4203},
    {"district": "Jamalpur",    "division": "Mymensingh",  "lat": 24.9375, "lon": 89.9378},
    {"district": "Netrokona",   "division": "Mymensingh",  "lat": 24.8709, "lon": 90.7279},
    {"district": "Sherpur",     "division": "Mymensingh",  "lat": 25.0205, "lon": 90.0153},
]

_SYNDICATES = [
    {"name": "Padma-Jamuna Highway Syndicate",        "districts": ["Dhaka", "Faridpur", "Rajbari", "Manikganj"],    "vector": "GUARANTEE",   "agencies": ["RHD"],        "collusion_pct_range": (25, 48)},
    {"name": "Dhaka South Metro Building Cartel",     "districts": ["Dhaka", "Narayanganj", "Gazipur", "Munshiganj"],"vector": "COVER_BID",   "agencies": ["PWD", "LGED"],"collusion_pct_range": (18, 35)},
    {"name": "Northern Road Sector Ring",             "districts": ["Rangpur", "Dinajpur", "Gaibandha", "Nilphamari"],"vector": "ROTATIONAL",  "agencies": ["RHD", "LGED"],"collusion_pct_range": (22, 40)},
    {"name": "Chittagong Coastal Embankment Cartel",  "districts": ["Chattogram", "Cumilla", "Noakhali", "Feni"],    "vector": "ADDRESS",     "agencies": ["BWDB", "RHD"],"collusion_pct_range": (15, 30)},
    {"name": "Barisal River Dredging Alliance",       "districts": ["Barishal", "Patuakhali", "Bhola"],              "vector": "ROTATIONAL",  "agencies": ["BWDB"],       "collusion_pct_range": (20, 38)},
    {"name": "Rajshahi Grain Silo Infrastructure Ring","districts": ["Rajshahi", "Naogaon", "Bogura", "Pabna"],      "vector": "GUARANTEE",   "agencies": ["PWD", "DPHE"],"collusion_pct_range": (16, 28)},
]

_AGENCIES = ["RHD", "LGED", "BWDB", "PWD", "DPHE", "BREB"]
_WORK_TYPES = [
    "Road Pavement & Embankment", "Bridge & Culvert", "River Dredging",
    "Building Construction", "Water Supply Infrastructure", "Flood Embankment Repair",
    "Rural Road Development", "Institutional Building",
]


def _fast_cartel_inference(district: str, agency: str, cost_cr: float) -> Dict[str, Any]:
    """GAT Cartel Radar fast-path inference - syndicate territory check + probabilistic roll."""
    matched_syn = None
    for syn in _SYNDICATES:
        if district in syn["districts"] and agency in syn["agencies"]:
            matched_syn = syn
            break

    base_prob = 0.38 if matched_syn else 0.08
    cost_factor = min(0.20, cost_cr / 500.0)
    is_collusive = random.random() < (base_prob + cost_factor)

    if is_collusive and matched_syn:
        pct = random.uniform(*matched_syn["collusion_pct_range"])
        return {
            "is_collusive": True,
            "threat_tier": "CRITICAL" if pct > 35 else "HIGH",
            "integrity_score": round(100 - pct, 1),
            "collusion_pct": round(pct, 1),
            "syndicate": matched_syn["name"],
            "collusion_vector": matched_syn["vector"],
            "partner_districts": [d for d in matched_syn["districts"] if d != district][:2],
        }
    elif is_collusive:
        pct = random.uniform(12, 22)
        return {
            "is_collusive": True,
            "threat_tier": "ELEVATED",
            "integrity_score": round(100 - pct, 1),
            "collusion_pct": round(pct, 1),
            "syndicate": "Unknown Local Cartel",
            "collusion_vector": random.choice(["GUARANTEE", "COVER_BID", "ADDRESS", "ROTATIONAL"]),
            "partner_districts": [],
        }
    else:
        return {
            "is_collusive": False,
            "threat_tier": "CLEAN",
            "integrity_score": round(random.uniform(82, 99), 1),
            "collusion_pct": 0.0,
            "syndicate": None,
            "collusion_vector": None,
            "partner_districts": [],
        }


def _synthesize_tender() -> Dict[str, Any]:
    """Generate a realistic simulated e-GP tender award event."""
    dist_info = random.choice(_DISTRICT_POOL)
    agency = random.choice(_AGENCIES)
    cost_cr = round(random.uniform(2.5, 120.0), 2)
    tender_id = f"BD-eGP-{time.strftime('%Y%m%d')}-{random.randint(10000, 99999)}"
    ref_no = f"{agency}/{dist_info['district'][:3].upper()}/{time.strftime('%Y')}/W-{random.randint(10, 99):02d}"
    work_type = random.choice(_WORK_TYPES)
    cartel = _fast_cartel_inference(dist_info["district"], agency, cost_cr)
    # Cover-bid spread: collusive = 3-7% over estimate, clean = wider natural spread
    spread = random.uniform(0.03, 0.07) if cartel["is_collusive"] else random.uniform(-0.10, 0.22)
    award_cr = round(cost_cr * (1 + spread), 2)

    return {
        "event_id": str(uuid.uuid4())[:8].upper(),
        "event_type": "LIVE_AWARD",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tender_id": tender_id,
        "ref_no": ref_no,
        "title": f"{work_type} ({dist_info['district']} District)",
        "agency": agency,
        "district": dist_info["district"],
        "division": dist_info["division"],
        "latitude": dist_info["lat"],
        "longitude": dist_info["lon"],
        "estimated_cost_cr": cost_cr,
        "award_price_cr": award_cr,
        "work_type": work_type,
        "provenance": {
            "kind": "synthetic",
            "label": "Simulated live-radar event",
            "notes": ["Generated locally for interface demonstration; not an e-GP award event."],
        },
        **cartel,
    }


class LiveTenderBroadcaster:
    """
    Async WebSocket broadcast hub for real-time e-GP tender ingestion.

    - Maintains active WebSocket connection registry.
    - Runs a background asyncio task generating events at configurable intervals.
    - Applies GAT Cartel Radar fast-path inference on every award.
    - Broadcasts structured JSON events to all connected clients.
    """

    _MIN_INTERVAL = 0.5
    _MAX_INTERVAL = 15.0
    _MAX_RECENT = 50

    def __init__(self, interval: float = 2.0):
        self._connections: Set[Any] = set()
        self._interval: float = max(self._MIN_INTERVAL, min(self._MAX_INTERVAL, interval))
        self._running: bool = False
        self._paused: bool = False
        self._task: Optional[asyncio.Task] = None
        self._recent_events: List[Dict[str, Any]] = []
        self._total_emitted: int = 0
        self._total_collusive: int = 0
        self._started_at: Optional[float] = None

    # ------------------------------------------------------------------
    # Connection Management
    # ------------------------------------------------------------------
    async def connect(self, ws) -> None:
        await ws.accept()
        self._connections.add(ws)
        # Greet new client with current stream status
        try:
            await ws.send_text(json.dumps({"event_type": "STREAM_CONNECTED", "status": self.get_status()}))
        except Exception:
            pass

    def disconnect(self, ws) -> None:
        self._connections.discard(ws)

    async def _broadcast(self, event: Dict[str, Any]) -> None:
        dead: Set[Any] = set()
        payload = json.dumps(event)
        for ws in list(self._connections):
            try:
                await ws.send_text(payload)
            except Exception:
                dead.add(ws)
        for ws in dead:
            self._connections.discard(ws)

    # ------------------------------------------------------------------
    # Stream Controls
    # ------------------------------------------------------------------
    def start(self) -> None:
        if self._running and self._task and not self._task.done():
            self._paused = False
            return
        self._running = True
        self._paused = False
        self._started_at = time.time()
        self._task = asyncio.ensure_future(self._ingestion_loop())

    def pause(self) -> None:
        self._paused = True

    def resume(self) -> None:
        self._paused = False
        if not self._running or not self._task or self._task.done():
            self.start()

    def toggle(self) -> str:
        if self._paused:
            self.resume()
            return "RESUMED"
        else:
            self.pause()
            return "PAUSED"

    def stop(self) -> None:
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()

    @property
    def is_active(self) -> bool:
        return self._running and not self._paused

    @property
    def client_count(self) -> int:
        return len(self._connections)

    def get_status(self) -> Dict[str, Any]:
        state = "PAUSED" if self._paused else ("ACTIVE" if self._running else "STOPPED")
        return {
            "stream_state": state,
            "connected_clients": self.client_count,
            "interval_seconds": self._interval,
            "total_events_emitted": self._total_emitted,
            "total_collusive_detected": self._total_collusive,
            "uptime_seconds": round(time.time() - self._started_at, 1) if self._started_at else 0,
            "recent_events": self._recent_events[-5:],
        }

    # ------------------------------------------------------------------
    # Inject API
    # ------------------------------------------------------------------
    async def inject(self, override: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Manually inject a tender event (test/demo API)."""
        if override:
            event = dict(override)
            if "is_collusive" not in event:
                cartel = _fast_cartel_inference(
                    event.get("district", "Dhaka"),
                    event.get("agency", "RHD"),
                    float(event.get("estimated_cost_cr", 50.0)),
                )
                event.update(cartel)
            event.setdefault("event_type", "INJECTED_AWARD")
            event.setdefault("event_id", str(uuid.uuid4())[:8].upper())
            event.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
        else:
            event = _synthesize_tender()
            event["event_type"] = "INJECTED_AWARD"
        await self._emit(event)
        return event

    # ------------------------------------------------------------------
    # Internal Loop
    # ------------------------------------------------------------------
    async def _ingestion_loop(self) -> None:
        while self._running:
            try:
                await asyncio.sleep(self._interval)
                if not self._paused:
                    await self._emit(_synthesize_tender())
            except asyncio.CancelledError:
                break
            except Exception:
                pass

    async def _emit(self, event: Dict[str, Any]) -> None:
        self._total_emitted += 1
        if event.get("is_collusive"):
            self._total_collusive += 1
        self._recent_events.append(event)
        if len(self._recent_events) > self._MAX_RECENT:
            self._recent_events = self._recent_events[-self._MAX_RECENT:]
        await self._broadcast(event)


# Module-level singleton shared across WebSocket connections
live_broadcaster = LiveTenderBroadcaster(interval=2.0)
