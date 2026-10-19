"""No-network tests for optional strict acoustic review + durable SQLite audit.

Only fabricated signed metadata, fresh local ephemeral keys and sidecars are
used. None of the checks represent real audio listening or release clearance.
"""
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import sqlite3
import unittest

from autopilot.agent_org import WorkflowError
from autopilot.cloud_transcript_replay_ledger import OfflineTranscriptReviewLedger
from autopilot.test_cloud_transcript_replay_ledger import fixture
from autopilot.test_cloud_acoustic_review_evidence import _data
from autopilot.test_cloud_signed_transcript_reviews import resign, EXCLUDED


class AcousticReviewJournalTests(unittest.TestCase):
    def setUp(self):
        temp=TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.directory=Path(temp.name)
        self.db=self.directory/"review.sqlite3"
        self.ledger=OfflineTranscriptReviewLedger(self.db)
        self.candidate,self.media,self.audio,self.keys,self.registry,original=fixture("short_hi")
        self.sidecars={}
        signed=[]
        for entry in original:
            reviewer=entry.claim.reviewer_id
            payload=_data(self.candidate,entry.claim)
            raw=json.dumps(payload,sort_keys=True,ensure_ascii=False,
                           separators=(",",":")).encode("utf-8")
            sidecar=self.directory/(entry.claim.role+".json")
            sidecar.write_bytes(raw)
            self.sidecars[reviewer]=sidecar
            signed.append(resign(
                entry,self.keys[reviewer],
                evidence_sha256=sha256(raw).hexdigest(),
            ))
        self.signed=tuple(signed)

    def admit(self,*,sidecars=None,ledger=None):
        return (ledger or self.ledger).commit_sidecar_bound(
            candidate=self.candidate,media=self.media,audio_screen=self.audio,
            signed_attestations=self.signed,registry=self.registry,
            excluded_creator_publisher_ids=EXCLUDED,
            now=datetime.now(timezone.utc),expected_current_sha=None,
            evidence_files=self.sidecars if sidecars is None else sidecars,
        )

    def test_strict_intake_chains_two_real_file_hashes_into_event(self):
        result=self.admit()
        self.assertTrue(result["signed_sidecar_digests_chained"])
        self.assertFalse(result["actual_audio_content_independently_verified"])
        self.assertFalse(result["youtube_publishing_authorized"])
        with sqlite3.connect(self.db) as conn:
            rows=conn.execute(
                "SELECT role,reviewer_id,evidence_sha "
                "FROM transcript_review_sidecars ORDER BY role"
            ).fetchall()
        self.assertEqual(len(rows),2)
        self.assertEqual({r[0] for r in rows},
                         {"transcriber","independent_listener"})
        for role,reviewer_id,digest in rows:
            self.assertEqual(digest,sha256(self.sidecars[reviewer_id].read_bytes()).hexdigest())
        reopened=OfflineTranscriptReviewLedger(self.db)
        status=reopened.current_status(self.candidate.episode_id)
        self.assertEqual(status["current_event_sha256"],result["event_sha256"])
        self.assertTrue(status["current_event_has_chained_sidecar_digests"])

    def test_missing_sidecar_or_changed_bytes_fail_before_any_receipt_use(self):
        with self.assertRaises(WorkflowError):
            self.admit(sidecars={})
        reviewer=next(iter(self.sidecars))
        p=self.sidecars[reviewer]
        p.write_bytes(p.read_bytes()+b" ")
        with self.assertRaises(WorkflowError):
            self.admit()
        with sqlite3.connect(self.db) as conn:
            self.assertEqual(conn.execute(
                "SELECT count(*) FROM transcript_review_events").fetchone()[0],0)
            self.assertEqual(conn.execute(
                "SELECT count(*) FROM transcript_review_consumed").fetchone()[0],0)
            self.assertEqual(conn.execute(
                "SELECT count(*) FROM transcript_review_sidecars").fetchone()[0],0)

    def test_tampering_a_stored_sidecar_digest_breaks_chain(self):
        self.admit()
        with sqlite3.connect(self.db) as conn:
            conn.execute(
                "UPDATE transcript_review_sidecars SET evidence_sha=? "
                "WHERE role='transcriber'",("f"*64,)
            )
        with self.assertRaises(WorkflowError):
            OfflineTranscriptReviewLedger(self.db)

    def test_deleting_one_sidecar_breaks_chain_after_reopen(self):
        self.admit()
        with sqlite3.connect(self.db) as conn:
            conn.execute(
                "DELETE FROM transcript_review_sidecars "
                "WHERE role='independent_listener'"
            )
        with self.assertRaises(WorkflowError):
            OfflineTranscriptReviewLedger(self.db)

    def test_legacy_detached_only_journal_is_visibly_weaker(self):
        result=self.ledger.commit(
            candidate=self.candidate,media=self.media,audio_screen=self.audio,
            signed_attestations=self.signed,registry=self.registry,
            excluded_creator_publisher_ids=EXCLUDED,
            now=datetime.now(timezone.utc),expected_current_sha=None,
        )
        self.assertFalse(result["signed_sidecar_digests_chained"])
        status=OfflineTranscriptReviewLedger(self.db).current_status(
            self.candidate.episode_id)
        self.assertFalse(status["current_event_has_chained_sidecar_digests"])
        self.assertFalse(status["youtube_publishing_authorized"])


if __name__=="__main__":
    unittest.main()
