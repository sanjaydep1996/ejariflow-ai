"""DEWA & District Cooling (Empower / Tabreed) Tariff Forecaster.

Models official Dubai utility tariffs:
- DEWA Residential Expat Electricity slabs (23 to 38 fils/kWh) + fuel surcharge.
- DEWA Residential Expat Water slabs (3.5 to 4.6 fils/Imperial Gallon).
- Dubai Municipality Housing Fee (5% of annual rent / 12 months).
- District Cooling (Empower / Tabreed / Emicool):
    * Capacity charge (RT per year, typically ~AED 750/RT/year).
    * Consumption charge (metered RT-hour ~AED 0.568/RT-h).
    * Meter maintenance & billing admin fees.
- Chiller-Free vs. District Cooling comparison.
"""

from dataclasses import dataclass
from typing import Dict, Any, List

# DEWA Expat Residential Electricity Slabs (fils per kWh, 1 AED = 100 fils)
# 1-2000 kWh: 23 fils, 2001-4000: 28 fils, 4001-6000: 32 fils, 6001+: 38 fils
ELECTRICITY_SLABS = [
    (2000, 0.23),
    (2000, 0.28),
    (2000, 0.32),
    (float("inf"), 0.38),
]
FUEL_SURCHARGE_PER_KWH = 0.05  # 5 fils per kWh fuel adjustment

# DEWA Expat Residential Water Slabs (fils per Imperial Gallon)
# 0-6000 IG: 3.5 fils, 6001-12000 IG: 4.0 fils, 12001+ IG: 4.6 fils
WATER_SLABS = [
    (6000, 0.035),
    (6000, 0.040),
    (float("inf"), 0.046),
]

# District Cooling Benchmarks (Dubai / Empower / Tabreed standards)
DEFAULT_CAPACITY_CHARGE_PER_RT_ANNUAL = 750.0  # AED per Refrigeration Ton / year
DEFAULT_CONSUMPTION_RATE_PER_RTH = 0.568       # AED per RT-hour
DEFAULT_MONTHLY_ADMIN_FEE = 40.0              # Meter admin / connection charge

# Average cooling load sizing (Refrigeration Tons per sq ft in UAE)
# ~1 RT per 350-450 sq ft of residential space
RT_PER_SQFT = 1.0 / 400.0


def calculate_dewa_electricity(monthly_kwh: float) -> Dict[str, float]:
    """Calculate progressive DEWA electricity charges under Dubai slab tariffs."""
    remaining = max(0.0, monthly_kwh)
    slab_charge = 0.0
    for slab_limit, rate in ELECTRICITY_SLABS:
        if remaining <= 0:
            break
        used = min(remaining, slab_limit)
        slab_charge += used * rate
        remaining -= used
    
    fuel_surcharge = monthly_kwh * FUEL_SURCHARGE_PER_KWH
    total = round(slab_charge + fuel_surcharge, 2)
    return {
        "monthly_kwh": round(monthly_kwh, 1),
        "base_slab_charge_aed": round(slab_charge, 2),
        "fuel_surcharge_aed": round(fuel_surcharge, 2),
        "total_electricity_aed": total
    }


def calculate_dewa_water(monthly_ig: float) -> Dict[str, float]:
    """Calculate progressive DEWA water charges under Dubai slab tariffs."""
    remaining = max(0.0, monthly_ig)
    water_charge = 0.0
    for slab_limit, rate in WATER_SLABS:
        if remaining <= 0:
            break
        used = min(remaining, slab_limit)
        water_charge += used * rate
        remaining -= used
    
    return {
        "monthly_imperial_gallons": round(monthly_ig, 1),
        "total_water_aed": round(water_charge, 2)
    }


def calculate_municipality_fee(annual_rent: float) -> float:
    """Dubai Municipality housing fee is 5% of annual rent divided across 12 monthly bills."""
    return round((annual_rent * 0.05) / 12.0, 2)


def estimate_district_cooling(
    sqft: float,
    summer_months: int = 5,
    capacity_charge_annual: float = DEFAULT_CAPACITY_CHARGE_PER_RT_ANNUAL,
    consumption_rate_rth: float = DEFAULT_CONSUMPTION_RATE_PER_RTH,
) -> Dict[str, Any]:
    """Estimate monthly and annual district cooling charges (Tabreed / Empower)."""
    tons = max(1.0, round(sqft * RT_PER_SQFT, 2))
    monthly_capacity_charge = (tons * capacity_charge_annual) / 12.0
    
    # Summer hours: ~14 hrs/day full load; Winter: ~4 hrs/day
    summer_rth_per_month = tons * 14.0 * 30.0 * 0.70  # diversity factor 70%
    winter_rth_per_month = tons * 4.0 * 30.0 * 0.50   # diversity factor 50%
    
    summer_consumption = summer_rth_per_month * consumption_rate_rth
    winter_consumption = winter_rth_per_month * consumption_rate_rth
    
    monthly_summer_bill = round(monthly_capacity_charge + summer_consumption + DEFAULT_MONTHLY_ADMIN_FEE, 2)
    monthly_winter_bill = round(monthly_capacity_charge + winter_consumption + DEFAULT_MONTHLY_ADMIN_FEE, 2)
    
    winter_months = 12 - summer_months
    annual_total = round((monthly_summer_bill * summer_months) + (monthly_winter_bill * winter_months), 2)
    
    return {
        "cooling_capacity_tons": tons,
        "monthly_capacity_fixed_aed": round(monthly_capacity_charge, 2),
        "monthly_admin_fee_aed": DEFAULT_MONTHLY_ADMIN_FEE,
        "summer_monthly_avg_aed": monthly_summer_bill,
        "winter_monthly_avg_aed": monthly_winter_bill,
        "annual_cooling_cost_aed": annual_total,
        "summer_months_assumed": summer_months,
    }


def forecast_tenancy_utilities(
    sqft: float,
    annual_rent: float,
    chiller_type: str = "district_cooling",  # "chiller_free" or "district_cooling"
    occupants: int = 2,
) -> Dict[str, Any]:
    """Provide comprehensive summer vs winter utility breakdown and chiller-free savings."""
    # Base electricity consumption estimates (lighting, appliances, plug load)
    # If chiller-free, HVAC power is borne by building owner, but tenant still pays DEWA for apartment
    base_kwh_per_sqft_monthly = 0.85 + (occupants * 60.0 / max(sqft, 300.0))
    
    # In chiller-free units with individual split ACs, electricity is higher in summer
    summer_elec_kwh = sqft * (base_kwh_per_sqft_monthly * (1.6 if chiller_type == "chiller_free" else 1.1))
    winter_elec_kwh = sqft * (base_kwh_per_sqft_monthly * 0.85)
    
    elec_summer = calculate_dewa_electricity(summer_elec_kwh)
    elec_winter = calculate_dewa_electricity(winter_elec_kwh)
    
    # Water: ~45 Imperial Gallons per occupant per day
    monthly_ig = occupants * 45.0 * 30.0
    water_res = calculate_dewa_water(monthly_ig)
    
    muni_fee = calculate_municipality_fee(annual_rent)
    
    is_district = (chiller_type.lower() != "chiller_free")
    cooling_res = estimate_district_cooling(sqft) if is_district else None
    
    cooling_summer = cooling_res["summer_monthly_avg_aed"] if cooling_res else 0.0
    cooling_winter = cooling_res["winter_monthly_avg_aed"] if cooling_res else 0.0
    cooling_annual = cooling_res["annual_cooling_cost_aed"] if cooling_res else 0.0
    
    monthly_summer_total = round(elec_summer["total_electricity_aed"] + water_res["total_water_aed"] + muni_fee + cooling_summer, 2)
    monthly_winter_total = round(elec_winter["total_electricity_aed"] + water_res["total_water_aed"] + muni_fee + cooling_winter, 2)
    
    # Full year cost (5 summer months May-Sep, 7 winter/moderate months)
    elec_annual = (elec_summer["total_electricity_aed"] * 5) + (elec_winter["total_electricity_aed"] * 7)
    water_annual = water_res["total_water_aed"] * 12
    muni_annual = muni_fee * 12
    annual_grand_total = round(elec_annual + water_annual + muni_annual + cooling_annual, 2)
    
    # Chiller-free net tenant savings comparison
    chiller_free_annual_cooling_savings = cooling_annual if is_district else 0.0
    
    return {
        "property_sqft": sqft,
        "annual_rent_aed": annual_rent,
        "chiller_type": "chiller_free" if not is_district else "district_cooling",
        "occupants": occupants,
        "monthly_breakdown": {
            "summer_peak_month_aed": monthly_summer_total,
            "winter_moderate_month_aed": monthly_winter_total,
            "dewa_electricity_summer_aed": elec_summer["total_electricity_aed"],
            "dewa_electricity_winter_aed": elec_winter["total_electricity_aed"],
            "dewa_water_monthly_aed": water_res["total_water_aed"],
            "municipality_housing_fee_monthly_aed": muni_fee,
            "district_cooling_summer_aed": cooling_summer,
            "district_cooling_winter_aed": cooling_winter,
        },
        "annual_totals_aed": {
            "electricity": round(elec_annual, 2),
            "water": round(water_annual, 2),
            "municipality_housing_fee": round(muni_annual, 2),
            "district_cooling": round(cooling_annual, 2),
            "grand_total": annual_grand_total,
        },
        "chiller_free_annual_savings_aed": round(chiller_free_annual_cooling_savings, 2),
        "utility_cost_percent_of_rent": round((annual_grand_total / max(1.0, annual_rent)) * 100.0, 1),
    }
