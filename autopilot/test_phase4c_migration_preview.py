"""Phase 4C synthetic metadata migration preview security regression tests."""
import unittest
from copy import deepcopy

from autopilot.core import CHANNEL_ID
from autopilot.phase4b_readonly_audit import AuditBlocked
from autopilot.phase4c_migration_preview import generate_migration_review_preview

SLOT = "2026-10-20T05:30:00+00:00"
VIDEO = "abc123def45"
SHA = "a"*64


def record(source="private_sqlite_claim", **overrides):
    value = {
        "source": source,
        "channel_id": CHANNEL_ID,
        "episode_id": "ep_01",
        "stage": "planned",
        "youtube_id": VIDEO,
        "media_sha256": SHA,
        "planned_utc": SLOT,
    }
    value.update(overrides)
    return value


def issues(*claims):
    report = generate_migration_review_preview(list(claims))
    return [c["issues"] for c in report["candidates"]]


class MigrationPreviewTests(unittest.TestCase):
    def test_empty_set_blocks_production_and_generates_no_sql(self):
        r = generate_migration_review_preview([])
        self.assertEqual(r["episode_count"], 0)
        self.assertFalse(r["production_migration_ready"])
        self.assertFalse(r["production_upload_ready"])
        self.assertEqual(r["generated_sql"], [])
        self.assertEqual(r["network_calls"], 0)
        self.assertEqual(r["database_mutations"], 0)

    def test_three_claimed_sources_agree_but_no_live_authority(self):
        r = generate_migration_review_preview([
            record("private_sqlite_claim", release_date="2026-10-20"),
            record("d1_claim"), record("youtube_claim")
        ])
        candidate = r["candidates"][0]
        self.assertEqual(candidate["issues"], [])
        self.assertEqual(candidate["resolution"],
                         "UNVERIFIED_CANDIDATE_REQUIRES_INDEPENDENT_REVIEW")
        self.assertTrue(candidate["operator_review_required"])
        self.assertIsNone(candidate["proposed_mutation"])
        self.assertFalse(r["trusted_live_evidence"])
        self.assertFalse(r["production_migration_ready"])

    def test_missing_d1_and_remote_claims_explicitly_block(self):
        item = issues(record())[0]
        self.assertIn("MISSING_LIVE_D1_METADATA_CLAIM", item)
        self.assertIn("MISSING_YOUTUBE_METADATA_CLAIM", item)

    def test_valid_legacy_ist_day_not_a_conflict(self):
        item = issues(record(release_date="2026-10-20"),
                      record("d1_claim"),record("youtube_claim"))[0]
        self.assertNotIn("LEGACY_IST_RELEASE_DAY_MISMATCH",item)

    def test_legacy_date_utc_day_is_not_assumed(self):
        # 20:00 UTC on October 20 is October 21 India time.
        later = "2026-10-20T20:00:00+00:00"
        item = issues(record(release_date="2026-10-20",planned_utc=later),
                      record("d1_claim",planned_utc=later),
                      record("youtube_claim",planned_utc=later))[0]
        self.assertIn("LEGACY_IST_RELEASE_DAY_MISMATCH",item)

    def test_legacy_date_without_remote_schedule_is_ambiguous(self):
        item = issues(record(release_date="2026-10-20",planned_utc=None))[0]
        self.assertIn("LEGACY_DATE_WITHOUT_EXACT_RELEASE_SLOT", item)

    def test_contradictory_legacy_days_detected(self):
        item = issues(record(release_date="2026-10-20"),
                      record("d1_claim",release_date="2026-10-21"))[0]
        self.assertIn("CONTRADICTORY_LEGACY_RELEASE_DAY", item)

    def test_unparseable_legacy_day_rejected(self):
        for wrong in ("20-10-2026","2026-02-31","2026-10-2",""):
            with self.subTest(wrong=wrong), self.assertRaises(AuditBlocked):
                generate_migration_review_preview([record(release_date=wrong)])

    def test_upload_started_after_crash_needs_reconciliation(self):
        item = issues(record(stage="upload_started"))[0]
        self.assertIn("UNCERTAIN_REMOTE_OPERATION_REQUIRES_RECONCILIATION", item)

    def test_scheduler_uncertainty_also_blocks(self):
        for stage in ("upload_uncertain","schedule_unresolved","schedule_uncertain"):
            with self.subTest(stage=stage):
                self.assertIn("UNCERTAIN_REMOTE_OPERATION_REQUIRES_RECONCILIATION",
                              issues(record(stage=stage))[0])

    def test_diverging_remote_and_local_stages_flagged(self):
        item = issues(record(stage="media_qa_passed"),
                      record("d1_claim",stage="upload_started"))[0]
        self.assertIn("DIVERGENT_STAGE_OBSERVATIONS",item)
        self.assertIn("UNCERTAIN_REMOTE_OPERATION_REQUIRES_RECONCILIATION",item)

    def test_public_versus_quarantine_claim_conflict(self):
        item = issues(record(stage="public_verified"),
                      record("d1_claim",stage="quarantined"))[0]
        self.assertIn("PUBLIC_VS_QUARANTINE_CONTRADICTION",item)

    def test_remote_stage_without_valid_video_id(self):
        item = issues(record(stage="scheduled_verified",youtube_id=None))[0]
        self.assertIn("REMOTE_STAGE_LACKS_EXACT_VIDEO_ID",item)
        self.assertIn("REMOTE_STATE_WITHOUT_VIDEO_ID",item)

    def test_remote_video_id_collision_cross_episode(self):
        claims = [record(),record("d1_claim",episode_id="ep_02",
                                  planned_utc="2026-10-21T05:30:00+00:00")]
        r = generate_migration_review_preview(claims)
        for candidate in r["candidates"]:
            self.assertIn("REMOTE_ID_SHARED_BY_DIFFERENT_EPISODES", candidate["issues"])

    def test_slot_collision_cross_episode(self):
        claims = [record(),record("d1_claim",episode_id="ep_02",youtube_id="def123abc45")]
        r = generate_migration_review_preview(claims)
        for candidate in r["candidates"]:
            self.assertIn("SLOT_SHARED_BY_DIFFERENT_EPISODES",candidate["issues"])

    def test_media_hash_conflict_retains_no_canonical_sha(self):
        r = generate_migration_review_preview([record(),record("d1_claim",media_sha256="b"*64)])
        self.assertIn("MEDIA_HASH_MISMATCH",r["candidates"][0]["issues"])
        self.assertIsNone(r["candidates"][0]["claimed_media_sha256"])

    def test_video_id_conflict_retains_no_canonical_id(self):
        r = generate_migration_review_preview([record(),record("d1_claim",youtube_id="def123abc45")])
        self.assertIn("REMOTE_VIDEO_ID_MISMATCH",r["candidates"][0]["issues"])
        self.assertIsNone(r["candidates"][0]["claimed_youtube_id"])

    def test_slot_conflict_retains_no_canonical_slot(self):
        r = generate_migration_review_preview([record(),record("d1_claim",
                             planned_utc="2026-10-20T06:30:00+00:00")])
        self.assertIn("SCHEDULE_SLOT_MISMATCH",r["candidates"][0]["issues"])
        self.assertIsNone(r["candidates"][0]["claimed_planned_utc"])

    def test_reordering_untrusted_claims_keeps_same_preview_digest(self):
        rows=[record("youtube_claim"),record("d1_claim"),
              record("public_draft_claim",episode_id="ep_02",
                     youtube_id="def123abc45",
                     planned_utc="2026-10-21T05:30:00+00:00")]
        first=generate_migration_review_preview(rows)
        second=generate_migration_review_preview(list(reversed(rows)))
        self.assertEqual(first["preview_sha256"],second["preview_sha256"])
        self.assertEqual(first["candidates"],second["candidates"])

    def test_secret_values_not_echoed_in_preview(self):
        secret="DO_NOT_LEAK_AES_GCM_CIPHERTEXT_123"
        r=generate_migration_review_preview([record(oauth_grant=secret,refresh_token=secret)])
        self.assertNotIn(secret,str(r))

    def test_wrong_channel_forged_remote_label_fails(self):
        with self.assertRaises(AuditBlocked):
            generate_migration_review_preview([record("youtube_claim",channel_id="wrong")])

    def test_invalid_media_metadata_fails(self):
        with self.assertRaises(AuditBlocked):
            generate_migration_review_preview([record(media_sha256="not_a_digest")])

    def test_bounds_and_nonlist_rejected(self):
        with self.assertRaises(AuditBlocked):
            generate_migration_review_preview([record()]*5001)
        with self.assertRaises(AuditBlocked):
            generate_migration_review_preview("not a list")

    def test_source_label_does_not_grant_remote_authentication(self):
        r=generate_migration_review_preview([record("d1_claim"),
                                             record("youtube_claim",
                                                    stage="public_verified")])
        self.assertFalse(r["trusted_live_evidence"])
        self.assertFalse(r["production_schedule_ready"])
        self.assertFalse(r["production_upload_ready"])
        self.assertIn("DIVERGENT_STAGE_OBSERVATIONS",r["candidates"][0]["issues"])


if __name__ == "__main__":
    unittest.main()
