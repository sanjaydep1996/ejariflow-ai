# Copyright (c) 2026 Sanjaydeep Gowrishankar. Licensed under the MIT License.

"""Unit tests for EjariFlow AI v1.0 Enterprise features:
1. DLD Smart Rental Index & 5-Star Building Rating Calculator
2. RDSC Legal Risk & Eviction Forecaster
3. UAE Direct Debit System (UAEDDS) Engine
4. HTTP Endpoints in Server
"""

import json
import unittest
from ejariflow import calculate_building_score, evaluate_smart_index, forecast_eviction_case, generate_uaedds_schedule, validate_uae_iban
from ejariflow.server import route


class TestSmartRentalIndex(unittest.TestCase):
    def test_five_star_building_scoring(self):
        specs = {
            "age_years": 2,
            "cooling_type": "chiller_free",
            "amenities": ["swimming_pool", "gym", "concierge_24_7", "covered_parking", "ev_chargers"],
            "metro_distance_meters": 250,
            "green_certified": True
        }
        score = calculate_building_score(specs)
        self.assertGreaterEqual(score["score"], 85)
        self.assertEqual(score["stars"], 5)
        self.assertEqual(score["market_multiplier"], 1.15)

    def test_upgrade_simulation(self):
        specs = {
            "age_years": 8,
            "cooling_type": "individual_ac",
            "amenities": ["gym"],
            "metro_distance_meters": 800
        }
        res = evaluate_smart_index(
            building_name="Marina View",
            area="Dubai Marina",
            base_area_average=100000,
            current_unit_rent=85000,
            proposed_unit_rent=95000,
            specs=specs,
            proposed_upgrades=["chiller_free", "concierge_24_7", "green_certified"]
        )
        self.assertIn("upgrade_simulation", res)
        self.assertGreater(res["upgrade_simulation"]["new_smart_benchmark"], res["smart_benchmark_rent"])


class TestRDSCForecaster(unittest.TestCase):
    def test_valid_twelve_month_notary_notice(self):
        res = forecast_eviction_case(
            ground="sale",
            notice_date="2026-01-01",
            target_eviction_date="2027-01-15",
            notice_method="notary_public",
            current_annual_rent=120000
        )
        self.assertTrue(res["viable"])
        self.assertGreaterEqual(res["success_probability_percent"], 85)

    def test_insufficient_notice_period(self):
        res = forecast_eviction_case(
            ground="personal_use",
            notice_date="2026-01-01",
            target_eviction_date="2026-07-01",  # only 6 months!
            notice_method="notary_public"
        )
        self.assertFalse(res["viable"])
        self.assertIn("insufficient notice", res["findings"][0].lower())

    def test_invalid_service_method(self):
        res = forecast_eviction_case(
            ground="sale",
            notice_date="2026-01-01",
            target_eviction_date="2027-01-15",
            notice_method="whatsapp_email"  # Dismissed by court!
        )
        self.assertFalse(res["viable"])
        self.assertIn("whatsapp", res["risks"][0].lower())


class TestUAEDDSEngine(unittest.TestCase):
    def test_valid_iban(self):
        iban = "AE07 0331 2345 6789 0123 456"
        res = validate_uae_iban(iban)
        self.assertTrue(res["valid"])
        self.assertEqual(res["bank_name"], "Emirates NBD")

    def test_invalid_iban_length(self):
        iban = "AE12345"
        res = validate_uae_iban(iban)
        self.assertFalse(res["valid"])

    def test_four_installment_schedule(self):
        res = generate_uaedds_schedule(
            annual_rent=120000,
            lease_start="2026-02-01",
            installments_count=4,
            tenant_name="Rashid Al-Nuaimi",
            landlord_name="Emaar PJSC",
            tenant_iban="AE070331234567890123456"
        )
        self.assertEqual(len(res["schedule"]), 4)
        self.assertEqual(res["per_installment_amount"], 30000.0)
        self.assertEqual(res["security_deposit_aed"], 6000.0)  # 5% for unfurnished
        self.assertIn("UAEDDS-EJARI-", res["mandate_reference"])


class TestServerV1Endpoints(unittest.TestCase):
    def test_smart_index_endpoint(self):
        body = {
            "building_name": "Downtown One",
            "area": "Downtown Dubai",
            "base_area_average": 120000,
            "current_unit_rent": 90000,
            "proposed_unit_rent": 105000,
            "specs": {"age_years": 3, "cooling_type": "chiller_free", "metro_distance_meters": 200}
        }
        status, data = route("POST", "/api/rera/smart-index", body)
        self.assertEqual(status, 200)
        self.assertIn("smart_benchmark_rent", data)

    def test_rdsc_endpoint(self):
        body = {
            "ground": "sale",
            "notice_date": "2026-01-01",
            "target_eviction_date": "2027-01-05",
            "notice_method": "notary_public"
        }
        status, data = route("POST", "/api/rdsc/evaluate", body)
        self.assertEqual(status, 200)
        self.assertTrue(data["viable"])

    def test_uaedds_endpoint(self):
        body = {
            "annual_rent": 80000,
            "lease_start": "2026-03-01",
            "installments_count": 4,
            "tenant_name": "Sarah Jenkins",
            "property_name": "Marina Crest · Unit 402"
        }
        status, data = route("POST", "/api/uaedds/schedule", body)
        self.assertEqual(status, 200)
        self.assertEqual(len(data["schedule"]), 4)


if __name__ == "__main__":
    unittest.main()
