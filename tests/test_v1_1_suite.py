"""Unit and integration tests for EjariFlow v1.1 Enterprise capabilities.

Tests:
1. DEWA & District Cooling Tariff Forecaster (dewa_cooling.py)
2. Dubai 10-Year Real Estate Golden Visa Screener (golden_visa.py)
3. Automated 90-Day Renewal Dispatcher & SHA-256 Proof (notice_bot.py)
4. Interactive Dubai Metro Transit & Commute Isochrone Twin (transit_twin.py)
5. Server API Endpoints in server.py
"""

import unittest
from datetime import date, timedelta

from ejariflow.dewa_cooling import (
    calculate_dewa_electricity,
    calculate_dewa_water,
    calculate_municipality_fee,
    estimate_district_cooling,
    forecast_tenancy_utilities,
)
from ejariflow.golden_visa import (
    evaluate_golden_visa_eligibility,
    PropertyAsset,
    GOLDEN_VISA_MINIMUM_EQUITY_AED,
)
from ejariflow.notice_bot import (
    generate_sha256_proof,
    evaluate_statutory_window,
    dispatch_renewal_notice,
)
from ejariflow.transit_twin import (
    find_nearest_metro_station,
    calculate_transit_profile,
    METRO_STATIONS,
)
from ejariflow.server import route


class TestDewaCooling(unittest.TestCase):
    def test_electricity_slabs_low_tier(self):
        res = calculate_dewa_electricity(1000)
        # 1000 * 0.23 + 1000 * 0.05 fuel = 230 + 50 = 280 AED
        self.assertEqual(res["base_slab_charge_aed"], 230.0)
        self.assertEqual(res["fuel_surcharge_aed"], 50.0)
        self.assertEqual(res["total_electricity_aed"], 280.0)

    def test_electricity_slabs_high_tier(self):
        res = calculate_dewa_electricity(7000)
        # 2000*0.23 (460) + 2000*0.28 (560) + 2000*0.32 (640) + 1000*0.38 (380) = 2040
        # fuel: 7000*0.05 = 350 -> total 2390
        self.assertEqual(res["base_slab_charge_aed"], 2040.0)
        self.assertEqual(res["total_electricity_aed"], 2390.0)

    def test_water_slabs(self):
        res = calculate_dewa_water(8000)
        # 6000 * 0.035 (210) + 2000 * 0.040 (80) = 290 AED
        self.assertEqual(res["total_water_aed"], 290.0)

    def test_municipality_fee(self):
        fee = calculate_municipality_fee(120_000.0)
        # 120,000 * 5% = 6,000 / 12 = 500 AED / month
        self.assertEqual(fee, 500.0)

    def test_district_cooling_estimate(self):
        res = estimate_district_cooling(sqft=1200)
        self.assertGreater(res["cooling_capacity_tons"], 2.0)
        self.assertGreater(res["summer_monthly_avg_aed"], res["winter_monthly_avg_aed"])
        self.assertGreater(res["annual_cooling_cost_aed"], 2000.0)

    def test_forecast_chiller_free_vs_district(self):
        dist = forecast_tenancy_utilities(sqft=1000, annual_rent=90000, chiller_type="district_cooling")
        free = forecast_tenancy_utilities(sqft=1000, annual_rent=90000, chiller_type="chiller_free")
        self.assertGreater(dist["annual_totals_aed"]["grand_total"], free["annual_totals_aed"]["grand_total"])
        self.assertGreater(dist["chiller_free_annual_savings_aed"], 0)


class TestGoldenVisaScreener(unittest.TestCase):
    def test_single_qualifying_property(self):
        props = [{"id": "P-1", "purchase_price_aed": 2_500_000, "mortgage_balance_aed": 0}]
        res = evaluate_golden_visa_eligibility(props)
        self.assertEqual(res["status"], "QUALIFIED")
        self.assertEqual(res["readiness_score"], 100)
        self.assertEqual(res["equity_shortfall_aed"], 0.0)

    def test_multi_property_aggregation(self):
        props = [
            {"id": "P-1", "purchase_price_aed": 1_200_000, "mortgage_balance_aed": 0},
            {"id": "P-2", "purchase_price_aed": 950_000, "mortgage_balance_aed": 0},
        ]
        res = evaluate_golden_visa_eligibility(props)
        self.assertEqual(res["status"], "QUALIFIED")
        self.assertEqual(res["total_qualifying_equity_aed"], 2_150_000.0)

    def test_mortgaged_property_with_paid_equity(self):
        props = [{"id": "P-1", "purchase_price_aed": 3_500_000, "mortgage_balance_aed": 1_200_000}]
        res = evaluate_golden_visa_eligibility(props)
        self.assertEqual(res["status"], "QUALIFIED")
        self.assertEqual(res["total_qualifying_equity_aed"], 2_300_000.0)

    def test_marginal_deficit(self):
        props = [{"id": "P-1", "purchase_price_aed": 1_850_000, "mortgage_balance_aed": 0}]
        res = evaluate_golden_visa_eligibility(props)
        self.assertEqual(res["status"], "MARGINAL_DEFICIT")
        self.assertEqual(res["equity_shortfall_aed"], 150_000.0)

    def test_unqualified(self):
        props = [{"id": "P-1", "purchase_price_aed": 900_000, "mortgage_balance_aed": 0}]
        res = evaluate_golden_visa_eligibility(props)
        self.assertEqual(res["status"], "UNQUALIFIED")
        self.assertGreater(res["equity_shortfall_aed"], 500_000.0)


class TestNoticeDispatcher(unittest.TestCase):
    def test_sha256_proof_deterministic(self):
        h1 = generate_sha256_proof("EJ-1", "2026-11-19T10:00:00Z", "Ali", 90000, 80000, "whatsapp")
        h2 = generate_sha256_proof("EJ-1", "2026-11-19T10:00:00Z", "Ali", 90000, 80000, "whatsapp")
        self.assertEqual(h1, h2)
        self.assertEqual(len(h1), 64)

    def test_statutory_window_compliant(self):
        dispatch = date(2026, 1, 1)
        expiry = (dispatch + timedelta(days=95)).isoformat()
        res = evaluate_statutory_window(expiry, dispatch)
        self.assertTrue(res["is_compliant"])
        self.assertEqual(res["status"], "COMPLIANT_ADVANCE")
        self.assertEqual(res["rdsc_admissibility"], "HIGH")

    def test_statutory_window_late(self):
        dispatch = date(2026, 1, 1)
        expiry = (dispatch + timedelta(days=60)).isoformat()
        res = evaluate_statutory_window(expiry, dispatch)
        self.assertFalse(res["is_compliant"])
        self.assertEqual(res["status"], "LATE_NOTICE_VOID_INCREASE")
        self.assertEqual(res["rdsc_admissibility"], "DISMISSIBLE")

    def test_full_notice_dispatch(self):
        expiry = (date.today() + timedelta(days=100)).isoformat()
        res = dispatch_renewal_notice(
            ejari_number="EJ-992288",
            tenant_name="Sarah Smith",
            tenant_phone="+971501112233",
            tenant_email="sarah@example.com",
            property_name="Marina Crest",
            unit_number="1402",
            current_rent=80000,
            proposed_rent=88000,
            expiry_date=expiry,
            channel="whatsapp_and_email",
        )
        self.assertTrue(res["dispatch_id"].startswith("DISP-"))
        self.assertIn("Sarah Smith", res["bilingual_notice"]["english"])
        self.assertIn("Sarah Smith", res["bilingual_notice"]["arabic"])
        self.assertEqual(len(res["delivery_channels"]), 2)
        self.assertEqual(res["cryptographic_proof"]["algorithm"], "SHA-256")


class TestTransitTwin(unittest.TestCase):
    def test_nearest_station_financial_centre(self):
        # Coordinates near X=10, Z=-46
        res = find_nearest_metro_station(x=12.0, z=-45.0)
        self.assertEqual(res["station"]["code"], "R24")
        self.assertTrue(res["in_5min_isochrone"])
        self.assertTrue(res["in_10min_isochrone"])

    def test_transit_profile_scoring(self):
        res = calculate_transit_profile("DIFC Tower", x=10.0, z=-46.0)
        self.assertGreaterEqual(res["transit_mobility_score"], 80)
        self.assertIn("Super-Transit", res["transit_tier"])
        self.assertEqual(len(res["commute_destinations"]), 4)


class TestServerRoutes(unittest.TestCase):
    def test_utilities_route(self):
        code, body = route("POST", "/api/utilities/forecast", {"sqft": 1100, "annual_rent": 95000})
        self.assertEqual(code, 200)
        self.assertIn("annual_totals_aed", body)

    def test_golden_visa_route(self):
        code, body = route("POST", "/api/golden-visa/evaluate", {
            "applicant_name": "Test Investor",
            "properties": [{"purchase_price_aed": 2_200_000}]
        })
        self.assertEqual(code, 200)
        self.assertEqual(body["status"], "QUALIFIED")

    def test_notice_dispatch_route(self):
        code, body = route("POST", "/api/notices/dispatch", {
            "tenant_name": "John",
            "current_rent": 100000,
            "proposed_rent": 105000
        })
        self.assertEqual(code, 200)
        self.assertIn("cryptographic_proof", body)

    def test_transit_profile_route(self):
        code, body = route("POST", "/api/transit/profile", {"property_name": "Test Tower", "x": 0, "z": -46})
        self.assertEqual(code, 200)
        self.assertIn("transit_mobility_score", body)

    def test_transit_stations_route(self):
        code, body = route("GET", "/api/transit/stations", {})
        self.assertEqual(code, 200)
        self.assertEqual(len(body["stations"]), 5)


if __name__ == "__main__":
    unittest.main()
