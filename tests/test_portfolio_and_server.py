# Copyright (c) 2026 Sanjaydeep Gowrishankar. Licensed under the MIT License.

"""The portfolio analysis behind the 3D view, and the local API server."""

import datetime as dt
import http.client
import json
import threading
import unittest

from ejariflow.portfolio import analyse, expiry_band, load_sample
from ejariflow.server import make_server

PORTFOLIO = {"buildings": [{"id": "b1", "name": "Test Tower", "avg_rent": 100_000, "floors": 1, "units_per_floor": 3, "units": [
    {"unit": "101", "floor": 1, "index": 1, "occupied": True, "annual_rent": 80_000, "proposed_rent": 90_000, "lease_end": "2026-12-01"},
    {"unit": "102", "floor": 1, "index": 2, "occupied": True, "annual_rent": 80_000, "proposed_rent": 84_000, "lease_end": "2027-09-01"},
    {"unit": "103", "floor": 1, "index": 3, "occupied": False},
]}]}


class PortfolioTests(unittest.TestCase):
    def test_bands(self):
        self.assertEqual([expiry_band(d) for d in (-1, 0, 90, 91, 180, 181)], ["expired", "due_90", "due_90", "due_180", "due_180", "later"])

    def test_units_get_status_expiry_and_rent_checks(self):
        out = analyse(PORTFOLIO, today=dt.date(2026, 11, 16))
        t = out["totals"]
        self.assertEqual((t["units"], t["occupied"], t["vacant"], t["over_cap"], t["due_90"]), (3, 2, 1, 1, 1))
        self.assertEqual(t["occupancy_percent"], 66.7)
        u101, u102, u103 = out["buildings"][0]["units"]
        self.assertEqual((u101["status"], u101["days_to_expiry"]), ("over_cap", 15))
        self.assertEqual(u102["status"], "later")
        self.assertEqual(u103["status"], "vacant")

    def test_the_sample_portfolio_loads(self):
        out = analyse(load_sample())
        self.assertGreater(out["totals"]["units"], 100)


class ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = make_server("127.0.0.1", 0)
        cls.port = cls.srv.server_address[1]
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown(); cls.srv.server_close()

    def call(self, method, path, body=None, headers=None):
        c = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        h = {"Content-Type": "application/json", **(headers or {})}
        c.request(method, path, json.dumps(body) if body is not None else None, h)
        r = c.getresponse()
        data = r.read()
        return r.status, (json.loads(data) if r.getheader("Content-Type", "").startswith("application/json") else data)

    def test_rera_check(self):
        s, body = self.call("POST", "/api/rera/check", {"current_rent": 80000, "proposed_rent": 90000, "average_rent": 100000})
        self.assertEqual((s, body["compliant"], body["max_percent"]), (200, False, 5))
        self.assertEqual(self.call("POST", "/api/rera/check", {"current_rent": 0, "proposed_rent": 1, "average_rent": 1})[0], 400)

    def test_contract_audit(self):
        text = "Ejari Contract No: 0012026000123456\nAnnual Rent: AED 85,000\nSPECIAL CONDITIONS\n1. The rent shall increase by 10% on each renewal.\n"
        s, body = self.call("POST", "/api/contract/audit", {"text": text, "average_rent": 100000})
        self.assertEqual(s, 200)
        self.assertEqual(body["contract"]["annual_rent"], 85000)
        self.assertIn("ESCALATION_OVER_CAP", [f["code"] for f in body["audit"]["findings"]])

    def test_portfolio_and_page(self):
        s, body = self.call("GET", "/api/portfolio")
        self.assertEqual(s, 200)
        self.assertTrue(body["buildings"])
        s, page = self.call("GET", "/")
        self.assertEqual(s, 200)
        self.assertIn(b"EjariFlow", page)

    def test_other_sites_are_refused(self):
        self.assertEqual(self.call("GET", "/api/portfolio", headers={"Host": "evil.example"})[0], 403)
        s, _ = self.call("POST", "/api/rera/check", {"current_rent": 1, "proposed_rent": 1, "average_rent": 1},
                         headers={"Origin": "https://evil.example"})
        self.assertEqual(s, 403)


if __name__ == "__main__":
    unittest.main()
