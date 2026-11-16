# Copyright (c) 2026 Sanjaydeep Gowrishankar. Licensed under the MIT License.

"""RERA rent increase caps (Dubai Decree No. 43 of 2013) and the notice rules around them."""

import datetime as dt
import unittest

from ejariflow.rera import allowed_increase, check_increase, check_renewal_notice, check_eviction_notice


class AllowedIncreaseTests(unittest.TestCase):
    def test_the_five_bands_of_decree_43(self):
        # (current rent, average rent for similar units) -> maximum increase %
        cases = [
            (100_000, 100_000, 0),    # at the average
            (95_000, 100_000, 0),     # 5% below
            (90_000, 100_000, 0),     # exactly 10% below: still no increase
            (89_000, 100_000, 5),     # 11% below
            (80_000, 100_000, 5),     # 20% below
            (75_000, 100_000, 10),    # 25% below
            (70_000, 100_000, 10),    # 30% below
            (65_000, 100_000, 15),    # 35% below
            (60_000, 100_000, 15),    # 40% below
            (55_000, 100_000, 20),    # 45% below
            (120_000, 100_000, 0),    # above the average
        ]
        for current, average, pct in cases:
            self.assertEqual(allowed_increase(current, average)["max_percent"], pct, (current, average))

    def test_bad_input_is_refused(self):
        for current, average in ((0, 100_000), (100_000, 0), (-5, 10)):
            with self.assertRaises(ValueError):
                allowed_increase(current, average)


class CheckIncreaseTests(unittest.TestCase):
    def test_a_compliant_increase(self):
        r = check_increase(current_rent=80_000, proposed_rent=84_000, average_rent=100_000)
        self.assertTrue(r["compliant"])
        self.assertEqual((r["max_percent"], r["max_rent"], r["proposed_percent"]), (5, 84_000, 5.0))

    def test_an_increase_over_the_cap(self):
        r = check_increase(current_rent=80_000, proposed_rent=90_000, average_rent=100_000)
        self.assertFalse(r["compliant"])
        self.assertEqual(r["excess"], 6_000)
        self.assertIn("5%", r["reason"])

    def test_no_increase_allowed_near_the_average(self):
        r = check_increase(current_rent=95_000, proposed_rent=96_000, average_rent=100_000)
        self.assertFalse(r["compliant"])
        self.assertEqual(r["max_rent"], 95_000)

    def test_a_decrease_is_always_fine(self):
        self.assertTrue(check_increase(current_rent=95_000, proposed_rent=90_000, average_rent=100_000)["compliant"])


class NoticeTests(unittest.TestCase):
    def test_renewal_changes_need_90_days_notice(self):
        end = dt.date(2027, 3, 31)
        self.assertTrue(check_renewal_notice(notice_date=dt.date(2026, 12, 31), contract_end=end)["compliant"])   # 90 days
        late = check_renewal_notice(notice_date=dt.date(2027, 1, 15), contract_end=end)
        self.assertFalse(late["compliant"])
        self.assertEqual(late["days_given"], 75)

    def test_eviction_for_sale_or_own_use_needs_12_months(self):
        end = dt.date(2027, 6, 30)
        ok = check_eviction_notice(notice_date=dt.date(2026, 6, 30), contract_end=end, reason="sale")
        self.assertTrue(ok["compliant"])
        short = check_eviction_notice(notice_date=dt.date(2026, 9, 1), contract_end=end, reason="own_use")
        self.assertFalse(short["compliant"])
        self.assertIn("12 months", short["reason"])
        with self.assertRaises(ValueError):
            check_eviction_notice(notice_date=dt.date(2026, 1, 1), contract_end=end, reason="because")


if __name__ == "__main__":
    unittest.main()
