from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import unittest

from job_radar.config import load_profile
from job_radar.models import Job
from job_radar.scoring import score_job


PROFILE = load_profile(Path(__file__).parents[1] / "config" / "profile.toml")
NOW = datetime(2026, 7, 14, tzinfo=timezone.utc)


def make_job(**overrides):
    base = dict(
        job_id="1", source="test", source_name="test", company="Company", external_id="1",
        title="Senior Growth Automation Manager", location="Remote Europe", workplace_type="remote",
        employment_type="Full-time", url="https://example.com/1", apply_url="https://example.com/1/apply",
        description="Own growth, CRM automation, lifecycle, acquisition funnels, analytics and partnerships for an AI SaaS company.",
        posted_at="2026-07-13T00:00:00Z", collected_at="2026-07-14T00:00:00Z",
    )
    base.update(overrides)
    return Job(**base)


class ScoringTests(unittest.TestCase):
    def test_growth_role_scores_high(self):
        ranked = score_job(make_job(), PROFILE, now=NOW)
        self.assertTrue(ranked.eligible)
        self.assertEqual("growth_automation", ranked.persona_key)
        self.assertGreaterEqual(ranked.score, 80)

    def test_us_only_is_blocked(self):
        ranked = score_job(make_job(location="United States only", workplace_type="hybrid",
                                    description="Must reside in the United States."), PROFILE, now=NOW)
        self.assertFalse(ranked.eligible)
        self.assertLessEqual(ranked.score, 25)
        self.assertTrue(ranked.gates)

    def test_internship_is_blocked(self):
        ranked = score_job(make_job(title="Marketing Internship", description="Unpaid internship"), PROFILE, now=NOW)
        self.assertFalse(ranked.eligible)


if __name__ == "__main__":
    unittest.main()
