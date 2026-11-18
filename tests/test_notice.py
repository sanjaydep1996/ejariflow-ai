# Copyright (c) 2026 Sanjaydeep Gowrishankar. Licensed under the MIT License.

"""Unit tests for the bilingual 90-day renewal notice generator."""

import datetime as dt
import unittest
from ejariflow.notice import generate_90day_notice
from ejariflow.server import route


class TestNoticeGenerator(unittest.TestCase):
    def test_compliant_renewal_notice(self):
        # 100 days notice given
        today = dt.date.today()
        end_date = (today + dt.timedelta(days=100)).isoformat()

        res = generate_90day_notice(
            tenant="Ahmed Al-Mansoori",
            landlord="Emaar Properties PJSC",
            property_name="Marina Crest Tower",
            unit="1402",
            area="Dubai Marina",
            current_rent=80000.0,
            average_rent=100000.0,  # 20% gap -> 5% max increase (AED 84,000)
            lease_end_date=end_date,
            notice_date=today.isoformat(),
            ejari_number="2026-1049281",
        )

        self.assertEqual(res["status"], "generated")
        self.assertTrue(res["compliant"])
        self.assertTrue(res["on_time"])
        self.assertEqual(res["max_increase_percent"], 5)
        self.assertEqual(res["max_rent_allowed"], 84000.0)

        # Check English notice content
        self.assertIn("Ahmed Al-Mansoori", res["notice_en"])
        self.assertIn("Marina Crest Tower", res["notice_en"])
        self.assertIn("Dubai Decree No. 43 of 2013", res["notice_en"])
        self.assertIn("AED 84,000.00", res["notice_en"])

        # Check Arabic notice content
        self.assertIn("أحمد المنصوري" if "أحمد" in res["notice_ar"] else "Ahmed Al-Mansoori", res["notice_ar"])
        self.assertIn("المرسوم رقم (43) لسنة 2013", res["notice_ar"])
        self.assertIn("القانون رقم (26) لسنة 2007", res["notice_ar"])

    def test_late_notice_warning(self):
        # Only 60 days notice given (violates 90-day statutory rule)
        today = dt.date.today()
        end_date = (today + dt.timedelta(days=60)).isoformat()

        res = generate_90day_notice(
            tenant="John Smith",
            landlord="Dubai Asset Management",
            property_name="Downtown Views",
            unit="504",
            area="Downtown Dubai",
            current_rent=100000.0,
            average_rent=120000.0,
            lease_end_date=end_date,
            notice_date=today.isoformat(),
        )

        self.assertFalse(res["on_time"])
        self.assertIn("WARNING: Only 60 days notice provided", res["timing_warning"])
        self.assertIn("تنبيه: تم تقديم الإخطار قبل 60 يوماً فقط", res["timing_warning_ar"])

    def test_server_notice_route(self):
        code, body = route("POST", "/api/notice/generate", {
            "tenant": "Fatima Al-Zahra",
            "landlord": "Al Wasl Properties",
            "property_name": "Creek Residences",
            "unit": "802",
            "area": "Dubai Creek Harbour",
            "current_rent": 90000.0,
            "average_rent": 110000.0,
            "lease_end_date": (dt.date.today() + dt.timedelta(days=95)).isoformat(),
        })

        self.assertEqual(code, 200)
        self.assertEqual(body["status"], "generated")
        self.assertTrue(body["on_time"])
        self.assertIn("notice_en", body)
        self.assertIn("notice_ar", body)


if __name__ == "__main__":
    unittest.main()
