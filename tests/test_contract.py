# Copyright (c) 2026 Sanjaydeep Gowrishankar. Licensed under the MIT License.

"""Reading a tenancy contract into fields, and auditing its clauses."""

import json
import pathlib
import unittest

from ejariflow.audit import audit_contract
from ejariflow.contract import parse_contract

SAMPLE = (pathlib.Path(__file__).resolve().parent.parent / "data" / "sample-contract.txt").read_text(encoding="utf-8")


class ParseTests(unittest.TestCase):
    def test_the_key_fields_are_read(self):
        c = parse_contract(SAMPLE)
        self.assertEqual(c["ejari_number"], "0012026000123456")
        self.assertEqual(c["landlord"], "Al Noor Properties LLC")
        self.assertEqual(c["tenant"], "Test Tenant One")
        self.assertEqual(c["property"]["unit"], "1204")
        self.assertEqual(c["property"]["building"], "Marina Crest Tower")
        self.assertEqual(c["property"]["area"], "Dubai Marina")
        self.assertEqual(c["annual_rent"], 85_000)
        self.assertEqual(c["security_deposit"], 4_250)
        self.assertEqual((c["start_date"], c["end_date"]), ("2026-04-01", "2027-03-31"))
        self.assertEqual(c["payments"]["cheques"], 4)
        self.assertEqual(c["language"], "en")

    def test_arabic_digits_and_labels_are_understood(self):
        text = "رقم إيجاري: ٠٠١٢٠٢٦٠٠٠٦٥٤٣٢١\nالإيجار السنوي: ٩٠٬٠٠٠ درهم\nتاريخ البدء: 01/05/2026\nتاريخ الانتهاء: 30/04/2027\n"
        c = parse_contract(text)
        self.assertEqual(c["ejari_number"], "0012026000654321")
        self.assertEqual(c["annual_rent"], 90_000)
        self.assertEqual((c["start_date"], c["end_date"]), ("2026-05-01", "2027-04-30"))
        self.assertEqual(c["language"], "ar")

    def test_missing_fields_are_listed_not_guessed(self):
        c = parse_contract("This is not a tenancy contract.")
        self.assertIsNone(c["annual_rent"])
        self.assertIn("ejari_number", c["missing"])
        json.dumps(c)


class AuditTests(unittest.TestCase):
    def test_clauses_that_break_rera_rules_are_flagged(self):
        report = audit_contract(parse_contract(SAMPLE), average_rent=100_000)
        codes = {f["code"] for f in report["findings"]}
        self.assertIn("ESCALATION_OVER_CAP", codes)         # the contract allows a 10% yearly rise; the cap here is 5%
        self.assertIn("EVICTION_NOTICE_TOO_SHORT", codes)   # 60 days' notice for own use instead of 12 months
        self.assertIn("RENEWAL_NOTICE_TOO_SHORT", codes)    # changes on 30 days' notice instead of 90
        self.assertFalse(report["compliant"])
        self.assertTrue(all(f["rule"] for f in report["findings"]))

    def test_a_clean_contract_passes(self):
        clean = SAMPLE.split("SPECIAL CONDITIONS")[0]
        report = audit_contract(parse_contract(clean), average_rent=100_000)
        self.assertTrue(report["compliant"], report["findings"])


if __name__ == "__main__":
    unittest.main()
