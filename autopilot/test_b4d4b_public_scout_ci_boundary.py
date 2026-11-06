"""B4d4b research-only cloud scout must not waste video minutes or leak RSS URLs."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
WORKFLOW=ROOT/".github/workflows/flowminute-cloud-scout.yml"


class PublicScoutCostAndPrivacyBoundary(unittest.TestCase):
    def setUp(self):
        self.source=WORKFLOW.read_text(encoding="utf8")

    def test_no_system_apt_no_video_model_no_paid_api(self):
        self.assertNotIn("sudo apt-get",self.source)
        self.assertNotIn("apt-get update",self.source)
        self.assertNotIn("npm install",self.source)
        self.assertNotIn("kokoro-onnx",self.source)
        self.assertNotIn("aws-actions/",self.source)
        self.assertIn("'cryptography>=46,<48'",self.source)

    def test_public_scout_runs_real_source_only_security_tests(self):
        for name in (
            "autopilot.test_daily_cloud_plan",
            "autopilot.test_evidence_probe",
            "autopilot.test_source_fetch_diagnostics_b4d3",
            "autopilot.test_arxiv_primary_feed_b4d4",
            "autopilot.test_daily_editorial_board",
            "autopilot.test_daily_evidence_bundle",
            "autopilot.test_independent_fact_review_gate",
        ):
            self.assertIn(name,self.source)

    def test_no_unverified_headline_or_link_ever_printed_into_public_log(self):
        self.assertNotIn('lead["title"]',self.source)
        self.assertNotIn('lead["url"]',self.source)
        self.assertNotIn('item.get("title"',self.source)
        self.assertNotIn('item.get("url"',self.source)
        self.assertNotIn("Source URL:",self.source)
        self.assertIn("B4D4B_SCOUT_COUNTS_ONLY",self.source)
        self.assertIn("rm -f out/scout-report.json",self.source)

    def test_still_run_original_github_only_scheduled_research_with_no_write_permissions(self):
        self.assertIn('cron: "15 13 * * *"',self.source)
        self.assertIn("permissions:\n  contents: read",self.source)
        self.assertIn("flowminute-public-scout-${{ github.event_name }}-${{ github.ref }}",self.source)
        self.assertIn("cancel-in-progress: ${{ github.event_name == 'pull_request' }}",self.source)
        self.assertIn("persist-credentials: false",self.source)
        self.assertIn("if: github.event_name != 'pull_request'",self.source)
        self.assertNotIn("secrets.",self.source)
        self.assertNotIn("id-token: write",self.source)
        self.assertNotIn("actions/upload-artifact",self.source)
        self.assertNotIn("youtube().",self.source)


if __name__=="__main__":
    unittest.main()
