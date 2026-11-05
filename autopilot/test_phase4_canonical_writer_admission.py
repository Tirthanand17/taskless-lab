"""Major Phase4 canonical one-way reservation simulation regressions."""
import json
import sqlite3
import unittest
from autopilot.phase4_canonical_writer_admission import (
    CHANNEL,UnsafeReservation,_database,_slot_index_verified,rehearse,
)
def receipt():
    return {
        "release_date":"2026-10-20",
        "slot_ist":"long",
        "episode_id":"fm_20261020_long_hi",
        "channel_id":CHANNEL,
        "publish_at_utc":"2026-10-20T10:30:00Z",
        "media_sha256":"a"*64
    }
class CanonicalSingleUseReservationTests(unittest.TestCase):
    def test_actual_nonunique_index_is_not_sufficient(self):
        out=rehearse(receipt(),unique_slot=False)
        self.assertEqual(out["decision"],"HOLD_DATE_SLOT_UNIQUENESS_NOT_PROVEN")
        self.assertEqual(out["simulated_release_state"],"MEDIA_QA_PASSED")
        self.assertEqual(out["simulated_event_rows"],0)

    def test_unique_index_allows_exactly_one_reservation_event(self):
        out=rehearse(receipt(),unique_slot=True,replay=True)
        self.assertEqual(out["decision"],"SIMULATED_RESERVATION_ONLY_NO_EXTERNAL_UPLOAD")
        self.assertEqual(out["replayed_decision"],"HOLD_ALREADY_RESERVED_OR_IMMUTABLE_CONFLICT")
        self.assertEqual(out["simulated_release_state"],"UPLOAD_STARTED")
        self.assertEqual(out["simulated_event_rows"],1)

    def test_uncertain_uploaded_state_cannot_be_reclaimed(self):
        out=rehearse(receipt(),unique_slot=True,existing_state="UPLOAD_STARTED",replay=True)
        self.assertEqual(out["decision"],"HOLD_ALREADY_RESERVED_OR_IMMUTABLE_CONFLICT")
        self.assertEqual(out["simulated_event_rows"],0)
        self.assertEqual(out["simulated_release_state"],"UPLOAD_STARTED")

    def test_unknown_schedule_state_keeps_no_retry(self):
        out=rehearse(receipt(),unique_slot=True,existing_state="SCHEDULING_UNRESOLVED")
        self.assertEqual(out["decision"],"HOLD_ALREADY_RESERVED_OR_IMMUTABLE_CONFLICT")
        self.assertFalse(out["automatic_upload_retry_authorized"])

    def test_processed_public_release_not_reuploaded(self):
        out=rehearse(receipt(),unique_slot=True,existing_state="PUBLIC_VERIFIED")
        self.assertEqual(out["decision"],"HOLD_ALREADY_RESERVED_OR_IMMUTABLE_CONFLICT")

    def test_sha_mismatch_refused_without_state_change(self):
        out=rehearse(receipt(),unique_slot=True,altered_digest=True)
        self.assertEqual(out["decision"],"HOLD_ALREADY_RESERVED_OR_IMMUTABLE_CONFLICT")
        self.assertEqual(out["simulated_event_rows"],0)

    def test_interrupted_transaction_rolls_back_state_and_event(self):
        out=rehearse(receipt(),unique_slot=True,simulate_failure=True)
        self.assertEqual(out["decision"],"HOLD_TRANSACTION_FAILURE_ROLLED_BACK")
        self.assertEqual(out["simulated_release_state"],"MEDIA_QA_PASSED")
        self.assertEqual(out["simulated_event_rows"],0)

    def test_no_index_transaction_cannot_create_event(self):
        out=rehearse(receipt(),unique_slot=False,replay=True)
        self.assertEqual(out["simulated_event_rows"],0)
        self.assertEqual(out["replayed_decision"],"HOLD_DATE_SLOT_UNIQUENESS_NOT_PROVEN")

    def test_youtube_id_unique_index_not_slot_unique_index(self):
        db=_database(unique_slot=False)
        try:
            self.assertFalse(_slot_index_verified(db))
            indexes=db.execute("PRAGMA index_list('releases')").fetchall()
            self.assertTrue(any(i[2]==1 for i in indexes))
        finally:db.close()

    def test_date_slot_index_verified_when_unique(self):
        db=_database(unique_slot=True)
        try:self.assertTrue(_slot_index_verified(db))
        finally:db.close()

    def test_reject_credential_fields(self):
        x=receipt();x["refresh_token"]="secret"
        with self.assertRaises(UnsafeReservation) as caught:rehearse(x)
        self.assertNotIn("secret",str(caught.exception))

    def test_wrong_slot_clock_rejected(self):
        x=receipt();x["publish_at_utc"]="2026-10-20T16:00:00Z"
        with self.assertRaises(UnsafeReservation):rehearse(x)

    def test_wrong_owner_channel_rejected(self):
        x=receipt();x["channel_id"]="UCnotowner"
        with self.assertRaises(UnsafeReservation):rehearse(x)

    def test_boolean_fields_must_be_true_booleans(self):
        with self.assertRaises(UnsafeReservation):rehearse(receipt(),unique_slot="true")

    def test_no_external_side_effects_even_successful_simulation(self):
        r=rehearse(receipt(),unique_slot=True)
        for key in ("production_d1_writes","real_youtube_uploads",
                    "real_youtube_schedule_writes"):
            self.assertEqual(r[key],0)
        for key in ("owner_oauth_authenticated_here","cloud_autopilot_ready",
                    "production_migration_authorized"):
            self.assertFalse(r[key])
        serialized=json.dumps(r)
        self.assertNotIn("fm_20261020_long_hi",serialized)
        self.assertNotIn("a"*64,serialized)

if __name__=="__main__":unittest.main()
