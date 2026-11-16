# Copyright (c) 2026 Sanjaydeep Gowrishankar. Licensed under the MIT License.

"""Reads a Dubai tenancy contract (English or Arabic text) into structured fields.

This is the rules-based first stage of the document pipeline: it works on text, from a typed contract,
a PDF's text layer (`pdftotext`) or OCR output. Fields it can't find are listed in `missing` rather
than guessed, so a later stage (OCR clean-up, a local vision model, or a person) knows what to check.
"""

import datetime as dt
import re
import shutil
import subprocess
from typing import Any, Dict, List, Optional

ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹٬٫", "01234567890123456789,.")
DATE = r"(\d{1,2}[/.-]\d{1,2}[/.-]\d{4}|\d{4}-\d{2}-\d{2})"
AMOUNT = r"(?:AED|Dhs?\.?|درهم)?\s*([\d,]+(?:\.\d+)?)\s*(?:AED|درهم)?"

FIELDS = {
    "ejari_number": [r"Ejari(?:\s+Contract)?\s*(?:No\.?|Number)\s*[:#]?\s*(\d{10,20})", r"رقم\s+(?:عقد\s+)?إيجاري\s*[:#]?\s*(\d{10,20})"],
    "landlord": [r"(?:Owner\s*/\s*Lessor|Lessor|Landlord|Owner)(?:'s)?\s+Name\s*:\s*(.+)", r"اسم\s+(?:المالك|المؤجر)\s*:\s*(.+)"],
    "tenant": [r"Tenant(?:'s)?\s+Name\s*:\s*(.+)", r"اسم\s+المستأجر\s*:\s*(.+)"],
    "building": [r"Building\s+Name\s*:\s*(.+)", r"اسم\s+المبنى\s*:\s*(.+)"],
    "unit": [r"(?:Unit|Flat|Apartment)\s+No\.?\s*:\s*([\w-]+)", r"رقم\s+الوحدة\s*:\s*([\w-]+)"],
    "area": [r"(?:Area|Location|Community)\s*:\s*(.+)", r"المنطقة\s*:\s*(.+)"],
    "plot": [r"Plot\s+No\.?\s*:\s*([\w-]+)", r"رقم\s+(?:الأرض|القطعة)\s*:\s*([\w-]+)"],
    "property_type": [r"Property\s+Type\s*:\s*(.+)", r"نوع\s+العقار\s*:\s*(.+)"],
    "annual_rent": [r"Annual\s+Rent\s*:\s*" + AMOUNT, r"(?:Rent\s+Amount|Contract\s+Value)\s*:\s*" + AMOUNT, r"الإيجار\s+السنوي\s*:\s*" + AMOUNT],
    "security_deposit": [r"Security\s+Deposit(?:\s+Amount)?\s*:\s*" + AMOUNT, r"(?:مبلغ\s+)?التأمين\s*:\s*" + AMOUNT],
    "start_date": [r"(?:Contract\s+Period\s+)?From\s*:?\s*" + DATE, r"(?:Start|Commencement)\s+Date\s*:\s*" + DATE, r"تاريخ\s+البدء\s*:\s*" + DATE],
    "end_date": [r"(?:Contract\s+Period.*?)?\bTo\s*:?\s*" + DATE, r"(?:End|Expiry)\s+Date\s*:\s*" + DATE, r"تاريخ\s+الانتهاء\s*:\s*" + DATE],
    "cheques": [r"(\d{1,2})\s+cheques?", r"(\d{1,2})\s+شيكات"],
}
REQUIRED = ["ejari_number", "landlord", "tenant", "annual_rent", "start_date", "end_date"]


def _normalise(text: str) -> str:
    return (text or "").translate(ARABIC_DIGITS).replace("\r", "")


def _date(value: str) -> Optional[str]:
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y", "%Y-%m-%d"):
        try:
            return dt.datetime.strptime(value, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def _first(text: str, patterns: List[str]) -> Optional[str]:
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            return m.group(1).strip().rstrip(".,;")
    return None


def _amount(value: Optional[str]) -> Optional[float]:
    if not value:
        return None
    try:
        n = float(value.replace(",", ""))
    except ValueError:
        return None
    return int(n) if n.is_integer() else n


def special_conditions(text: str) -> List[str]:
    """The numbered clauses under a SPECIAL CONDITIONS / ADDENDUM heading (or its Arabic equivalent)."""
    m = re.search(r"(?:SPECIAL\s+CONDITIONS|ADDENDUM|ADDITIONAL\s+TERMS|شروط\s+(?:خاصة|إضافية))\s*\n(.+)", text, re.IGNORECASE | re.DOTALL)
    if not m:
        return []
    clauses = re.findall(r"^\s*\d+[.)]\s*(.+)$", m.group(1), re.MULTILINE)
    return [c.strip() for c in clauses]


def parse_contract(text: str) -> Dict[str, Any]:
    t = _normalise(text)
    raw = {name: _first(t, patterns) for name, patterns in FIELDS.items()}
    arabic = len(re.findall(r"[؀-ۿ]", t))
    latin = len(re.findall(r"[A-Za-z]", t))
    contract = {
        "ejari_number": raw["ejari_number"],
        "landlord": raw["landlord"],
        "tenant": raw["tenant"],
        "property": {k: raw[k] for k in ("building", "unit", "area", "plot", "property_type")},
        "annual_rent": _amount(raw["annual_rent"]),
        "security_deposit": _amount(raw["security_deposit"]),
        "start_date": _date(raw["start_date"]) if raw["start_date"] else None,
        "end_date": _date(raw["end_date"]) if raw["end_date"] else None,
        "payments": {"cheques": int(raw["cheques"]) if raw["cheques"] else None},
        "special_conditions": special_conditions(t),
        "language": "ar" if arabic > latin else "en",
    }
    contract["missing"] = [f for f in REQUIRED if contract.get(f) in (None, "")]
    return contract


def text_from_pdf(path: str) -> str:
    """The text layer of a PDF, using poppler's `pdftotext` if it is installed. Scanned PDFs need OCR first."""
    exe = shutil.which("pdftotext")
    if not exe:
        raise RuntimeError("pdftotext isn't installed (brew install poppler / apt install poppler-utils).")
    r = subprocess.run([exe, "-layout", path, "-"], capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip() or "pdftotext failed")
    return r.stdout
