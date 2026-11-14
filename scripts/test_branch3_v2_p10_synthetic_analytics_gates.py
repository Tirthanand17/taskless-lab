"""Adversarial P10 YouTube Analytics provenance tests: ZERO real user data."""
from __future__ import annotations

import copy
from datetime import datetime, timezone
import json
import unittest
from unittest.mock import patch

from scripts.branch3_a10_analytics import (
    POLICY, FIXTURE, METRICS, read_json,
)
from scripts.branch3_v2_p10_synthetic_analytics_gates import (
    CHANNEL, CATEGORIES, P10Denied, REPORT_FIELDS, STAGE,
    WINDOW_HOURS, PUBLISH_EXAMPLE, REQUIRED_METRICS,
    closed_a10_and_p9, hypothetical_checkpoints,
    source_free_p10_report, synthetic_metric_availability,
    synthetic_review_groups, validate_report,
)


def fixture():
    return read_json(FIXTURE)


def policy():
    return read_json(POLICY)


def report():
    return source_free_p10_report(fixture(), policy())


class P10SourceFreeAnalyticsTests(unittest.TestCase):
    def test_real_analytics_and_upload_policy_stay_closed(self):
        closed_a10_and_p9()
        r = report()
        self.assertEqual(set(r), REPORT_FIELDS)
        self.assertEqual(r["stage"], STAGE)
        self.assertEqual(r["channel_id"], CHANNEL)
        self.assertTrue(r["synthetic_fixture_only"])
        self.assertTrue(r["original_a10_offline_schema_validated"])
        self.assertTrue(r["p9_closed_rights_and_upload_gate_verified"])
        self.assertTrue(r["a10_owner_only_readonly_adapter_policy_respected"])
        self.assertEqual(r["real_google_requests"], 0)
        self.assertEqual(r["real_published_videos_observed"], 0)
        self.assertEqual(r["youtube_uploads"], 0)
        for field in (
            "real_analytics_oauth_verified", "real_clivox_metrics_observed",
            "live_owner_analytics_connected", "public_report_exposes_private_video_ids",
            "creator_analytics_requested", "video_or_creator_ranking_performed",
            "public_api_derived_viral_score", "copyright_or_ypp_status_inferred",
            "retention_curve_verified", "shorts_feed_stayed_to_watch_verified",
            "synthetic_metrics_extrapolated_as_real",
            "cross_owner_metric_aggregation_performed",
            "experiment_causal_winner_declared",
            "auto_optimization_or_publication_authorized",
            "real_analysis_milestone_complete", "youtube_publish_authorized",
        ):
            with self.subTest(field=field):
                self.assertFalse(r[field])
        self.assertEqual(validate_report(r), r)

    def test_no_private_video_ids_analytics_numbers_or_tokens_exported(self):
        r = report()
        output = json.dumps(r, sort_keys=True)
        raw = fixture()
        for video in raw["video_annotations"]:
            self.assertNotIn(video["video_id"], output)
        for secret in ("refresh_token", "client_secret", "Authorization",
                       "access_token", "Bearer ", "youtube.com/watch",
                       "creator_video_url", "viral_probability"):
            self.assertNotIn(secret, output)
        self.assertNotIn("average_views_per_1000", output)
        self.assertNotIn("median_shares_per_1000_engaged", output)
        self.assertNotIn("median_subs_gained_per_1000_engaged", output)

    def test_synthetic_metric_availability_only_no_real_values(self):
        r = report()
        self.assertEqual(r["hypothetical_record_count"], 12)
        self.assertEqual([m["metric"] for m in r["metric_provenance"]],
                         list(REQUIRED_METRICS))
        self.assertEqual(list(METRICS), list(REQUIRED_METRICS))
        for metric in r["metric_provenance"]:
            self.assertEqual(metric["source"], "SYNTHETIC_A10_API_SHAPE_NOT_REAL")
            self.assertIsNone(metric["real_clivox_value"])
            self.assertFalse(metric["can_infer_short_swipe_behaviour"])
            self.assertFalse(metric["safe_for_cross_creator_comparison"])
            self.assertEqual(metric["fixture_reported_value_count"] +
                             metric["fixture_missing_value_count"], 12)

    def test_missing_api_metric_is_null_not_inferred_from_views(self):
        dataset = fixture()
        header_names = [h["name"] for h in dataset[
            "analytics_api_response"]["columnHeaders"]]
        idx = header_names.index("engagedViews")
        dataset["analytics_api_response"]["rows"][0][idx] = None
        output = source_free_p10_report(dataset, policy())
        engaged = [m for m in output["metric_provenance"]
                   if m["metric"] == "engagedViews"][0]
        self.assertEqual(engaged["fixture_missing_value_count"], 1)
        self.assertIsNone(engaged["real_clivox_value"])
        self.assertFalse(output["shorts_feed_stayed_to_watch_verified"])
        self.assertTrue(all(x is None for x in
                            output["studio_only_metrics"].values()))

    def test_stayed_to_watch_retention_and_feed_metric_never_fabricated(self):
        self.assertEqual(report()["studio_only_metrics"], {
            "stayed_to_watch_percent": None,
            "shown_in_feed": None,
            "shorts_audience_retention_curve": None,
        })
        for field, fake in (
            ("stayed_to_watch_percent", 78.9),
            ("shown_in_feed", 12000),
            ("shorts_audience_retention_curve", [100, 80, 60]),
        ):
            mutated = copy.deepcopy(report())
            mutated["studio_only_metrics"][field] = fake
            with self.subTest(field=field), self.assertRaises(P10Denied):
                validate_report(mutated)
        for field, fake in (
            ("shown_in_feed", 9999),
            ("chose_to_view_pct", 93.1),
            ("audience_retention_curve", [100, 90]),
        ):
            dataset = fixture()
            dataset["studio_metrics"][field] = fake
            with self.subTest(field=field), self.assertRaises(P10Denied):
                source_free_p10_report(dataset, policy())

    def test_experiment_cohorts_only_test_counts_no_causal_claim(self):
        groups = report()["synthetic_cohort_review"]
        self.assertEqual(sum(x["fixture_hook_A_count"] +
                             x["fixture_hook_B_count"] for x in groups), 12)
        self.assertTrue(all(x["category"] in CATEGORIES for x in groups))
        self.assertTrue(all(x["minimum_examples_per_arm"] == 10 for x in groups))
        self.assertTrue(all(x["real_video_samples"] == 0 for x in groups))
        self.assertTrue(all(x["experiment_randomized"] is False for x in groups))
        self.assertTrue(all(x["causal_winner_declared"] is False for x in groups))
        self.assertTrue(all(not x["real_editorial_optimization_authorized"]
                            for x in groups))
        self.assertFalse(report()["experiment_causal_winner_declared"])

    def test_even_sufficient_synthetic_cohort_has_no_real_winner(self):
        rows = [
            {"category": "gaming", "hook_variant": "A"}
            for _ in range(15)
        ] + [
            {"category": "gaming", "hook_variant": "B"}
            for _ in range(15)
        ]
        groups = synthetic_review_groups(rows, threshold=10)
        self.assertEqual((groups[0]["fixture_hook_A_count"],
                          groups[0]["fixture_hook_B_count"]), (15, 15))
        self.assertFalse(groups[0]["experiment_randomized"])
        self.assertFalse(groups[0]["causal_winner_declared"])
        self.assertEqual(groups[0]["real_video_samples"], 0)

    def test_checkpoint_schedule_is_hypothetical_not_real_or_automated(self):
        rows = hypothetical_checkpoints()
        self.assertEqual([x["hours_after_hypothetical_publish"] for x in rows],
                         list(WINDOW_HOURS))
        self.assertEqual([x["hypothetical_checkpoint_utc"] for x in rows], [
            "2027-02-02T00:00:00Z", "2027-02-04T00:00:00Z",
            "2027-02-08T00:00:00Z", "2027-02-15T00:00:00Z",
        ])
        for row in rows:
            for field in (
                "real_video_publish_time_verified",
                "real_authenticated_snapshot_received",
                "youtube_data_availability_confirmed",
                "owner_editorial_review_completed",
                "performance_conclusion_allowed",
            ):
                self.assertFalse(row[field])
        for other in (
            datetime(2027,2,2,tzinfo=timezone.utc),
            datetime(2026,11,14,tzinfo=timezone.utc),
            "2027-02-01T00:00:00Z",
        ):
            with self.subTest(other=str(other)), self.assertRaises(P10Denied):
                hypothetical_checkpoints(template_publish_at=other)
        self.assertEqual(PUBLISH_EXAMPLE.year, 2027)

    def test_wrong_channel_fake_live_data_or_2026_fixture_rejected(self):
        changes = (
            ("channel_id", "UCCcL9Q_jqVq6LJmnYUSAFZA"),
            ("source_kind", "ACTUAL_CLIVOX_OAUTH_DATA"),
            ("synthetic", False),
            ("hypothetical_observation_date", "2026-11-14"),
            ("window_days", 30),
        )
        for name, value in changes:
            d = fixture()
            d[name] = value
            with self.subTest(name=name), self.assertRaises(P10Denied):
                source_free_p10_report(d, policy())

    def test_forbidden_platform_metrics_and_cross_owner_rows_denied(self):
        for change, value in (
            ("name", "viral_velocity_score"),
            ("name", "mostReplayed"),
            ("name", "stayed_to_watch_pct"),
        ):
            d = fixture()
            d["analytics_api_response"]["columnHeaders"][1][change] = value
            with self.subTest(value=value), self.assertRaises(P10Denied):
                source_free_p10_report(d, policy())
        d = fixture()
        d["analytics_api_response"]["rows"][0][0] = "SOMEOTHER42"
        with self.assertRaises(P10Denied):
            source_free_p10_report(d, policy())
        d = fixture()
        d["analytics_api_response"]["ownerExternalReport"] = {}
        with self.assertRaises(P10Denied):
            source_free_p10_report(d, policy())

    def test_report_laundering_real_metrics_viral_claim_or_owner_grant_denied(self):
        r = report()
        falsifications = (
            ("real_google_requests", 1),
            ("real_published_videos_observed", 1),
            ("real_analytics_oauth_verified", True),
            ("real_clivox_metrics_observed", True),
            ("youtube_uploads", 1),
            ("youtube_publish_authorized", True),
            ("shorts_feed_stayed_to_watch_verified", True),
            ("public_api_derived_viral_score", True),
            ("video_or_creator_ranking_performed", True),
            ("copyright_or_ypp_status_inferred", True),
            ("cross_owner_metric_aggregation_performed", True),
            ("auto_optimization_or_publication_authorized", True),
            ("experiment_causal_winner_declared", True),
            ("synthetic_fixture_only", False),
            ("hypothetical_record_count", True),
        )
        for field, value in falsifications:
            candidate = copy.deepcopy(r)
            candidate[field] = value
            with self.subTest(field=field), self.assertRaises(P10Denied):
                validate_report(candidate)

    def test_modified_metric_provenance_and_cohort_count_denied(self):
        for field, value in (
            ("real_clivox_value", 120),
            ("can_infer_short_swipe_behaviour", True),
            ("safe_for_cross_creator_comparison", True),
            ("source", "YOUTUBE_REAL"),
            ("fixture_missing_value_count", 123456),
            ("fixture_reported_value_count", True),
        ):
            r = report()
            r["metric_provenance"][0][field] = value
            with self.subTest(field=field), self.assertRaises(P10Denied):
                validate_report(r)
        for field, value in (
            ("causal_winner_declared", True),
            ("experiment_randomized", True),
            ("real_video_samples", 20),
            ("real_editorial_optimization_authorized", True),
            ("fixture_hook_A_count", -1),
            ("category", "unknown"),
        ):
            r = report()
            r["synthetic_cohort_review"][0][field] = value
            with self.subTest(field=field), self.assertRaises(P10Denied):
                validate_report(r)
        r = report()
        r["fictional_monetization_estimate"] = "$999"
        with self.assertRaises(P10Denied):
            validate_report(r)

    def test_modified_checkpoint_or_fake_observation_denied(self):
        for field, value in (
            ("hypothetical_checkpoint_utc", "2026-11-14T00:00:00Z"),
            ("hours_after_hypothetical_publish", 1),
            ("real_authenticated_snapshot_received", True),
            ("youtube_data_availability_confirmed", True),
            ("performance_conclusion_allowed", True),
        ):
            item = report()
            item["hypothetical_review_checkpoints"][0][field] = value
            with self.subTest(field=field), self.assertRaises(P10Denied):
                validate_report(item)

    def test_p9_and_a10_owner_policy_gate_cannot_be_promoted(self):
        with patch(
            "scripts.branch3_v2_p10_synthetic_analytics_gates._closed_live_policies",
            side_effect=P10Denied("P9_RIGHTS_OR_YOUTUBE_WRITE_ENABLED")
        ), self.assertRaises(P10Denied):
            closed_a10_and_p9()
        with patch(
            "scripts.branch3_v2_p10_synthetic_analytics_gates.fixture_report",
            return_value={
                "stage": "A10_OWNER_LIVE",
                "channel_id": CHANNEL, "actual_google_requests": 1,
                "real_clivox_video_metrics_observed": True,
            },
        ), self.assertRaises(P10Denied):
            closed_a10_and_p9()
        p = policy()
        p["live_api_enabled"] = True
        with self.assertRaises(P10Denied):
            source_free_p10_report(fixture(), p)
        p = policy()
        p["analytics_scope"] = "https://www.googleapis.com/auth/youtube.upload"
        with self.assertRaises(P10Denied):
            source_free_p10_report(fixture(), p)

    def test_output_is_deterministic_and_not_ranked(self):
        self.assertEqual(report(), source_free_p10_report(
            copy.deepcopy(fixture()), copy.deepcopy(policy())))
        self.assertEqual(report()["source_kind"],
                         "OFFLINE_A10_SYNTHETIC_METRIC_SHAPE_ONLY")
        self.assertFalse(report()["video_or_creator_ranking_performed"])


if __name__ == "__main__":
    unittest.main()
