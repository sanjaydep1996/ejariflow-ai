# Copyright (c) 2026 Sanjaydeep Gowrishankar. Licensed under the MIT License.

"""Dubai rent rules: RERA rent increase caps and the notice periods around a tenancy.

Rent increase caps come from Dubai Decree No. 43 of 2013. How much a landlord may raise the rent on
renewal depends on how far the current rent is *below* the average rent for similar units (the
figure published in the RERA / DLD rental index):

    up to 10% below the average     -> no increase
    11% to 20% below                -> up to 5%
    21% to 30% below                -> up to 10%
    31% to 40% below                -> up to 15%
    more than 40% below             -> up to 20%

Notice periods come from Dubai Law No. 26 of 2007 as amended by Law No. 33 of 2008:
    - changing the terms of a renewal (including rent): at least 90 days before the contract ends;
    - eviction at the end of the contract for sale, own use (or a first-degree relative), demolition or
      major renovation: 12 months' notice, served through a notary public or registered mail.

The average rent itself has to come from the official RERA rental index calculator for the specific
unit: this module doesn't guess it. This is a software check to point at likely problems; it is not
legal advice, and the Rental Disputes Centre has the final word.
"""

import datetime as dt
from typing import Any, Dict

DECREE = "Dubai Decree No. 43 of 2013"
TENANCY_LAW = "Dubai Law No. 26 of 2007, as amended by Law No. 33 of 2008"
RENEWAL_NOTICE_DAYS = 90
EVICTION_NOTICE_MONTHS = 12
EVICTION_REASONS = {
    "sale": "the landlord wants to sell the property",
    "own_use": "the landlord (or a first-degree relative) wants to live in it",
    "demolition": "the property is being demolished and rebuilt",
    "renovation": "the property needs major renovation or maintenance that can't be done with the tenant in it",
}
# (gap below average in %, upper bound inclusive) -> max increase %
BANDS = [(10, 0), (20, 5), (30, 10), (40, 15)]
TOP_BAND = 20


def allowed_increase(current_rent: float, average_rent: float) -> Dict[str, Any]:
    """The maximum rent increase on renewal for a unit renting at `current_rent`."""
    if current_rent <= 0 or average_rent <= 0:
        raise ValueError("Current rent and average rent must both be more than zero.")
    gap = (average_rent - current_rent) / average_rent * 100
    gap_rounded = round(gap, 2)
    max_percent = TOP_BAND
    for upper, pct in BANDS:
        if gap_rounded <= upper:
            max_percent = pct
            break
    return {"current_rent": current_rent, "average_rent": average_rent, "gap_percent": gap_rounded,
            "max_percent": max_percent, "max_rent": round(current_rent * (1 + max_percent / 100)), "rule": DECREE}


def check_increase(current_rent: float, proposed_rent: float, average_rent: float) -> Dict[str, Any]:
    """Is `proposed_rent` within the RERA cap for this unit?"""
    cap = allowed_increase(current_rent, average_rent)
    proposed_pct = round((proposed_rent - current_rent) / current_rent * 100, 2)
    compliant = proposed_rent <= cap["max_rent"]
    if compliant:
        reason = (f"An increase of {proposed_pct:g}% is within the {cap['max_percent']}% allowed."
                  if proposed_rent > current_rent else "No increase.")
    elif cap["max_percent"] == 0:
        reason = (f"The rent is only {max(cap['gap_percent'], 0):g}% below the average for similar units, "
                  "so no increase is allowed.")
    else:
        reason = (f"The rent is {cap['gap_percent']:g}% below the average, so the cap is {cap['max_percent']}% "
                  f"(AED {cap['max_rent']:,}). The proposal is {proposed_pct:g}%.")
    return {**cap, "proposed_rent": proposed_rent, "proposed_percent": proposed_pct, "compliant": compliant,
            "excess": max(0, round(proposed_rent - cap["max_rent"])), "reason": reason}


def _months_between(start: dt.date, end: dt.date) -> int:
    months = (end.year - start.year) * 12 + (end.month - start.month)
    return months - (1 if end.day < start.day else 0)


def check_renewal_notice(notice_date: dt.date, contract_end: dt.date) -> Dict[str, Any]:
    """Changes to renewal terms (including rent) need 90 days' notice before the contract ends."""
    days = (contract_end - notice_date).days
    ok = days >= RENEWAL_NOTICE_DAYS
    return {"compliant": ok, "days_given": days, "days_required": RENEWAL_NOTICE_DAYS, "rule": TENANCY_LAW,
            "reason": f"{days} days' notice given." + ("" if ok else f" At least {RENEWAL_NOTICE_DAYS} days are required.")}


def check_eviction_notice(notice_date: dt.date, contract_end: dt.date, reason: str) -> Dict[str, Any]:
    """Eviction at the end of the contract for sale, own use, demolition or renovation needs 12 months' notice."""
    if reason not in EVICTION_REASONS:
        raise ValueError(f"Unknown eviction reason '{reason}'. Use one of: {', '.join(EVICTION_REASONS)}.")
    months = _months_between(notice_date, contract_end)
    ok = months >= EVICTION_NOTICE_MONTHS
    return {"compliant": ok, "months_given": months, "months_required": EVICTION_NOTICE_MONTHS, "rule": TENANCY_LAW,
            "eviction_reason": EVICTION_REASONS[reason],
            "reason": f"{months} months' notice given." + ("" if ok else
                      f" Eviction because {EVICTION_REASONS[reason]} needs 12 months' notice through a notary public or registered mail.")}
