# Copyright (c) 2026 Sanjaydeep Gowrishankar. Licensed under the MIT License.

"""Dubai Rental Dispute Settlement Centre (RDSC) Legal Risk & Eviction Forecaster.

Evaluates tenancy disputes, eviction notices, and compensation liabilities pursuant to
Dubai Law No. 26 of 2007 as amended by Dubai Law No. 33 of 2008 (Articles 25 & 26).
"""

import datetime as dt
from typing import Any, Dict, List, Optional


VALID_EVICTION_GROUNDS = {
    "sale": {
        "title": "Sale of Property",
        "citation": "Law No. 33 of 2008, Art. 25(2)(d)",
        "notice_months": 12,
        "requires_proof": True,
        "proof_document": "Proof of active marketing or sale agreement"
    },
    "personal_use": {
        "title": "Owner or First-Degree Relative Personal Use",
        "citation": "Law No. 33 of 2008, Art. 25(2)(c)",
        "notice_months": 12,
        "requires_proof": True,
        "proof_document": "Proof of non-ownership of alternative suitable property in Dubai",
        "re_lease_ban_years": 2
    },
    "demolition": {
        "title": "Demolition or Urban Reconstruction",
        "citation": "Law No. 33 of 2008, Art. 25(2)(a)",
        "notice_months": 12,
        "requires_proof": True,
        "proof_document": "Official technical demolition license from Dubai Municipality"
    },
    "comprehensive_renovation": {
        "title": "Comprehensive Renovation / Maintenance",
        "citation": "Law No. 33 of 2008, Art. 25(2)(b)",
        "notice_months": 12,
        "requires_proof": True,
        "proof_document": "Dubai Municipality technical report proving tenant cannot remain in occupancy"
    }
}


def forecast_eviction_case(
    ground: str,
    notice_date: str,
    target_eviction_date: str,
    notice_method: str,
    landlord_owns_alternatives: bool = False,
    has_official_permits: bool = True,
    current_annual_rent: float = 100000.0
) -> Dict[str, Any]:
    """Evaluates whether an eviction claim will hold at the Dubai RDSC tribunal."""
    findings = []
    risks = []
    is_valid = True
    ground_info = VALID_EVICTION_GROUNDS.get(ground.lower())

    if not ground_info:
        return {
            "viable": False,
            "success_probability_percent": 0,
            "verdict": "Invalid Eviction Ground",
            "findings": [f"Ground '{ground}' is not recognized under Dubai Law No. 33 of 2008."],
            "risks": ["Immediate dismissal by RDSC judicial committee."]
        }

    # 1. Verification of Notice Period (12 Months Statutory Requirement)
    try:
        n_date = dt.date.fromisoformat(notice_date)
        e_date = dt.date.fromisoformat(target_eviction_date)
        days_notice = (e_date - n_date).days
        months_notice = round(days_notice / 30.416, 1)
    except (ValueError, TypeError):
        return {"error": "Invalid date format. Use YYYY-MM-DD."}

    if days_notice < 365:
        is_valid = False
        shortfall = 365 - days_notice
        findings.append(
            f"Insufficient notice period: {days_notice} days provided (~{months_notice} months). "
            f"Statute strictly mandates at least 365 days (12 full months). Shortfall: {shortfall} days."
        )
        risks.append("RDSC judges will dismiss the case; notice period must restart from scratch.")
    else:
        findings.append(f"Statutory 12-month notice duration satisfied ({days_notice} days provided).")

    # 2. Service Channel Validation (Notary Public or Registered Mail Only)
    clean_method = notice_method.lower().strip()
    if clean_method not in ("notary_public", "notary", "registered_mail"):
        is_valid = False
        findings.append(
            f"Notice served via '{notice_method}'. Article 25 explicitly requires service via "
            "Notary Public (كاتب العدل) or Registered Mail with acknowledgment receipt."
        )
        risks.append("Emails, WhatsApp, and verbal notices are routinely dismissed by RDSC.")
    else:
        findings.append(f"Service via '{clean_method.replace('_', ' ').title()}' is legally compliant.")

    # 3. Ground-Specific Evidentiary Proof
    if ground == "personal_use":
        if landlord_owns_alternatives:
            is_valid = False
            findings.append(
                "Landlord owns alternative suitable residential properties in Dubai. Under Article 25(2)(c), "
                "personal use is barred if the owner possesses an alternative suitable property."
            )
            risks.append("High probability of tenant prevailing on bad-faith grounds.")
        findings.append(
            "Article 26 Penalty Warning: If evicted, landlord cannot re-lease the property for 2 years. "
            "Violation entitles tenant to seek damages up to 1 full year's rent."
        )

    if ground in ("demolition", "comprehensive_renovation") and not has_official_permits:
        is_valid = False
        findings.append(
            "Lack of official Dubai Municipality structural permits. RDSC requires certified technical "
            "reports proving that works cannot be conducted with tenant in residence."
        )
        risks.append("RDSC will reject eviction without Dubai Municipality engineering certification.")

    # Calculate Probability Score
    if not is_valid:
        prob = 15 if (days_notice >= 365 and clean_method in ("notary_public", "registered_mail")) else 5
        verdict = "High Risk of Dismissal at RDSC"
    else:
        prob = 92
        verdict = "Statutorily Compliant Eviction Case"

    max_penalty_liability = round(current_annual_rent) if ground == "personal_use" else 0.0

    return {
        "viable": is_valid,
        "success_probability_percent": prob,
        "verdict": verdict,
        "ground": ground_info["title"],
        "citation": ground_info["citation"],
        "days_notice_given": days_notice,
        "months_notice_given": months_notice,
        "service_channel": clean_method,
        "findings": findings,
        "risks": risks,
        "potential_tenant_compensation_liability": max_penalty_liability,
        "tribunal": "Dubai Rental Dispute Settlement Centre (RDSC - مركز فض المنازعات الإيجارية)",
        "disclaimer": "Informational assessment based on Dubai tenancy laws; not formal judicial representation."
    }
