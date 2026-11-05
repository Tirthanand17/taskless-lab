"""No-network full GitHub workflow source inventory regressions."""
from pathlib import Path
from tempfile import TemporaryDirectory
import shutil
import unittest

from autopilot.phase5j_full_workflow_inventory import (
    EXPECTED, enumerate_workflows, SourceHold
)

ROOT=Path(__file__).resolve().parents[1]

def fixture():
    temp=TemporaryDirectory()
    root=Path(temp.name)
    out=root/".github"/"workflows"
    out.mkdir(parents=True)
    for name in EXPECTED:
        shutil.copy2(ROOT/".github"/"workflows"/name,out/name)
    return temp,root,out

class Phase5JWorkflowInventoryTests(unittest.TestCase):
    def test_exact_current_28_source_workflows(self):
        r=enumerate_workflows(ROOT)
        self.assertEqual(r["total_workflows"],28)
        self.assertTrue(r["workflow_source_set_exactly_reviewed"])
        self.assertTrue(r["source_guards_passed"],r["risk_codes"])
        self.assertEqual(r["risk_codes"],[])
        self.assertEqual(r["video_upload_workflows"],2)
        self.assertEqual(r["repo_write_workflows"],8)
        self.assertEqual(r["scheduled_research_workflows"],1)

    def test_only_two_youtube_video_upload_entrypoints_in_known_sources(self):
        result=enumerate_workflows(ROOT)
        uploads={x["name"] for x in result["workflows"]
                  if x["role"]=="YOUTUBE_UPLOAD_WRITER"}
        self.assertEqual(uploads,{"publish-youtube.yml","publish-artifact-youtube.yml"})

    def test_repo_write_edges_are_not_confused_with_youtube_upload(self):
        r=enumerate_workflows(ROOT)
        writers={x["name"] for x in r["workflows"] if x["has_repo_write"]}
        self.assertIn("qa-v6.yml",writers)
        self.assertIn("render-brand.yml",writers)
        self.assertIn("publish-youtube.yml",writers)
        self.assertNotIn("flowminute-cloud-scout.yml",writers)

    def test_no_static_claim_proves_live_variables_or_cloud_budget(self):
        r=enumerate_workflows(ROOT)
        for key in ("production_github_variables_read",
                    "production_environment_protection_read",
                    "real_cloudflare_writers_enumerated",
                    "account_wide_zero_spend_verified",
                    "production_migration_authorized",
                    "unattended_publishing_authorized",
                    "cloud_autopilot_ready"):
            self.assertFalse(r[key])
        self.assertEqual(r["production_d1_writes"],0)
        self.assertEqual(r["youtube_api_writes"],0)

    def test_tampering_publishing_guard_blocks_source_acceptance(self):
        temp,root,out=fixture()
        try:
            path=out/"publish-youtube.yml"
            path.write_text(path.read_text().replace(
                "vars.PUBLISH_ENABLED == 'true'","true"))
            r=enumerate_workflows(root)
            self.assertFalse(r["source_guards_passed"])
            self.assertIn("WORKFLOW_GUARDS_NOT_CONFIRMED",r["risk_codes"])
        finally:temp.cleanup()

    def test_new_unknown_workflow_flagged(self):
        temp,root,out=fixture()
        try:
            (out/"unknown-publisher.yml").write_text(
                "on:\n  workflow_dispatch:\njobs:\n  upload:\n    steps:\n      - run: python scripts/publish_youtube.py\n")
            r=enumerate_workflows(root)
            self.assertIn("WORKFLOW_SET_CHANGED_REQUIRES_REVIEW",r["risk_codes"])
            self.assertIn("UNEXPECTED_YOUTUBE_OWNER_ACCESS_IN_WORKFLOW",r["risk_codes"])
        finally:temp.cleanup()

    def test_deleted_workflow_blocks(self):
        temp,root,out=fixture()
        try:
            (out/"collect-metrics.yml").unlink()
            r=enumerate_workflows(root)
            self.assertIn("WORKFLOW_SET_CHANGED_REQUIRES_REVIEW",r["risk_codes"])
        finally:temp.cleanup()

    def test_new_scheduled_writer_flagged(self):
        temp,root,out=fixture()
        try:
            path=out/"publish-artifact-youtube.yml"
            path.write_text(path.read_text()+"\n  schedule:\n    - cron: '0 2 * * *'\n")
            r=enumerate_workflows(root)
            self.assertIn("SCHEDULED_WRITER_REQUIRES_REVIEW",r["risk_codes"])
        finally:temp.cleanup()

    def test_unexpected_youtube_secret_in_ordinary_render_is_flagged(self):
        temp,root,out=fixture()
        try:
            path=out/"render-long-001.yml"
            path.write_text(path.read_text()+"\n  PRIVATE_TOKEN: ${{ secrets.YOUTUBE_TOKEN_JSON }}\n")
            r=enumerate_workflows(root)
            self.assertIn("UNEXPECTED_YOUTUBE_OWNER_ACCESS_IN_WORKFLOW",r["risk_codes"])
        finally:temp.cleanup()

    def test_privileged_pr_target_writer_requires_review(self):
        temp,root,out=fixture()
        try:
            path=out/"publish-youtube.yml"
            path.write_text(path.read_text()+"\n  pull_request_target:\n")
            r=enumerate_workflows(root)
            self.assertIn("PR_TARGET_WRITE_PRIVILEGE_REQUIRES_REVIEW",r["risk_codes"])
        finally:temp.cleanup()

    def test_unreadable_or_missing_dir_rejected(self):
        with TemporaryDirectory() as empty:
            with self.assertRaises(SourceHold):
                enumerate_workflows(Path(empty))

    def test_non_path_repository_root_rejected(self):
        with self.assertRaises(SourceHold):
            enumerate_workflows(str(ROOT))

if __name__=="__main__":
    unittest.main()
