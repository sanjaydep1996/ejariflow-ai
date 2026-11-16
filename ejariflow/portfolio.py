# Copyright (c) 2026 Sanjaydeep Gowrishankar. Licensed under the MIT License.

"""Portfolio view: every unit's occupancy, lease expiry and rent-cap status, ready for the 3D map."""

import datetime as dt
import json
import pathlib
from typing import Any, Dict, Optional

from . import rera

SAMPLE = pathlib.Path(__file__).resolve().parent.parent / "data" / "sample-portfolio.json"


def expiry_band(days: int) -> str:
    if days < 0:
        return "expired"
    if days <= 90:
        return "due_90"        # inside the 90-day renewal notice window
    if days <= 180:
        return "due_180"
    return "later"


def analyse(portfolio: Dict[str, Any], today: Optional[dt.date] = None) -> Dict[str, Any]:
    today = today or dt.date.fromisoformat(portfolio.get("generated_for") or dt.date.today().isoformat())
    totals = {"units": 0, "occupied": 0, "vacant": 0, "expired": 0, "due_90": 0, "due_180": 0, "over_cap": 0, "annual_rent": 0}
    buildings = []
    for b in portfolio.get("buildings", []):
        units = []
        for u in b.get("units", []):
            unit = dict(u)
            totals["units"] += 1
            if not u.get("occupied"):
                totals["vacant"] += 1
                unit["status"] = "vacant"
                units.append(unit)
                continue
            totals["occupied"] += 1
            totals["annual_rent"] += u.get("annual_rent", 0)
            days = (dt.date.fromisoformat(u["lease_end"]) - today).days
            unit["days_to_expiry"] = days
            unit["expiry"] = expiry_band(days)
            if unit["expiry"] in totals:
                totals[unit["expiry"]] += 1
            if u.get("proposed_rent") and b.get("avg_rent"):
                check = rera.check_increase(u["annual_rent"], u["proposed_rent"], b["avg_rent"])
                unit["rent_check"] = {k: check[k] for k in ("compliant", "max_percent", "max_rent", "proposed_percent", "reason")}
                if not check["compliant"]:
                    totals["over_cap"] += 1
            unit["status"] = ("over_cap" if not unit.get("rent_check", {}).get("compliant", True) else unit["expiry"])
            units.append(unit)
        buildings.append({**{k: v for k, v in b.items() if k != "units"}, "units": units})
    totals["occupancy_percent"] = round(totals["occupied"] / totals["units"] * 100, 1) if totals["units"] else 0
    return {"today": today.isoformat(), "totals": totals, "buildings": buildings, "note": portfolio.get("note", "")}


def load_sample() -> Dict[str, Any]:
    return json.loads(SAMPLE.read_text(encoding="utf-8"))
