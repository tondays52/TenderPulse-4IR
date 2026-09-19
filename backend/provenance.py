"""Provenance labels for data shown by TenderPulse.

Every response should state whether it came from a verified external source,
local cache, a derived transformation, or a simulation.  This module keeps
that contract consistent while legacy records are gradually backfilled.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from typing import Any, Dict, Iterable


VALID_KINDS = {"live", "cached", "synthetic", "derived", "legacy_unknown"}


def tender_provenance(item: Dict[str, Any], *, transport: str = "database") -> Dict[str, Any]:
    existing = item.get("provenance") if isinstance(item.get("provenance"), dict) else {}
    kind = existing.get("kind") or item.get("source_kind") or "legacy_unknown"
    if kind not in VALID_KINDS:
        kind = "legacy_unknown"
    return {
        "kind": kind,
        "label": existing.get("label") or item.get("source") or "Unclassified legacy record",
        "transport": transport,
        "retrieved_at": existing.get("retrieved_at") or item.get("retrieved_at"),
        "source_url": existing.get("source_url") or item.get("officialUrl"),
        "notes": existing.get("notes") or ([] if kind != "legacy_unknown" else ["Source provenance was not recorded when this record was created."]),
    }


def annotate_tender(item: Dict[str, Any], *, transport: str = "database") -> Dict[str, Any]:
    annotated = dict(item)
    annotated["provenance"] = tender_provenance(annotated, transport=transport)
    return annotated


def provenance_summary(items: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    counts = Counter(item.get("provenance", {}).get("kind", "legacy_unknown") for item in items)
    return {
        "counts": dict(counts),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "policy": "Live, cached, derived, synthetic, and legacy-unknown records are labeled explicitly.",
    }
