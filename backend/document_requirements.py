"""Conservative, source-backed tender requirement extraction."""
import re
from typing import Dict, List


def extract_explicit_requirements(text: str, page_texts=None) -> List[Dict[str, str]]:
    patterns = [
        ("submission_deadline", r"(?:submission|closing)\s*(?:date|deadline)?\s*[:\-]?\s*([^\n]{4,100})"),
        ("tender_security", r"(?:tender|bid)\s+security\s*[:\-]?\s*([^\n]{3,120})"),
        ("annual_turnover", r"(?:annual|average annual)\s+turnover\s*[:\-]?\s*([^\n]{3,120})"),
        ("liquid_assets", r"liquid\s+assets?\s*[:\-]?\s*([^\n]{3,120})"),
        ("bid_validity", r"bid\s+validity\s*[:\-]?\s*([^\n]{3,120})"),
    ]
    requirements = []
    for key, pattern in patterns:
        match = re.search(pattern, text or "", re.IGNORECASE)
        if match:
            excerpt = match.group(0).strip()
            page = next((item["page"] for item in (page_texts or []) if excerpt in item.get("text", "")), None)
            requirements.append({"key": key, "source_excerpt": excerpt[:300], "source_page": page, "review_status": "unreviewed"})
    return requirements
