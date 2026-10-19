"""Actual four-prompt integration: authored research -> 8 agent teams -> calendar.

All releases, metrics, human voice, rights and cloud deployment stay HOLD.
"""
from datetime import date
from hashlib import sha256
import json
import unittest

from autopilot.agent_org import CHANNEL_ID,WorkflowError
from autopilot.calendar import PublishingCalendar,CalendarError
from autopilot.four_prompt_autopilot_bridge import (
    staging_cycle_for_day,staging_cycle_json,HARD_PRODUCTION_BLOCKERS,
)


TODAY=date(2026,10,19)
PACK_DAY=date(2026,10,20)


class FourPromptBundleIntegrationTests(unittest.TestCase):
    def test_default_two_original_shorts_plus_one_long_no_extra(self):
        outcome=staging_cycle_for_day(PACK_DAY)
        self.assertEqual(outcome["status"],
            "BUNDLE_FOUR_PROMPTS_INTEGRATED_STAGING_NOT_LIVE_AUTOPILOT")
        self.assertEqual(outcome["channel_id"],CHANNEL_ID)
        self.assertEqual(outcome["timezone"],"Asia/Kolkata")
        self.assertEqual(outcome["calendar_draft_slots"],3)
        self.assertEqual(len(outcome["source_matched_original_episodes"]),3)
        self.assertEqual(outcome["source_missing_slots"],[])
        self.assertEqual(outcome["specialist_task_contracts"],54)
        org=outcome["master_agent"]
        self.assertEqual(org["departments"],8)
        self.assertEqual(org["specialists"],48)
        self.assertEqual(org["episodes_queued"],3)
        self.assertEqual(org["episodes_active"],3)
        self.assertEqual(org["ready_tasks"],3)
        self.assertFalse(org["uploads_enabled"])
        self.assertFalse(org["cloud_deployed"])
        self.assertEqual({x["owner"] for x in outcome["initial_ready_assignments"]},
                         {"research.launch_researcher"})
        expected={("short","en",42),("short","hi",44),("long","hi",480)}
        self.assertEqual(
            {(e["kind"],e["language"],e["duration_seconds"])
             for e in outcome["source_matched_original_episodes"]},expected)

    def test_multiple_shot_families_only_for_current_two_short_scripts(self):
        obj=staging_cycle_for_day(PACK_DAY)
        shots=[x for x in obj["source_matched_original_episodes"]
               if x["kind"]=="short"]
        self.assertEqual(len(shots),2)
        for episode in shots:
            visual=episode["visual_style_plan"]
            self.assertEqual(visual["unique_subjects"],7)
            self.assertEqual(visual["digital_scenes"],3)
            self.assertEqual(visual["mesh_or_hybrid_scenes"],4)
            self.assertFalse(visual["release_approved"]
                if "release_approved" in visual else
                visual["youtube_upload_authorized"])
            self.assertFalse(episode["authentic_human_narration_verified"])
            self.assertFalse(episode["full_hd_media_verified"])
        long=[x for x in obj["source_matched_original_episodes"]
              if x["kind"]=="long"]
        self.assertEqual(len(long),1)
        self.assertIsNone(long[0]["visual_style_plan"])
        self.assertFalse(long[0]["long_full_hybrid_visuals_rendered"])

    def test_all_four_original_prompt_requirements_tracked_without_false_approval(self):
        obj=staging_cycle_for_day(PACK_DAY)
        self.assertEqual(len(obj["bundles_applied"]),4)
        self.assertEqual(obj["pending_production_gates"],list(HARD_PRODUCTION_BLOCKERS))
        self.assertEqual(len(obj["pending_production_gates"]),6)
        for field in (
            "verified_engagement_analytics_loaded",
            "audience_data_fabricated",
            "estimated_srt_promoted_to_real_asr",
            "visual_3d_preview_is_final_movie",
            "real_human_or_model_voice_accepted",
            "authenticated_youtube_receipts_used",
            "real_upload_scheduling_or_publication_performed",
            "cloud_deployment_performed","new_external_service_connected",
            "accessed_nirala","paid_resources_used",
        ):
            self.assertIs(obj[field],False)
        self.assertEqual(obj["monthly_recurring_budget_inr"],0)

    def test_pause_tomorrow_generates_no_content_or_agent_tasks(self):
        c=PublishingCalendar()
        c.apply("Pause all videos tomorrow",today=TODAY)
        obj=staging_cycle_for_day(PACK_DAY,calendar=c)
        self.assertEqual(obj["calendar_draft_slots"],0)
        self.assertEqual(obj["source_matched_original_episodes"],[])
        self.assertEqual(obj["source_missing_slots"],[])
        self.assertEqual(obj["specialist_task_contracts"],0)
        self.assertEqual(obj["master_agent"]["episodes_active"],0)
        self.assertFalse(obj["real_upload_scheduling_or_publication_performed"])

    def test_demand_more_content_than_authored_creates_hold_not_filler(self):
        c=PublishingCalendar()
        c.apply("Tomorrow upload 6 Shorts and 3 long videos",today=TODAY)
        outcome=staging_cycle_for_day(PACK_DAY,calendar=c)
        self.assertEqual(outcome["calendar_draft_slots"],9)
        self.assertEqual(len(outcome["source_matched_original_episodes"]),3)
        self.assertEqual(len(outcome["source_missing_slots"]),6)
        self.assertTrue(all(row["status"]=="NO_ORIGINAL_SOURCE_EPISODE_HOLD"
                            for row in outcome["source_missing_slots"]))
        self.assertEqual(outcome["specialist_task_contracts"],54)
        self.assertFalse(outcome["real_upload_scheduling_or_publication_performed"])

    def test_future_unresearched_day_cannot_reuse_the_oct20_video(self):
        outcome=staging_cycle_for_day(date(2026,10,21))
        self.assertEqual(outcome["calendar_draft_slots"],3)
        self.assertEqual(outcome["source_matched_original_episodes"],[])
        self.assertEqual(len(outcome["source_missing_slots"]),3)
        self.assertEqual(outcome["master_agent"]["episodes_queued"],0)

    def test_authenticated_utc_reservations_can_block_proposed_slots(self):
        original=staging_cycle_for_day(PACK_DAY)
        planned=original["source_matched_original_episodes"][0]["calendar_utc"]
        with self.assertRaises(CalendarError):
            staging_cycle_for_day(
                PACK_DAY,existing_reserved_utc=(planned,))
        after=staging_cycle_for_day(PACK_DAY)
        self.assertEqual(original,after)

    def test_json_manifest_is_exactly_reproducible_and_safe(self):
        raw=staging_cycle_json(PACK_DAY)
        self.assertEqual(raw,staging_cycle_json(PACK_DAY))
        obj=json.loads(raw)
        self.assertEqual(obj,staging_cycle_for_day(PACK_DAY))
        self.assertNotIn("refresh_token",raw)
        self.assertNotIn("access_token",raw)
        self.assertNotIn("private_key",raw)
        self.assertNotIn("videos.insert",raw)
        self.assertEqual(obj["monthly_recurring_budget_inr"],0)

    def test_real_cli_prints_draft_manifest_and_obeys_pause(self):
        from contextlib import redirect_stdout
        from io import StringIO
        from autopilot.four_prompt_autopilot_bridge import main
        standard=StringIO()
        with redirect_stdout(standard):
            self.assertEqual(main(["--day","2026-10-20"]),0)
        data=json.loads(standard.getvalue())
        self.assertEqual(data["calendar_draft_slots"],3)
        self.assertFalse(data["real_upload_scheduling_or_publication_performed"])

        paused=StringIO()
        with redirect_stdout(paused):
            self.assertEqual(main([
                "--day","2026-10-20",
                "--today","2026-10-19",
                "--calendar-command","Pause all videos tomorrow",
            ]),0)
        halted=json.loads(paused.getvalue())
        self.assertEqual(halted["calendar_draft_slots"],0)
        self.assertEqual(halted["specialist_task_contracts"],0)

    def test_real_cli_invalid_instruction_exits_without_fake_success(self):
        from contextlib import redirect_stderr
        from io import StringIO
        from autopilot.four_prompt_autopilot_bridge import main
        with redirect_stderr(StringIO()):
            with self.assertRaises(SystemExit):
                main(["--day","2026-10-20",
                      "--today","2026-10-19",
                      "--calendar-command","Publish everything immediately"])

    def test_reject_datetime_and_malformed_user_provided_metadata(self):
        from datetime import datetime
        for wrong in (None,datetime(2026,10,20,8,30),"2026-10-20",True):
            with self.subTest(day=str(wrong)),self.assertRaises(WorkflowError):
                staging_cycle_for_day(wrong)
        with self.assertRaises(WorkflowError):
            staging_cycle_for_day(PACK_DAY,existing_reserved_utc=[123])
        with self.assertRaises(WorkflowError):
            staging_cycle_for_day(PACK_DAY,calendar="fake scheduler")


if __name__=="__main__":
    unittest.main()
