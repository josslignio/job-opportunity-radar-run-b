from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
import tempfile
import unittest

from job_radar.pipeline import run_pipeline


ROOT = Path(__file__).parents[1]


class PipelineTests(unittest.TestCase):
    def test_offline_pipeline_creates_auditable_report(self):
        with tempfile.TemporaryDirectory() as temp:
            manifest = run_pipeline(
                profile_path=str(ROOT / "config" / "profile.toml"),
                sources_path=str(ROOT / "tests" / "fixtures" / "sources.toml"),
                runtime_root=temp,
                fixture_dir=str(ROOT / "tests" / "fixtures"),
                allow_network=False,
                now=datetime(2026, 7, 14, 12, 0, tzinfo=timezone.utc),
            )
            run_dir = Path(temp) / "runs" / manifest["run_id"]
            self.assertEqual("completed", manifest["status"])
            self.assertEqual(5, manifest["counts"]["raw_jobs"])
            self.assertEqual(5, manifest["counts"]["deduplicated_jobs"])
            self.assertTrue((run_dir / "report.html").exists())
            self.assertTrue((run_dir / "ranked.jsonl").exists())
            self.assertEqual(0, manifest["incremental_api_cost_usd"])
            self.assertFalse(manifest["automatic_application"])
            ranked = [json.loads(line) for line in (run_dir / "ranked.jsonl").read_text().splitlines()]
            self.assertTrue(any(row["persona_key"] == "crypto_affiliate_bd" for row in ranked))
            self.assertTrue(any(not row["eligible"] for row in ranked))


if __name__ == "__main__":
    unittest.main()
