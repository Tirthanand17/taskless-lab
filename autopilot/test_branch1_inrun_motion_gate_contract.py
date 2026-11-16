"""Per-app physical creative QA contract; zero uploads and no fake passes."""
from pathlib import Path
import unittest

class DirectRealMediaCreativeGateTests(unittest.TestCase):
    def test_each_narrated_real_app_job_runs_exact_pixel_audit(self):
        root=Path(__file__).resolve().parents[1]
        script=(root/".github/workflows/branch1-narrated-real-app-review.yml").read_text("utf8")
        assert script.count("matrix:")>=1
        self.assertIn("app: [calc, chrome]",script)
        self.assertIn("autopilot.branch1_short_motion_audit",script)
        self.assertIn("--mp4 \"/tmp/flowminute-b1-narrated-$DEMO_APP/NARRATED_REAL_APP_REVIEW_ONLY.mp4\"",script)
        self.assertIn("NARRATED_REAL_APP_PROVENANCE_NOT_RELEASE_APPROVED.json",script)
        self.assertIn('"/tmp/flowminute-b1-direct-pixel-$DEMO_APP"',script)
        self.assertIn("REAL_VISUAL_CREATIVE_REVIEW.json",script)
        self.assertIn("REAL_MOBILE_REVIEW_*.png",script)
        self.assertIn("REVIEW_CLIP_REJECTED_REAL_PIXELS",script)
        self.assertIn('report["visual_screening"]["high_risk_static_pacing"]',script)
        self.assertIn('report["publish_or_schedule_authorized"] is False',script)
        self.assertIn("raise SystemExit(1)",script)
        self.assertIn("REAL_PIXEL_SCREEN_PASSED_OWNER_WATCH_STILL_REQUIRED",script)
        self.assertNotIn("PUBLISH_ENABLED: \"true\"",script)

    def test_pixel_thresholds_still_fail_closed(self):
        root=Path(__file__).resolve().parents[1]
        visual=(root/"autopilot/branch1_short_motion_audit.py").read_text("utf8")
        for threshold in ("NEAR_STILL_DELTA=0.75",
                          "MAX_STATIC_SECONDS=3.0",
                          "MAX_STATIC_SHARE=.45",
                          "MIN_VISUAL_CONTRAST=9.0"):
            self.assertIn(threshold,visual)
        self.assertIn("high_risk_static_pacing",visual)

if __name__=="__main__":
    unittest.main()
