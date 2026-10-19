"""No-secrets replay/racing/revision tests using fake editorial attestations."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime,timedelta,timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import sqlite3
import unittest

from autopilot.agent_org import WorkflowError
from autopilot.cloud_signed_transcript_reviews import transcript_digest
from autopilot.test_cloud_signed_transcript_reviews import (
    fixture as old_test_fixture,resign,EXCLUDED,
)


def fixture(lane="short_en"):
    """Refresh ONLY synthetic signed times against actual disposable host time.

    The original signed-transcript unit fixtures use a fixed reference clock.
    This ledger tests the stronger SQLite-time boundary instead.
    """
    candidate,media,audio,keys,registry,original=old_test_fixture(lane)
    reference=datetime.now(timezone.utc)
    refreshed=tuple(resign(
        record,keys[record.claim.reviewer_id],
        assessed_at_utc=(reference-timedelta(minutes=7)).isoformat(),
        expires_at_utc=(reference+timedelta(hours=1)).isoformat(),
    ) for record in original)
    return candidate,media,audio,keys,registry,refreshed
from autopilot.cloud_transcript_replay_ledger import (
    MAX_REVIEW_EVENTS,OfflineTranscriptReviewLedger,
)


class TranscriptReviewJournalTests(unittest.TestCase):
    def setUp(self):
        tmp=TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.path=Path(tmp.name)/"signed_reviews.sqlite3"
        self.ledger=OfflineTranscriptReviewLedger(self.path)

    def admit(self,f,*,ledger=None,expected=None):
        a,b,c,keys,registry,signed=f
        return (ledger or self.ledger).commit(
            candidate=a,media=b,audio_screen=c,
            signed_attestations=signed,registry=registry,
            excluded_creator_publisher_ids=EXCLUDED,
            now=datetime.now(timezone.utc),expected_current_sha=expected,
        )

    def different_media(self,f,*,digest,nonce):
        a,b,c,keys,registry,signed=f
        a=replace(a,media_sha256=digest)
        b=replace(b,video_sha256=digest)
        c=replace(c,video_sha256=digest)
        new=[]
        for old in signed:
            owner=old.claim.reviewer_id
            new.append(resign(
                old,keys[owner],transcript_sha256=transcript_digest(a),
                media_sha256=digest,receipt_id=old.claim.receipt_id+"_"+nonce,
            ))
        return (a,b,c,keys,registry,tuple(new))

    def test_caller_cannot_backdate_or_jump_time_to_bypass_review_expiry(self):
        f=fixture()
        a,b,c,keys,reg,old=f
        for forged in (
            datetime.now(timezone.utc)-timedelta(days=3),
            datetime.now(timezone.utc)+timedelta(days=3),
            datetime.now(timezone.utc).replace(tzinfo=None),
        ):
            with self.subTest(clock=str(forged)),self.assertRaises(WorkflowError):
                self.ledger.commit(
                    candidate=a,media=b,audio_screen=c,
                    signed_attestations=old,registry=reg,
                    excluded_creator_publisher_ids=EXCLUDED,
                    now=forged,expected_current_sha=None,
                )
        self.assertEqual(self.ledger.current_status(a.episode_id)[
            "total_accepted_review_batches"],0)
        accepted=self.admit(f)
        self.assertTrue(accepted["local_sqlite_time_checked_in_transaction"])
        self.assertFalse(accepted["remotely_trusted_database_time"])

    def test_durable_event_timestamp_uses_transaction_sqlite_time(self):
        f=fixture()
        accepted=self.admit(f)
        with sqlite3.connect(self.path) as db:
            stored=db.execute(
                "SELECT accepted_at_utc FROM transcript_review_events"
            ).fetchone()[0]
        self.assertEqual(stored,accepted["accepted_at_host_utc"])
        self.assertEqual(datetime.fromisoformat(stored).microsecond,0)
        self.assertEqual(datetime.fromisoformat(stored).utcoffset(),
                         timedelta(0))

    def test_os_clock_rollback_after_reopen_blocks_second_signed_batch(self):
        from unittest.mock import patch
        import autopilot.cloud_transcript_replay_ledger as ledger_module
        f=fixture()
        first=self.admit(f)
        revised=self.different_media(f,digest="d"*64,nonce="rollback")
        with sqlite3.connect(self.path) as db:
            prior=datetime.fromisoformat(db.execute(
                "SELECT accepted_at_utc FROM transcript_review_events"
            ).fetchone()[0])
        past=int(prior.timestamp())-60
        reopened=OfflineTranscriptReviewLedger(self.path)
        with patch.object(ledger_module,"_sqlite_host_epoch",return_value=past):
            with self.assertRaises(WorkflowError):
                self.admit(revised,ledger=reopened,expected=first["event_sha256"])
        self.assertEqual(self.ledger.current_status(f[0].episode_id)[
            "total_accepted_review_batches"],1)

    def test_suspicious_future_sqlite_time_cannot_validate_expired_attestations(self):
        from unittest.mock import patch
        import autopilot.cloud_transcript_replay_ledger as ledger_module
        f=fixture()
        later=int(datetime.now(timezone.utc).timestamp())+86400*4
        with patch.object(ledger_module,"_sqlite_host_epoch",return_value=later):
            # Do not specify now; even the caller cannot override the
            # SQLite-selected verifier instant.
            a,b,c,keys,reg,signed=f
            with self.assertRaises(WorkflowError):
                self.ledger.commit(
                    candidate=a,media=b,audio_screen=c,
                    signed_attestations=signed,registry=reg,
                    excluded_creator_publisher_ids=EXCLUDED,
                    now=None,expected_current_sha=None,
                )
        self.assertEqual(self.ledger.current_status(f[0].episode_id)[
            "total_accepted_review_batches"],0)

    def test_first_accept_has_fenced_durable_one_time_receipts(self):
        f=fixture()
        got=self.admit(f)
        self.assertEqual(got["event_number"],1)
        self.assertFalse(got["youtube_publishing_authorized"])
        self.assertFalse(got["actual_audio_content_independently_verified"])
        db=OfflineTranscriptReviewLedger(self.path)
        status=db.current_status(f[0].episode_id)
        self.assertEqual(status["current_event_sha256"],got["event_sha256"])
        self.assertEqual(status["total_accepted_review_batches"],1)
        with sqlite3.connect(self.path) as connection:
            self.assertEqual(connection.execute(
                "SELECT count(*) FROM transcript_review_consumed"
            ).fetchone()[0],2)

    def test_identical_receipts_cannot_be_replayed_after_reopen(self):
        f=fixture()
        self.admit(f)
        db=OfflineTranscriptReviewLedger(self.path)
        with self.assertRaises(WorkflowError):
            self.admit(f,ledger=db,expected=None)
        self.assertEqual(db.current_status(f[0].episode_id)[
            "total_accepted_review_batches"],1)

    def test_replaced_media_requires_expected_prior_head(self):
        f=fixture()
        first=self.admit(f)
        next_f=self.different_media(f,digest="c"*64,nonce="v2")
        with self.assertRaises(WorkflowError):
            self.admit(next_f)
        second=self.admit(next_f,expected=first["event_sha256"])
        self.assertEqual(second["supersedes_sha256"],first["event_sha256"])
        self.assertEqual(second["event_number"],2)
        self.assertNotEqual(second["event_sha256"],first["event_sha256"])
        status=self.ledger.current_status(f[0].episode_id)
        self.assertEqual(status["current_event_sha256"],second["event_sha256"])
        with self.assertRaises(WorkflowError):
            self.admit(self.different_media(f,digest="d"*64,nonce="v3"),
                       expected=first["event_sha256"])

    def test_two_connections_racing_to_admit_one_batch(self):
        f=fixture()
        def attempt(_):
            try:
                return self.admit(f,ledger=OfflineTranscriptReviewLedger(self.path))
            except WorkflowError:
                return None
        with ThreadPoolExecutor(max_workers=3) as pool:
            replies=list(pool.map(attempt,range(3)))
        self.assertEqual(sum(x is not None for x in replies),1)
        self.assertEqual(self.ledger.current_status(f[0].episode_id)[
            "total_accepted_review_batches"],1)

    def test_rejected_or_bad_second_signature_rolls_back_every_receipt(self):
        f=fixture()
        a,b,c,keys,reg,signed=f
        denied=list(signed)
        denied[1]=resign(denied[1],keys[denied[1].claim.reviewer_id],
                         decision="REJECT")
        rejected=(a,b,c,keys,reg,tuple(denied))
        with self.assertRaises(WorkflowError):
            self.admit(rejected)
        self.assertEqual(self.ledger.current_status(a.episode_id)[
            "total_accepted_review_batches"],0)
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute(
                "SELECT COUNT(*) FROM transcript_review_consumed"
            ).fetchone()[0],0)
        self.assertEqual(self.admit(f)["event_number"],1)

    def test_reusing_only_one_old_receipt_on_new_episode_denied(self):
        f=fixture()
        first=self.admit(f)
        next_f=self.different_media(f,digest="c"*64,nonce="fresh")
        a,b,c,keys,reg,signed=next_f
        changed=resign(signed[0],keys[signed[0].claim.reviewer_id],
                       receipt_id=f[5][0].claim.receipt_id)
        with self.assertRaises(WorkflowError):
            self.admit((a,b,c,keys,reg,(changed,signed[1])),
                       expected=first["event_sha256"])
        self.assertEqual(self.ledger.current_status(a.episode_id)[
            "total_accepted_review_batches"],1)

    def test_durable_hash_chain_detects_tampered_event_or_head(self):
        f=fixture()
        self.admit(f)
        with sqlite3.connect(self.path) as db:
            db.execute("UPDATE transcript_review_events SET lane='wrong'")
        with self.assertRaises(WorkflowError):
            OfflineTranscriptReviewLedger(self.path)

    def test_consumed_index_tampering_detected_without_publish_permission(self):
        f=fixture()
        self.admit(f)
        with sqlite3.connect(self.path) as db:
            db.execute("DELETE FROM transcript_review_consumed")
        with self.assertRaises(WorkflowError):
            self.ledger.current_status(f[0].episode_id)

    def test_bounded_audit_fails_closed_not_expanding_indefinitely(self):
        f=fixture()
        from unittest.mock import patch
        with patch("autopilot.cloud_transcript_replay_ledger.MAX_REVIEW_EVENTS",0):
            with self.assertRaises(WorkflowError):
                self.admit(f)
        self.assertEqual(self.ledger.current_status(f[0].episode_id)[
            "total_accepted_review_batches"],0)

    def test_video_digest_globally_cannot_be_used_for_new_episode(self):
        first=self.admit(fixture("short_en"))
        # Test fixture intentionally shares one dummy media digest across all
        # lanes; cross-lane media reuse must be blocked even with fresh keys.
        other=fixture("short_hi")
        with self.assertRaises(WorkflowError):
            self.admit(other)
        self.assertEqual(self.ledger.current_status("csv_tutorial_short_en")[
            "total_accepted_review_batches"],1)

    def test_replay_ledger_persists_no_private_keys_media_or_raw_words(self):
        f=fixture()
        reply=self.admit(f)
        with sqlite3.connect(self.path) as db:
            schema="\n".join(x[0] for x in db.execute(
                "SELECT sql FROM sqlite_master WHERE sql IS NOT NULL"
            ))
            self.assertNotIn("private_key",schema)
            self.assertNotIn("oauth",schema.lower())
            self.assertEqual(db.execute(
                "SELECT count(*) FROM transcript_review_events"
            ).fetchone()[0],1)
        self.assertFalse(reply["actual_audio_content_independently_verified"])
        self.assertFalse(reply["youtube_publishing_authorized"])


if __name__=="__main__":
    unittest.main()
