# Copyright (c) 2026 Sanjaydeep Gowrishankar. Licensed under the MIT License.

"""UAE Direct Debit System (UAEDDS) & Digital Rental Payment Engine.

Implements Central Bank of the UAE and Dubai Land Department (DLD) paperless rental
mandate guidelines. Converts traditional physical post-dated cheque structures into
compliant direct debit payment schedules with UAE IBAN validation and statutory grace tracking.
"""

import datetime as dt
import re
from typing import Any, Dict, List, Optional


def validate_uae_iban(iban: str) -> Dict[str, Any]:
    """Validates a UAE International Bank Account Number (23 chars: AE + 21 digits/chars)."""
    clean = re.sub(r"\s+", "", str(iban or "")).upper()
    if not clean.startswith("AE"):
        return {"valid": False, "reason": "UAE IBAN must start with country code 'AE'."}
    if len(clean) != 23:
        return {"valid": False, "reason": f"UAE IBAN must be exactly 23 characters long (got {len(clean)})."}
    if not clean[2:].isalnum():
        return {"valid": False, "reason": "UAE IBAN contains invalid characters."}
    
    bank_code = clean[4:7]
    KNOWN_BANKS = {
        "033": "Emirates NBD",
        "024": "First Abu Dhabi Bank (FAB)",
        "035": "Dubai Islamic Bank (DIB)",
        "023": "Abu Dhabi Commercial Bank (ADCB)",
        "044": "Mashreq Bank",
        "030": "Abu Dhabi Islamic Bank (ADIB)",
        "026": "Commercial Bank of Dubai (CBD)"
    }
    bank_name = KNOWN_BANKS.get(bank_code, f"UAE Registered Bank (Routing: {bank_code})")
    
    return {
        "valid": True,
        "clean_iban": clean,
        "formatted": f"{clean[0:4]} {clean[4:8]} {clean[8:12]} {clean[12:16]} {clean[16:20]} {clean[20:23]}",
        "bank_name": bank_name,
        "bank_code": bank_code
    }


def generate_uaedds_schedule(
    annual_rent: float,
    lease_start: str,
    installments_count: int = 4,
    tenant_name: str = "Tenant",
    landlord_name: str = "Landlord",
    tenant_iban: Optional[str] = None,
    property_name: str = "Unit 101, Dubai",
    is_furnished: bool = False
) -> Dict[str, Any]:
    """Generates an official UAEDDS direct debit schedule and statutory payment calendar."""
    if installments_count not in (1, 2, 4, 6, 12):
        installments_count = 4

    try:
        start_date = dt.date.fromisoformat(lease_start)
    except (ValueError, TypeError):
        start_date = dt.date.today()

    iban_info = validate_uae_iban(tenant_iban) if tenant_iban else {"valid": False, "reason": "No IBAN supplied"}

    # Base per-installment rent
    installment_amount = round(annual_rent / installments_count, 2)
    step_months = 12 // installments_count

    schedule: List[Dict[str, Any]] = []
    for i in range(installments_count):
        # Calculate debit date (approximate equal monthly spacing)
        # Advance by (i * step_months) months
        month_offset = i * step_months
        year = start_date.year + (start_date.month - 1 + month_offset) // 12
        month = ((start_date.month - 1 + month_offset) % 12) + 1
        day = min(start_date.day, 28)
        debit_date = dt.date(year, month, day)

        # Statutory 30-day default cure notice date under Art. 25(1)(a)
        cure_deadline = debit_date + dt.timedelta(days=30)

        schedule.append({
            "installment_no": i + 1,
            "total_installments": installments_count,
            "due_date": debit_date.isoformat(),
            "amount_aed": installment_amount,
            "channel": "Central Bank UAEDDS Direct Debit",
            "statutory_cure_deadline": cure_deadline.isoformat(),
            "status": "Scheduled"
        })

    # Standard Security Deposit Benchmark (5% unfurnished / 10% furnished per Dubai custom)
    deposit_pct = 10 if is_furnished else 5
    security_deposit = round(annual_rent * (deposit_pct / 100))

    # Mandate Reference Number
    mandate_ref = f"UAEDDS-EJARI-{start_date.strftime('%Y%m')}-{abs(hash(property_name)) % 100000:05d}"

    return {
        "annual_rent": annual_rent,
        "installments_count": installments_count,
        "per_installment_amount": installment_amount,
        "lease_start": start_date.isoformat(),
        "tenant_name": tenant_name,
        "landlord_name": landlord_name,
        "property": property_name,
        "mandate_reference": mandate_ref,
        "is_furnished": is_furnished,
        "security_deposit_aed": security_deposit,
        "security_deposit_percent": deposit_pct,
        "tenant_iban_info": iban_info,
        "schedule": schedule,
        "regulatory_framework": "Central Bank of the UAE & Dubai Land Department (DLD) Direct Debit Mandate",
        "statutory_rule": "Dubai Law No. 26 of 2007 (Art. 25(1)(a) - 30-day default cure period)"
    }
