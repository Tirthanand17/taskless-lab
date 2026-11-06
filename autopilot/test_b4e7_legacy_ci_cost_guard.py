"""B4e7 budget guard: retired real-video renders are manual, not PR/push.

GitHub Actions minutes and artifact storage are finite. New active science_v7
three-video proofs remain on trusted-main changed source. No GitHub credentials,
paid provider, external network or owner device are used by these tests.
"""
from __future__ import annotations

from pathlib import Path
import re
import unittest

REPO = Path(__file__).resolve().parents[1]
LEGACY = {
    ".github/workflows/flowminute-b4e3-cinematic-three-video-review.yml":
        "actually_render_review_2_shorts_and_one_long",
    ".github/workflows/flowminute-b4e4c-floating-three-video-review.yml":
        "actually_render_review_2_shorts_and_one_long",
    ".github/workflows/flowminute-b3d4c2c3b-full-original-narration.yml":
        "three_actual_complete_topic_specific_kokoro_mp4s",
    ".github/workflows/flowminute-b4e3d-one-real-aac-challenge.yml":
        "actual_cinematic_short_mp4_true_peak_limit_and_artifact",
}
MAIN_BRANCH = "github.ref == 'refs/heads/main'"
DISPATCH = "github.event_name == 'workflow_dispatch'"
OWNER = "github.repository == 'Tirthanand17/taskless-lab'"


def _yaml(path: str) -> str:
    src = REPO / path
    if not src.is_file() or src.is_symlink():
        raise ValueError("Missing reviewed Actions source file")
    return src.read_text(encoding="utf8")


def _job_body(src: str, job_name: str) -> str:
    start = re.search(r"(?m)^  " + re.escape(job_name) + r":\s*$", src)
    if start is None:
        raise ValueError("Missing expected retired CI job")
    tail = src[start.end():]
    end = re.search(r"(?m)^  [a-zA-Z_]\w*:\s*$", tail)
    return tail[:end.start()] if end is not None else tail


class LegacySourceOnlyBudgetProtectionTests(unittest.TestCase):
    def test_four_legacy_full_media_jobs_only_on_approved_manual_main(self):
        for path, job in LEGACY.items():
            with self.subTest(path=path):
                src = _yaml(path)
                body = _job_body(src, job)
                lines = re.findall(r"(?m)^    if:\s*(.+)$", body)
                self.assertEqual(len(lines), 1, "One literal branch/event condition required")
                policy = lines[0]
                for term in (OWNER, MAIN_BRANCH, DISPATCH):
                    self.assertIn(term, policy)
                self.assertNotIn("!=", policy)
                self.assertNotIn("pull_request_target", src)
                self.assertIn("  workflow_dispatch:", src)
                self.assertIn("permissions:\n  contents: read", src)
                self.assertNotIn("id-token: write", src)
                self.assertNotIn("secrets.", body)

    def test_original_two_research_variants_still_run_cheap_native_quality(self):
        for path in list(LEGACY)[:2]:
            with self.subTest(path=path):
                src = _yaml(path)
                cheap = _job_body(src, "native_before_after_visual_source_and_caption_integrity")
                self.assertIn("    if: " + OWNER,cheap)
                self.assertIn("python -B -m unittest -v",cheap)
                self.assertIn("autopilot.test_",cheap)
                self.assertIn("  pull_request:",src)
                self.assertIn("  push:",src)

    def test_original_full_voice_contract_still_runs_pr_provenance_tests(self):
        src=_yaml(".github/workflows/flowminute-b3d4c2c3b-full-original-narration.yml")
        cheap=_job_body(src,"topic_provenance_voice_and_animation_timing_contracts")
        self.assertIn("python -B -m unittest -v",cheap)
        self.assertIn("autopilot.test_full_topic_narrated_pack",cheap)
        self.assertIn("  pull_request:",src)

    def test_single_current_science_v7_main_video_proof_retained(self):
        active=_yaml(".github/workflows/flowminute-b4e6b-real-science-v7-three-video-review.yml")
        heavy=_job_body(active, "physically_encode_three_existing_science_demos")
        self.assertIn(MAIN_BRANCH,heavy)
        self.assertIn("github.event_name != 'pull_request'",heavy)
        self.assertIn("needs: [safe_source_and_original_scene_diff]",heavy)
        self.assertIn("retain_science_v7_three_v8",active)
        self.assertIn("permissions:\n  contents: read",active)
        self.assertIn("  push:\n    branches: [main]",active)
        self.assertNotIn("youtube().",active)
        self.assertNotIn("secrets.",heavy)

    def test_no_legacy_auto_publish_or_unbounded_money_flag(self):
        for path in LEGACY:
            with self.subTest(path=path):
                src=_yaml(path)
                self.assertNotIn("videos.insert",src)
                self.assertNotIn("aws ecs run-task",src)
                self.assertNotIn("id-token: write",src)
                self.assertIn('FLOWMINUTE_ENABLE_PUBLISH: "0"',src)
                self.assertIn('FLOWMINUTE_MODEL_PAID_SPEND_USD: "0"',src)
                self.assertIn('FLOWMINUTE_ALLOW_LAPTOP: "0"',src)


if __name__=="__main__":
    unittest.main()
