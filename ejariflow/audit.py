# Copyright (c) 2026 Sanjaydeep Gowrishankar. Licensed under the MIT License.

"""Audits a parsed tenancy contract against Dubai rent rules.

Each finding names the clause, what is wrong, and the rule it breaks. Clause checks are pattern-based
in this first version: they read common wordings ("increase by 10%", "vacate ... with 60 days notice",
"notified 30 days before expiry"), so unusual wordings are listed as unchecked rather than passed.
"""

import re
from typing import Any, Dict, List, Optional

from . import rera

INCREASE = re.compile(r"(?:rent|amount).{0,40}?increase[sd]?\s+(?:by\s+)?(\d{1,3}(?:\.\d+)?)\s*%|(\d{1,3}(?:\.\d+)?)\s*%\s+(?:annual\s+|yearly\s+)?(?:rent\s+)?increase", re.IGNORECASE)
NOTICE = re.compile(r"(\d{1,3})\s*(days?|months?)['’]?\s*(?:prior\s+|advance\s+|written\s+)*notice|notified\s+(\d{1,3})\s*(days?|months?)", re.IGNORECASE)
EVICTION_WORDS = {
    "own_use": re.compile(r"own\s+use|personal\s+use|for\s+(?:his|her|their)\s+(?:own\s+)?(?:family|use)", re.IGNORECASE),
    "sale": re.compile(r"\bsell|\bsale\b", re.IGNORECASE),
    "demolition": re.compile(r"demoli", re.IGNORECASE),
    "renovation": re.compile(r"renovat", re.IGNORECASE),
}


def _notice_days(clause: str) -> Optional[int]:
    m = NOTICE.search(clause)
    if not m:
        return None
    n = int(m.group(1) or m.group(3))
    unit = (m.group(2) or m.group(4)).lower()
    return n * 30 if unit.startswith("month") else n


def audit_contract(contract: Dict[str, Any], average_rent: Optional[float] = None) -> Dict[str, Any]:
    findings: List[Dict[str, Any]] = []
    unchecked: List[str] = []
    rent = contract.get("annual_rent")
    cap = rera.allowed_increase(rent, average_rent) if rent and average_rent else None

    for n, clause in enumerate(contract.get("special_conditions") or [], 1):
        handled = False
        inc = INCREASE.search(clause)
        if inc:
            handled = True
            pct = float(inc.group(1) or inc.group(2))
            if cap is None:
                unchecked.append(f"Clause {n}: a {pct:g}% increase, but no average rent was given to check it against.")
            elif pct > cap["max_percent"]:
                findings.append({"code": "ESCALATION_OVER_CAP", "severity": "high", "clause": n, "text": clause,
                                 "message": f"Allows a {pct:g}% increase, but this unit's cap is {cap['max_percent']}% "
                                            f"(rent is {cap['gap_percent']:g}% below the average).", "rule": rera.DECREE})
        days = _notice_days(clause)
        if days is not None and re.search(r"vacate|evict|terminat|leave the (?:unit|property)", clause, re.IGNORECASE):
            handled = True
            reason = next((r for r, rx in EVICTION_WORDS.items() if rx.search(clause)), None)
            if reason and days < rera.EVICTION_NOTICE_MONTHS * 30:
                findings.append({"code": "EVICTION_NOTICE_TOO_SHORT", "severity": "high", "clause": n, "text": clause,
                                 "message": f"Gives {days} days' notice to vacate because {rera.EVICTION_REASONS[reason]}; "
                                            "the law requires 12 months, served through a notary public or registered mail.",
                                 "rule": rera.TENANCY_LAW})
        elif days is not None and re.search(r"renew|change|amend|terms|expir", clause, re.IGNORECASE):
            handled = True
            if days < rera.RENEWAL_NOTICE_DAYS:
                findings.append({"code": "RENEWAL_NOTICE_TOO_SHORT", "severity": "medium", "clause": n, "text": clause,
                                 "message": f"Changes to renewal terms on {days} days' notice; at least {rera.RENEWAL_NOTICE_DAYS} days are required.",
                                 "rule": rera.TENANCY_LAW})
        if not handled:
            unchecked.append(f"Clause {n}: not checked automatically.")

    for field in contract.get("missing") or []:
        findings.append({"code": "MISSING_FIELD", "severity": "low", "clause": None, "text": "",
                         "message": f"{field.replace('_', ' ').capitalize()} wasn't found in the document.", "rule": "Ejari registration"})

    high = sum(1 for f in findings if f["severity"] == "high")
    return {"compliant": not any(f["severity"] in ("high", "medium") for f in findings),
            "high": high, "findings": findings, "unchecked": unchecked, "rent_cap": cap,
            "disclaimer": "Automated check, not legal advice. The Rental Disputes Centre decides disputes."}
