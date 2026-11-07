"""B4g6 regression: actual source checks are not owner or YouTube evidence."""
from __future__ import annotations
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
import unittest

from autopilot.project_phase_acceptance_audit_b4g6 import (
    RUBRIC, NO_EXTERNAL_EVIDENCE,PhaseAuditRefused,
    inspect_source_acceptance,rubric_snapshot,
)

ROOT=Path(__file__).resolve().parents[1]


class StrictEvidenceAcceptanceAuditTests(unittest.TestCase):
    def test_current_merged_repo_source_safety_gates_independently_inspected(self):
        result=inspect_source_acceptance(ROOT)
        self.assertTrue(result["all_source_acceptance_gates_present"],
                        [k for k,v in result["checks"].items() if not v])
        self.assertEqual(result["checks_passed"],result["checks_total"])
        self.assertEqual(result["checks_total"],12)
        for name in (
            "main_branch_latest_real_three_video_run_status",
            "current_owner_youtube_oauth_status",
            "current_branch1_schedule_state",
            "actual_human_reviews_verified",
            "actual_unattended_real_youtube_publications",
        ):
            self.assertEqual(result[name],NO_EXTERNAL_EVIDENCE)
        self.assertIn("SOURCE_CONTRACT_AUDIT_ONLY",result["status"])

    def test_weighted_production_readiness_not_confused_with_engineering_or_uploads(self):
        score=rubric_snapshot()
        self.assertEqual(sum(row["weight"] for row in score["categories"]),100)
        self.assertEqual(sum(row["earned"] for row in score["categories"]),45)
        self.assertEqual(sum(row["remaining"] for row in score["categories"]),55)
        self.assertEqual(score["overall_production_readiness_estimate_percent"],45)
        self.assertEqual(score["overall_remaining_estimate_percent"],55)
        self.assertEqual(score["real_seven_day_unattended_release_target"],21)
        self.assertEqual(score["real_seven_day_unattended_releases_independently_verified"],0)
        self.assertTrue(score["engineering_progress_not_the_same_metric"])
        self.assertEqual(score["categories"][5]["earned"],0)
        self.assertEqual(score["categories"][6]["earned"],0)

    def test_source_gates_do_not_claim_live_oauth_or_verified_21_releases(self):
        src=(ROOT/"autopilot/project_phase_acceptance_audit_b4g6.py").read_text("utf8")
        for dangerous in ("googleapiclient.discovery","youtube.videos().insert",
                          "requests.post(","remote_api_token","credential.refresh(",
                          "GenUI.openUrl"):
            self.assertNotIn(dangerous,src)
        self.assertIn("NOT_ESTABLISHED_BY_SOURCE_INSPECTION",src)

    def test_removed_protected_manual_publish_gate_is_reported_as_failed_not_live(self):
        # A pure temporary source clone, no network, no GitHub mutation.
        required=(
            ".github/workflows/flowminute-daily-cloud-foundation.yml",
            ".github/workflows/publish-artifact-youtube.yml",
            ".github/workflows/flowminute-owner-readonly-channel-audit-b4f6.yml",
            "autopilot/agent_org.py","autopilot/daily_cloud_plan.py",
            "autopilot/full_original_rehearsal_media_b4e1.py",
            "autopilot/verified_aac_mastering_b4g5.py",
            "autopilot/encoded_aac_loudness_review_b4g4.py",
            "autopilot/offline_review_portal_b4e7.py",
            "scripts/publish_youtube.py",
            "scripts/owner_signed_release_b4f1.py",
            "autopilot/branch1_nov_repair_inventory.py",
        )
        with TemporaryDirectory() as tmp:
            root=Path(tmp)
            for relative in required:
                target=root/relative
                target.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(ROOT/relative,target)
            path=root/".github/workflows/publish-artifact-youtube.yml"
            source=path.read_text("utf8")
            self.assertIn("environment: youtube-production",source)
            path.write_text(source.replace(
                "environment: youtube-production",
                "environment: unprotected-publishing"),encoding="utf8")
            result=inspect_source_acceptance(root)
            self.assertFalse(result["all_source_acceptance_gates_present"])
            self.assertFalse(result["checks"][
                "manual_publisher_protected_and_disabled_by_default"])
            self.assertEqual(
                result["actual_unattended_real_youtube_publications"],
                NO_EXTERNAL_EVIDENCE)

    def test_missing_repo_file_or_relative_symlink_rejected(self):
        with TemporaryDirectory() as temporary:
            root=Path(temporary)
            with self.assertRaises(PhaseAuditRefused):
                inspect_source_acceptance(root)
        with self.assertRaises(PhaseAuditRefused):
            inspect_source_acceptance(Path("/path/that-is-not-a-repo"))


if __name__=="__main__":
    unittest.main()
