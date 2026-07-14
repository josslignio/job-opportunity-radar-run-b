from __future__ import annotations

import json
from pathlib import Path
import unittest

from job_radar.collectors import COLLECTORS
from job_radar.models import SourceConfig


FIXTURES = Path(__file__).parent / "fixtures"


class CollectorTests(unittest.TestCase):
    def test_greenhouse(self):
        payload = json.loads((FIXTURES / "fixture-greenhouse.json").read_text())
        source = SourceConfig("fixture-greenhouse", "greenhouse", "AI Systems Europe", "fixture")
        jobs = COLLECTORS["greenhouse"].parse(source, payload, "2026-07-14T00:00:00Z")
        self.assertEqual(2, len(jobs))
        self.assertEqual("Senior AI Implementation Manager — Europe", jobs[0].title)
        self.assertIn("AI workflow", jobs[0].description)

    def test_lever(self):
        payload = json.loads((FIXTURES / "fixture-lever.json").read_text())
        source = SourceConfig("fixture-lever", "lever", "Crypto Exchange Labs", "fixture", instance="eu")
        jobs = COLLECTORS["lever"].parse(source, payload, "2026-07-14T00:00:00Z")
        self.assertEqual(2, len(jobs))
        self.assertEqual("remote", jobs[0].workplace_type)
        self.assertIn("EUR", jobs[0].compensation)

    def test_ashby_skips_unlisted(self):
        payload = json.loads((FIXTURES / "fixture-ashby.json").read_text())
        source = SourceConfig("fixture-ashby", "ashby", "Growth Automation Cloud", "Fixture")
        jobs = COLLECTORS["ashby"].parse(source, payload, "2026-07-14T00:00:00Z")
        self.assertEqual(1, len(jobs))
        self.assertEqual("Head of Growth Automation", jobs[0].title)


if __name__ == "__main__":
    unittest.main()
