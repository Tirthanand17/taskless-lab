"""CLIVOX V2 P11 adversarial rights, capacity, originality and scale denial."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts.branch3_v2_p11_synthetic_scale_readiness import (
    BLOCKERS, CHANNEL, EXPECTED_WEEK_START, FIXTURE, P11Denied, RESULT_FIELDS,
    SOURCE_CATEGORIES, STAGE,
    closed_a10_and_p9, evaluate_source_free_p11,
    production_scale_or_contact, read_synthetic_fixture, validate_fixture,
    validate_report, weekly_slots,
)


def plan():
    return read_synthetic_fixture()


def report():
    return evaluate_source_free_p11(plan())


class P11SyntheticScaleTests(unittest.TestCase):
    def test_genuine_closed_rights_and_existing_analytics_not_connected(self):
        closed_a10_and_p9()
        with self.assertRaises(P11Denied):
            production_scale_or_contact()
        with self.assertRaises(P11Denied):
            production_scale_or_contact(
                creator="synthetic creator", upload=True, contact=True)

    def test_weekly_two_shorts_one_long_workload_is_illustrative(self):
        d = plan()
        self.assertEqual(d["channel_id"], CHANNEL)
        self.assertEqual(d["hypothetical_week_start_utc"], EXPECTED_WEEK_START)
        self.assertEqual(d["hypothetical_daily_targets"], {
            "shorts": 2, "long_form": 1})
        self.assertEqual(d["actual_committed_editor_minutes_per_week"], 0)
        self.assertEqual(d["hypothetical_available_editor_minutes_per_week"], 1200)
        out = report()
        self.assertEqual(out["stage"], STAGE)
        self.assertEqual(set(out), RESULT_FIELDS)
        self.assertEqual(out["hypothetical_target_shorts"], 14)
        self.assertEqual(out["hypothetical_target_long_videos"], 7)
        self.assertEqual(out["hypothetical_total_assets"], 21)
        self.assertEqual(out["hypothetical_editor_minutes_demand"], 2590)
        self.assertEqual(out["hypothetical_editor_hours_demand"], 43.167)
        self.assertEqual(out["hypothetical_editor_capacity_gap_minutes"], 1390)
        self.assertEqual(out["authorized_production_capacity_assets"], 0)
        self.assertEqual(out["real_licensed_source_files"], 0)
        self.assertEqual(out["actual_committed_editor_minutes"], 0)
        self.assertFalse(out["production_ready"])
        self.assertFalse(out["real_p11_milestone_complete"])
        self.assertEqual(validate_report(out), out)

    def test_weekly_slots_are_hypothetical_and_no_youtube_schedule(self):
        slots = weekly_slots(plan())
        self.assertEqual(len(slots), 7)
        self.assertEqual(slots[0]["hypothetical_date_utc"], "2027-03-01")
        self.assertEqual(slots[-1]["hypothetical_date_utc"], "2027-03-07")
        for i, day in enumerate(slots):
            self.assertEqual(day["day"], i + 1)
            self.assertEqual(day["target_shorts"], 2)
            self.assertEqual(day["target_long_videos"], 1)
            self.assertEqual(day["real_authorized_shorts"], 0)
            self.assertEqual(day["real_authorized_long_videos"], 0)
            self.assertEqual(day["actual_scheduled_youtube_uploads"], 0)
            self.assertFalse(day["human_context_review_completed"])
            self.assertFalse(day["rights_renewal_confirmed"])

    def test_source_categories_are_research_only_uncontacted_and_not_license(self):
        out = report()
        self.assertEqual(out["research_only_category_count"], 3)
        self.assertEqual([c["category"]
                          for c in out["source_category_hold_register"]],
                         list(SOURCE_CATEGORIES))
        self.assertEqual(out["verified_creator_partnerships"], 0)
        self.assertEqual(out["minimum_creator_partnerships_required"], 2)
        self.assertEqual(out["real_creator_outreach_messages_sent"], 0)
        self.assertEqual(out["real_source_downloads"], 0)
        self.assertEqual(out["actual_youtube_uploads"], 0)
        for row in out["source_category_hold_register"]:
            self.assertTrue(row["research_only_no_creator_contact"])
            self.assertFalse(row["verified_commercial_reuse_license"])
            self.assertFalse(row["reviewed_original_storytelling"])
            self.assertFalse(row["production_source_access_allowed"])
        self.assertEqual(out["blockers"], list(BLOCKERS))
        self.assertEqual(len(out["blockers"]), 10)

    def test_copyright_license_not_monetization_and_fake_virality_blocked(self):
        r = report()
        self.assertTrue(r["no_monetization_or_viral_predictions_made"])
        self.assertTrue(r["creative_editorial_novelty_review_required"])
        self.assertTrue(r["copyright_license_does_not_equal_ypp_approval"])
        for k in (
            "reused_content_ypp_safety_independently_verified",
            "youtube_partner_monetization_guaranteed",
            "human_originality_reviewed",
            "real_license_rights_current",
            "copyright_clearance_complete",
            "cross_creator_automatic_reupload_enabled",
            "public_youtube_scheduler_enabled",
            "owner_exact_video_release_signed",
            "live_clivox_upload_oauth_verified",
            "real_owned_analytics_observed",
            "youtube_publish_authorized",
        ):
            self.assertFalse(r[k])
        text = json.dumps(r)
        for unsafe in (
            "creator_email", "youtube.com/watch?", "private_key",
            "access_token", "revenue_estimate", "predicted_viral_views",
        ):
            self.assertNotIn(unsafe, text)

    def test_forged_rights_owner_keys_staffing_and_uploads_rejected(self):
        baseline = plan()
        mutations = (
            ("verified_rightsholder_agreements", 2),
            ("confirmed_licensed_source_media_files", 1),
            ("actual_committed_editor_minutes_per_week", 2500),
            ("approved_private_source_vault", True),
            ("real_editorial_owner_review_signatures", 1),
            ("real_publish_approved_videos", 5),
            ("live_clivox_upload_oauth_connected", True),
            ("live_analytics_evidence_connected", True),
            ("confirmed_youtube_monetization_eligibility", True),
            ("actual_creator_outreach_messages_sent", 2),
            ("actual_media_downloads", 1),
            ("actual_youtube_uploads", 1),
            ("synthetic", False),
            ("hypothetical_week_start_utc", "2026-11-14T00:00:00Z"),
            ("channel_id", "UCCcL9Q_jqVq6LJmnYUSAFZA"),
            ("execution_mode", "ACTUAL_CLIPPING_PRODUCTION"),
            ("expected_decision", "APPROVED"),
            ("minimum_distinct_creator_partnerships_before_scale", 0),
        )
        for field, value in mutations:
            d = copy.deepcopy(baseline)
            d[field] = value
            with self.subTest(field=field), self.assertRaises(P11Denied):
                validate_fixture(d)

    def test_mass_output_and_template_only_flag_denied(self):
        keys = (
            "requires_substantive_original_commentary",
            "requires_human_licensed_source_context_review",
            "requires_current_rights_and_revocation_recheck_per_video",
            "requires_no_misleading_claims_or_unoriginal_template_reuploads",
        )
        for field in keys:
            d = plan()
            d[field] = False
            with self.subTest(field=field), self.assertRaises(P11Denied):
                validate_fixture(d)
        for field, value in (
            ("shorts", 20), ("long_form", 3),
        ):
            d = plan()
            d["hypothetical_daily_targets"][field] = value
            with self.subTest(field=field), self.assertRaises(P11Denied):
                validate_fixture(d)
        for field, value in (
            ("shorts_edit", 1), ("shorts_originality_and_rights_review", 0),
            ("long_edit", 1), ("long_originality_and_rights_review", 0),
        ):
            d = plan()
            d["human_minutes_per_item"][field] = value
            with self.subTest(field=field), self.assertRaises(P11Denied):
                validate_fixture(d)

    def test_fake_synthetic_creator_cases_are_rejected(self):
        baseline = plan()
        for index in range(3):
            for field, value in (
                ("rights_state", "LICENSED"),
                ("commercial_youtube_derivatives_licensed", True),
                ("human_context_originality_reviewed", True),
                ("guest_music_game_rights_verified", True),
                ("source_media_delivered", True),
                ("category", "unknown_creator"),
            ):
                d = copy.deepcopy(baseline)
                d["source_research_cases"][index][field] = value
                with self.subTest(index=index, field=field), self.assertRaises(P11Denied):
                    validate_fixture(d)
        d = plan()
        d["source_research_cases"][0]["creator_email"] = "private@example.test"
        with self.assertRaises(P11Denied):
            validate_fixture(d)
        d = plan()
        d["source_research_cases"].reverse()
        with self.assertRaises(P11Denied):
            validate_fixture(d)

    def test_false_real_capacity_and_ypp_claim_in_report_rejected(self):
        fields = (
            ("verified_creator_partnerships", 2),
            ("real_licensed_source_files", 1),
            ("actual_editorial_signed_reviews", 4),
            ("actual_committed_editor_minutes", 1200),
            ("real_owned_analytics_observed", True),
            ("real_source_downloads", 1),
            ("actual_youtube_uploads", 1),
            ("authorized_production_capacity_assets", 3),
            ("production_ready", True),
            ("real_recurring_clip_scale_enabled", True),
            ("real_license_rights_current", True),
            ("human_originality_reviewed", True),
            ("reused_content_ypp_safety_independently_verified", True),
            ("youtube_partner_monetization_guaranteed", True),
            ("cross_creator_automatic_reupload_enabled", True),
            ("public_youtube_scheduler_enabled", True),
            ("approved_private_media_vault_verified", True),
            ("owner_exact_video_release_signed", True),
            ("youtube_publish_authorized", True),
            ("real_p11_milestone_complete", True),
            ("hypothetical_editor_minutes_demand", 200),
            ("hypothetical_total_assets", 100),
            ("hypothetical_editor_capacity_gap_minutes", 0),
            ("no_monetization_or_viral_predictions_made", False),
        )
        for field, value in fields:
            edited = report()
            edited[field] = value
            with self.subTest(field=field), self.assertRaises(P11Denied):
                validate_report(edited)

    def test_no_promoted_schedule_and_license_supply_in_report(self):
        d = report()
        d["hypothetical_weekly_slots"][0]["actual_scheduled_youtube_uploads"] = 1
        with self.assertRaises(P11Denied):
            validate_report(d)
        d = report()
        d["hypothetical_weekly_slots"][0]["human_context_review_completed"] = True
        with self.assertRaises(P11Denied):
            validate_report(d)
        d = report()
        d["source_category_hold_register"][0]["verified_commercial_reuse_license"] = True
        with self.assertRaises(P11Denied):
            validate_report(d)
        d = report()
        d["blockers"].pop()
        with self.assertRaises(P11Denied):
            validate_report(d)
        d = report()
        d["creator_private_contact"] = "email"
        with self.assertRaises(P11Denied):
            validate_report(d)

    def test_extra_config_key_cannot_override_production_block(self):
        for key, value in (
            ("youtube_write_enabled", True),
            ("creator_has_approved", True),
            ("force_release", True),
            ("private_media_path", "/tmp/private_movie.mp4"),
        ):
            d = plan()
            d[key] = value
            with self.subTest(key=key), self.assertRaises(P11Denied):
                validate_fixture(d)

    def test_only_fixed_repository_source_fixture_not_external_uploads(self):
        with tempfile.TemporaryDirectory() as tmp:
            local = Path(tmp) / "fake-capacity.json"
            local.write_text(json.dumps(plan()))
            with self.assertRaises(P11Denied):
                read_synthetic_fixture(local)
        self.assertEqual(read_synthetic_fixture(FIXTURE), plan())

    def test_a10_p9_rights_hold_refusal_before_any_plan(self):
        with patch(
            "scripts.branch3_v2_p11_synthetic_scale_readiness.closed_a10_and_p9",
            side_effect=P11Denied("P10_OR_P9_REAL_OWNER_NOT_APPROVED"),
        ):
            with self.assertRaises(P11Denied):
                validate_fixture(plan())
        # An unknown or incomplete value is NOT treated as 0 supply.
        d = plan()
        d["verified_rightsholder_agreements"] = None
        with self.assertRaises(P11Denied):
            evaluate_source_free_p11(d)

    def test_deterministic_with_original_fixture_and_no_external_api(self):
        self.assertEqual(report(),
                         evaluate_source_free_p11(copy.deepcopy(plan())))
        self.assertEqual(report()["source"],
                         "FIXED_ORIGINAL_SOURCE_FREE_WEEKLY_CAPACITY_FIXTURE")


if __name__ == "__main__":
    unittest.main()
