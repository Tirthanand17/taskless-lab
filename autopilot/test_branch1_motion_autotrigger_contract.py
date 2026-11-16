"""Source contract for an automatic, nonpublishing, exact-video creative gate.

A green codec job is not audience- or creative-QA success. The separate
pixel auditor must reject a real static video without a permissive fallback.
"""
from pathlib import Path
import unittest

class MotionAutotriggerContract(unittest.TestCase):
    def test_real_video_auto_audit_not_one_off_manual_check(self):
        root=Path(__file__).resolve().parents[1]
        flow=(root/".github/workflows/branch1-short-motion-audit.yml").read_text("utf8")
        self.assertIn("workflow_run:",flow)
        self.assertIn('workflows: ["FlowMinute B1 Narrated Real-App Shorts Review (NO YOUTUBE)"]',flow)
        self.assertIn("types: [completed]",flow)
        self.assertIn("github.event.workflow_run.event == 'workflow_dispatch'",flow)
        self.assertIn("github.event.workflow_run.head_branch == 'main'",flow)
        self.assertIn("github.event.workflow_run.conclusion == 'success'",flow)
        self.assertIn("github.event.workflow_run.name == 'FlowMinute B1 Narrated Real-App Shorts Review (NO YOUTUBE)'",flow)
        self.assertIn("github.event.workflow_run.id || inputs.source_run_id",flow)
        self.assertIn('r["conclusion"]=="success"',flow)
        self.assertIn('r["event"]=="workflow_dispatch"',flow)
        self.assertIn('r["headBranch"]=="main"',flow)
        self.assertIn("source_run_id:",flow)   # manual recheck still possible
        self.assertIn("raise SystemExit(1)",flow)
        self.assertIn('["high_risk_static_pacing"]',flow)
        self.assertIn("actions: read",flow)
        self.assertNotIn("PUBLISH_ENABLED: \"true\"",flow)
        self.assertNotIn("FLOWMINUTE_ENABLE_PUBLISH: \"1\"",flow)

    def test_strict_motion_heuristics_unchanged(self):
        root=Path(__file__).resolve().parents[1]
        code=(root/"autopilot/branch1_short_motion_audit.py").read_text("utf8")
        for exact in ("NEAR_STILL_DELTA=0.75", "MAX_STATIC_SECONDS=3.0",
                      "MAX_STATIC_SHARE=.45", "MIN_VISUAL_CONTRAST=9.0",
                      "CROP=\"crop=860:1100:110:175"):
            self.assertIn(exact,code)
        self.assertIn("Pixel motion alone cannot prove a good hook",code)

if __name__=="__main__":
    unittest.main()
