"""No-network tests for the future cloud-only 48-agent daily planner.

All tests run on disposable GitHub runners; never use Nirala, YouTube OAuth,
Cloudflare credentials or real publishing APIs.
"""
import datetime as dt
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from autopilot.agent_org import MasterOrchestrator, ROLES
from autopilot.daily_cloud_plan import (
    APPROVED_RESEARCH_ORIGINS,
    IST,
    PlanError,
    build_plan,
    candidate_leads,
    next_research_day,
    parse_day_ist,
)

UTC = dt.timezone.utc


def sample_report():
    return {
        "status": "leads_only_no_publish_authorization",
        "leads": [
            {"publisher": "OpenAI", "title": "Technical tutorial on agent task scheduling",
             "url": "https://openai.com/news/research", "status": "unverified_lead"},
            {"publisher": "Google DeepMind", "title": "Research on evaluation of responsible AI tools",
             "url": "https://deepmind.google/blog/responsible-research/",
             "status": "unverified_lead"},
            {"publisher": "The Verge", "title": "The practical changes in new browser permissions",
             "url": "https://www.theverge.com/tech/browser-permissions",
             "status": "unverified_lead"},
        ],
    }


class DailyCloudPlanTests(unittest.TestCase):
    def setUp(self):
        self.clock = dt.datetime(2026, 11, 4, 4, 0, tzinfo=UTC)

    def test_exact_three_daily_release_slots_and_types(self):
        result = build_plan("2026-11-05", generated_at_utc=self.clock)
        self.assertTrue(result["all_three_release_slots"])
        self.assertEqual([x["format"] for x in result["slots"]], ["short", "long", "short"])
        self.assertEqual([x["local_ist"] for x in result["slots"]], ["11:00", "16:00", "20:30"])
        self.assertEqual([x["release_utc"] for x in result["slots"]],
                         ["2026-11-05T05:30:00+00:00", "2026-11-05T10:30:00+00:00",
                          "2026-11-05T15:00:00+00:00"])
        self.assertEqual(len({x["episode_id"] for x in result["slots"]}), 3)

    def test_reuses_existing_eight_department_48_role_three_episode_orchestrator(self):
        result = build_plan("2026-11-05", generated_at_utc=self.clock)
        self.assertEqual(len(ROLES), 48)
        self.assertEqual(result["departments"], 8)
        self.assertEqual(result["specialist_roles"], 48)
        self.assertEqual(result["task_contracts"], 54)
        self.assertEqual(len(result["slots"][0]["required_handoffs"]), 18)
        self.assertEqual(result["slots"][0]["required_handoffs"][0],
                         "fm_20261105_short_am:research")
        self.assertIn("fm_20261105_long:release_review",
                      result["slots"][1]["required_handoffs"])

    def test_global_release_flags_and_all_content_gates_fail_closed(self):
        result = build_plan("2026-11-05", generated_at_utc=self.clock)
        for field in ("approved_provider_credentials_connected", "cloud_media_renderer_connected",
                      "production_release_ledger_connected", "cloud_publisher_connected",
                      "youtube_upload_enabled", "youtube_schedule_enabled",
                      "any_content_verified", "new_billable_resources_enabled"):
            self.assertIs(result[field], False, field)
        self.assertEqual(result["maximum_incremental_spend_inr"], 0)
        for slot in result["slots"]:
            for key in ("real_script_exists", "real_narration_exists", "real_media_exists",
                        "rights_approved", "real_media_qa_passed", "youtube_uploaded",
                        "youtube_scheduled", "release_authorized"):
                self.assertIs(slot[key], False, key)
            self.assertEqual(slot["agent_handoffs_completed"], 0)
            self.assertEqual(slot["status"], "BLOCKED_PENDING_RESEARCH_FACT_CHECK_AND_REAL_MEDIA")

    def test_primary_research_leads_are_never_fact_verified(self):
        result = build_plan("2026-11-05", scout_report=sample_report(), generated_at_utc=self.clock)
        self.assertEqual(result["research_lead_count"], 3)
        self.assertEqual([x["research_lead"]["publisher"] for x in result["slots"]],
                         ["OpenAI", "Google DeepMind", "The Verge"])
        for slot in result["slots"]:
            self.assertEqual(slot["editorial_state"], "UNVERIFIED_LEAD_ONLY")
            self.assertIs(slot["research_lead"]["fact_checked"], False)
            self.assertIs(slot["research_lead"]["video_ready"], False)
            self.assertIs(slot["youtube_upload_enabled"], False) if "youtube_upload_enabled" in slot else None

    def test_draft_without_source_leads_does_not_invent_topics(self):
        result = build_plan("2026-11-05", scout_report={
            "status": "leads_only_no_publish_authorization", "leads": []},
            generated_at_utc=self.clock)
        self.assertEqual(result["research_lead_count"], 0)
        for slot in result["slots"]:
            self.assertIsNone(slot["research_lead"])
            self.assertEqual(slot["editorial_state"], "RESEARCH_REQUIRED")

    def test_elevated_scout_status_is_rejected(self):
        for value in ("verified", "facts_approved", "release_ready", None, True):
            with self.subTest(value=value), self.assertRaises(PlanError):
                candidate_leads({"status": value, "leads": []})

    def test_invalid_reports_fail_closed(self):
        for report in ("untrusted", {}, [], None, {"status": "leads_only_no_publish_authorization"},
                       {"status": "leads_only_no_publish_authorization", "leads": "unbounded"},
                       {"status": "leads_only_no_publish_authorization", "leads": [{}] * 1001}):
            with self.subTest(report=type(report).__name__), self.assertRaises(PlanError):
                candidate_leads(report)

    def test_non_https_wrong_publisher_and_embedded_credentials_dropped(self):
        payload = sample_report()
        payload["leads"].extend([
            {"publisher": "OpenAI", "title": "Valid looking bad external link",
             "url": "https://evil.example/other", "status": "unverified_lead"},
            {"publisher": "OpenAI", "title": "Wrong scheme is not accepted",
             "url": "http://openai.com/test", "status": "unverified_lead"},
            {"publisher": "OpenAI", "title": "Embedded password is not accepted",
             "url": "https://user:secret@openai.com/test", "status": "unverified_lead"},
            {"publisher": "unknown", "title": "Unknown publisher cannot be promoted",
             "url": "https://openai.com/test", "status": "unverified_lead"},
            {"publisher": "The Verge", "title": "Source marked approved is untrusted",
             "url": "https://www.theverge.com/x", "status": "approved"},
        ])
        self.assertEqual(len(candidate_leads(payload)), 3)

    def test_duplicate_lead_is_removed(self):
        payload = sample_report()
        payload["leads"].append(dict(payload["leads"][0]))
        self.assertEqual(len(candidate_leads(payload)), 3)

    def test_research_publisher_origins_are_explicit(self):
        self.assertIn("OpenAI", APPROVED_RESEARCH_ORIGINS)
        self.assertNotIn("Other AI", APPROVED_RESEARCH_ORIGINS)
        self.assertEqual(len(APPROVED_RESEARCH_ORIGINS), 4)
        self.assertEqual(APPROVED_RESEARCH_ORIGINS["arXiv AI"], {"arxiv.org"})

    def test_wrong_channel_is_rejected(self):
        with self.assertRaises(PlanError):
            build_plan("2026-11-05", channel_id="UCwrong", generated_at_utc=self.clock)

    def test_invalid_dates_rejected(self):
        for day in ("tomorrow", "2026-1-5", "2026-11-32", "2026-13-01", "2026-11-05T00:00Z",
                    "2026/11/05", None, 20261105):
            with self.subTest(day=day), self.assertRaises(PlanError):
                parse_day_ist(day)

    def test_naive_clock_rejected(self):
        naive = dt.datetime(2026, 11, 4, 10, 0)
        with self.assertRaises(PlanError):
            next_research_day(naive)
        with self.assertRaises(PlanError):
            build_plan("2026-11-05", generated_at_utc=naive)

    def test_planning_tomorrow_uses_ist_not_utc(self):
        clock = dt.datetime(2026, 11, 4, 21, 0, tzinfo=UTC)
        self.assertEqual(clock.astimezone(IST).day, 5)
        self.assertEqual(next_research_day(clock), "2026-11-06")

    def test_cli_writes_nonpublishing_plan_on_disposable_runner(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            infile = root / "scout.json"
            outfile = root / "next-day.json"
            infile.write_text(json.dumps(sample_report()), encoding="utf-8")
            command = [sys.executable, "-m", "autopilot.daily_cloud_plan",
                       "--date", "2026-11-05", "--scout-report", str(infile),
                       "--output", str(outfile)]
            result = subprocess.run(command, text=True, capture_output=True, timeout=15)
            self.assertEqual(result.returncode, 0, result.stderr)
            result_json = json.loads(outfile.read_text(encoding="utf-8"))
            self.assertEqual(len(result_json["slots"]), 3)
            self.assertIs(result_json["youtube_upload_enabled"], False)
            self.assertEqual(json.loads(result.stdout)["uploads_enabled"], False)


if __name__ == "__main__":
    unittest.main()
