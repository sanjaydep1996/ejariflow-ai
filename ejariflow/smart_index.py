# Copyright (c) 2026 Sanjaydeep Gowrishankar. Licensed under the MIT License.

"""DLD Smart Rental Index & 5-Star Building Rating Engine.

Calculates technical classifications (1 to 5 stars) based on Dubai Land Department (DLD)
criteria: building age, chiller infrastructure, amenities, transit proximity, and green rating.
Determines building-specific benchmark rents and models allowable RERA rental increases
under Dubai Decree No. 43 of 2013.
"""

from typing import Any, Dict, List, Optional
from . import rera


def calculate_building_score(specs: Dict[str, Any]) -> Dict[str, Any]:
    """Scores a building from 0 to 100 based on official DLD technical parameters."""
    breakdown = {}
    
    # 1. Structural Age (Max 25 pts)
    age = int(specs.get("age_years", 5))
    if age <= 3:
        age_pts = 25
    elif age <= 7:
        age_pts = 20
    elif age <= 15:
        age_pts = 14
    elif age <= 25:
        age_pts = 8
    else:
        age_pts = 4
    breakdown["structural_age"] = {"points": age_pts, "max": 25, "value": f"{age} years"}

    # 2. Chiller & Energy Infrastructure (Max 20 pts)
    cooling = str(specs.get("cooling_type", "district_cooling")).lower()
    if cooling in ("chiller_free", "chiller-free"):
        cool_pts = 20
        cool_label = "Chiller-free (Included)"
    elif cooling in ("district_cooling", "empower", "tabreed"):
        cool_pts = 15
        cool_label = "District Cooling (Empower/Tabreed)"
    else:
        cool_pts = 7
        cool_label = "Individual Split AC"
    breakdown["cooling_system"] = {"points": cool_pts, "max": 20, "value": cool_label}

    # 3. Amenities & Facilities (Max 30 pts)
    amenity_pts = 0
    amenities = specs.get("amenities", [])
    if isinstance(amenities, dict):
        amenities = [k for k, v in amenities.items() if v]
    amenities_set = {str(a).lower() for a in amenities}
    
    amenity_weights = {
        "infinity_pool": 8, "swimming_pool": 6, "gym": 6, "spa_sauna": 4,
        "concierge_24_7": 6, "covered_parking": 4, "ev_chargers": 3,
        "children_play_area": 3, "padel_tennis_court": 3
    }
    for item, weight in amenity_weights.items():
        if item in amenities_set or (item == "swimming_pool" and "pool" in amenities_set):
            amenity_pts += weight
    amenity_pts = min(30, amenity_pts)
    breakdown["amenities"] = {"points": amenity_pts, "max": 30, "count": len(amenities_set)}

    # 4. Transit & Dubai Metro Proximity (Max 15 pts)
    metro_dist = int(specs.get("metro_distance_meters", 600))
    if metro_dist <= 300:
        metro_pts = 15
    elif metro_dist <= 600:
        metro_pts = 12
    elif metro_dist <= 1200:
        metro_pts = 7
    else:
        metro_pts = 3
    breakdown["metro_proximity"] = {"points": metro_pts, "max": 15, "value": f"{metro_dist}m"}

    # 5. Sustainability & Green Certification (Max 10 pts)
    has_green_cert = bool(specs.get("green_certified") or specs.get("leed_certified"))
    green_pts = 10 if has_green_cert else 2
    breakdown["sustainability"] = {"points": green_pts, "max": 10, "certified": has_green_cert}

    total_score = age_pts + cool_pts + amenity_pts + metro_pts + green_pts

    # Star rating tiers:
    if total_score >= 85:
        stars = 5
        tier = "5-Star Ultra Luxury"
        multiplier = 1.15   # +15% over standard area baseline
    elif total_score >= 70:
        stars = 4
        tier = "4-Star Prime Luxury"
        multiplier = 1.08   # +8% over standard area baseline
    elif total_score >= 50:
        stars = 3
        tier = "3-Star Standard Residential"
        multiplier = 1.00   # Baseline
    elif total_score >= 35:
        stars = 2
        tier = "2-Star Economy"
        multiplier = 0.90   # -10%
    else:
        stars = 1
        tier = "1-Star Basic"
        multiplier = 0.80   # -20%

    return {
        "score": total_score,
        "stars": stars,
        "star_display": "★" * stars + "☆" * (5 - stars),
        "tier": tier,
        "market_multiplier": multiplier,
        "breakdown": breakdown
    }


def evaluate_smart_index(
    building_name: str,
    area: str,
    base_area_average: float,
    current_unit_rent: float,
    proposed_unit_rent: float,
    specs: Dict[str, Any],
    proposed_upgrades: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Evaluates building rating and calculates Decree 43/2013 allowable rent cap."""
    base_eval = calculate_building_score(specs)
    adjusted_benchmark = round(base_area_average * base_eval["market_multiplier"])

    # Standard RERA cap check against the building's smart benchmark
    rera_result = rera.check_increase(current_unit_rent, proposed_unit_rent, adjusted_benchmark)

    result = {
        "building_name": building_name,
        "area": area,
        "base_area_average": base_area_average,
        "smart_benchmark_rent": adjusted_benchmark,
        "rating": base_eval,
        "rera_check": rera_result,
        "citation": "DLD Smart Rental Index 2024 & Dubai Decree No. 43 of 2013"
    }

    # Simulate upgrades if requested
    if proposed_upgrades:
        simulated_specs = dict(specs)
        current_amenities = set(simulated_specs.get("amenities", []))
        for up in proposed_upgrades:
            u_clean = up.lower()
            if "chiller" in u_clean:
                simulated_specs["cooling_type"] = "chiller_free"
            elif "green" in u_clean or "leed" in u_clean:
                simulated_specs["green_certified"] = True
            elif "concierge" in u_clean:
                current_amenities.add("concierge_24_7")
            elif "ev" in u_clean:
                current_amenities.add("ev_chargers")
            else:
                current_amenities.add(u_clean)
        simulated_specs["amenities"] = list(current_amenities)
        
        sim_eval = calculate_building_score(simulated_specs)
        sim_benchmark = round(base_area_average * sim_eval["market_multiplier"])
        sim_rera = rera.check_increase(current_unit_rent, proposed_unit_rent, sim_benchmark)

        result["upgrade_simulation"] = {
            "proposed_upgrades": proposed_upgrades,
            "new_rating": sim_eval,
            "new_smart_benchmark": sim_benchmark,
            "benchmark_delta": sim_benchmark - adjusted_benchmark,
            "new_rera_check": sim_rera
        }

    return result
