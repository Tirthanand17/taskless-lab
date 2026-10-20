"""Synthetic review-only IPC test: no actual audio, external API or video release."""
from datetime import datetime,timezone
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from multiprocessing import get_context
from unittest.mock import patch
import hashlib
import hmac
import json
import os
import sqlite3
import stat
import time
import unittest

from autopilot.agent_org import WorkflowError
from autopilot.agent_staging_ipc_service import send_signed_ipc
from autopilot.cloud_transcript_review_ipc import (
    OfflineReviewBundle,StrictTranscriptReviewCommandBoundary,
    canonical_signed_command,serve_offline_strict_review,
    OfflineStrictTranscriptReviewIPC,
)
from autopilot.cloud_transcript_replay_ledger import OfflineTranscriptReviewLedger
from autopilot.test_cloud_transcript_replay_ledger import fixture
from autopilot.test_cloud_acoustic_review_evidence import _data
from autopilot.test_cloud_signed_transcript_reviews import resign,EXCLUDED


def pack(fields,secret):
    signed=dict(fields)
    signed["mac_sha256"]=hmac.new(
        secret,canonical_signed_command(fields),hashlib.sha256,
    ).hexdigest()
    return json.dumps(signed,sort_keys=True,separators=(",",":"))


class StrictTranscriptIPCRehearsalTests(unittest.TestCase):
    def setUp(self):
        tmp=TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name)
        self.db=self.root/"strict_reviews.sqlite3"
        self.socket=self.root/"admit.sock"
        self.secret=os.urandom(32)
        candidate,media,audio,keys,registry,original=fixture("short_hi")
        signed=[]
        evidence={}
        for entry in original:
            who=entry.claim.reviewer_id
            doc=_data(candidate,entry.claim)
            raw=json.dumps(doc,sort_keys=True,ensure_ascii=False,
                           separators=(",",":")).encode()
            path=self.root/(entry.claim.role+".json")
            path.write_bytes(raw)
            evidence[who]=path
            signed.append(resign(
                entry,keys[who],evidence_sha256=sha256(raw).hexdigest(),
            ))
        self.evidence=evidence
        self.episode=candidate.episode_id
        self.review=OfflineReviewBundle(
            candidate,media,audio,tuple(signed),registry,EXCLUDED,evidence
        )
        self.reviews={self.episode:self.review}
        self.fields={
            "action":"review.admit","episode_id":self.episode,
            "expected_current_sha":None,
            "nonce":"synthetic_nonce_123456",
            "expires_at_epoch":int(time.time())+120,
        }

    def test_in_process_signed_entry_never_calls_weak_legacy_path(self):
        ledger=OfflineTranscriptReviewLedger(self.db)
        boundary=StrictTranscriptReviewCommandBoundary(
            ledger,reviews=self.reviews,hmac_key=self.secret
        )
        result=boundary.execute(pack(self.fields,self.secret))
        self.assertTrue(result["two_signed_sidecar_digests_chained"])
        self.assertTrue(result["signed_command_nonce_persisted"])
        self.assertFalse(result["real_audio_verified"])
        self.assertFalse(result["publishing_authorized"])
        self.assertFalse(result["youtube_upload_authorized"])
        self.assertNotIn("media_sha256",result)
        self.assertNotIn("episode_id",result)
        self.assertTrue(ledger.current_status(self.episode)[
            "current_event_has_chained_sidecar_digests"])
        self.assertTrue(ledger.current_status(self.episode)[
            "current_event_has_chained_command_nonce"])

    def test_tampered_unsigned_unknown_stale_or_path_injection_denied(self):
        ledger=OfflineTranscriptReviewLedger(self.db)
        boundary=StrictTranscriptReviewCommandBoundary(
            ledger,reviews=self.reviews,hmac_key=self.secret
        )
        valid=pack(self.fields,self.secret)
        variations=[
            valid.replace('"action":"review.admit"','"action":"publish"'),
            pack({**self.fields,"action":"youtube.upload"},self.secret),
            valid.replace('"nonce":','"nonce":"altered","nonce":'),
            json.dumps({**json.loads(valid),"evidence_path":"/etc/passwd"}),
            pack({**self.fields,"expires_at_epoch":int(time.time())-1},
                 self.secret),
            pack({**self.fields,"expires_at_epoch":int(time.time())+3600},
                 self.secret),
            pack({**self.fields,"episode_id":"not_pre_provisioned"},
                 self.secret),
            "{}",
        ]
        for i,payload in enumerate(variations):
            with self.subTest(case=i),self.assertRaises(WorkflowError):
                boundary.execute(payload)
        self.assertEqual(ledger.current_status(self.episode)[
            "total_accepted_review_batches"],0)

    def test_invalid_sidecar_aborts_before_signed_receipts_are_consumed(self):
        ledger=OfflineTranscriptReviewLedger(self.db)
        boundary=StrictTranscriptReviewCommandBoundary(
            ledger,reviews=self.reviews,hmac_key=self.secret
        )
        path=next(iter(self.evidence.values()))
        path.write_bytes(path.read_bytes()+b" ")
        with self.assertRaises(WorkflowError):
            boundary.execute(pack(self.fields,self.secret))
        with sqlite3.connect(self.db) as conn:
            for table in ("transcript_review_events",
                          "transcript_review_consumed",
                          "transcript_review_sidecars",
                          "transcript_review_command_nonces"):
                self.assertEqual(conn.execute(
                    "SELECT COUNT(*) FROM "+table
                ).fetchone()[0],0)

    def test_actual_separate_process_socket_replay_refusal_and_no_publishing(self):
        context=get_context("spawn")
        read,write=context.Pipe(duplex=False)
        worker=context.Process(
            target=serve_offline_strict_review,
            kwargs={
                "db_path":self.db,"socket_path":self.socket,
                "reviews":self.reviews,"hmac_key":self.secret,
                "ready_pipe":write,
            },
        )
        worker.start()
        write.close()
        self.addCleanup(lambda: worker.join(timeout=5))
        self.addCleanup(lambda: worker.terminate() if worker.is_alive() else None)
        try:
            self.assertTrue(read.poll(20),"Offline strict review socket not ready")
            self.assertTrue(read.recv(),"Offline strict review failed startup")
            self.assertTrue(worker.is_alive())
            self.assertTrue(stat.S_ISSOCK(self.socket.stat().st_mode))
            self.assertEqual(stat.S_IMODE(self.socket.stat().st_mode),0o600)
            command=pack(self.fields,self.secret)
            result=send_signed_ipc(self.socket,command)
            self.assertEqual(result["status"],"OFFLINE_STRICT_REVIEW_JOURNALED")
            self.assertTrue(result["two_signed_sidecar_digests_chained"])
            self.assertTrue(result["signed_command_nonce_persisted"])
            self.assertFalse(result["publishing_authorized"])
            for denied in (command,pack({**self.fields,"action":"release.publish"},
                                        self.secret)):
                with self.assertRaises(WorkflowError):
                    send_signed_ipc(self.socket,denied)
        finally:
            read.close()
            worker.terminate()
            worker.join(timeout=5)
            if worker.is_alive():
                worker.kill()
                worker.join(timeout=5)
        status=OfflineTranscriptReviewLedger(self.db).current_status(self.episode)
        self.assertEqual(status["total_accepted_review_batches"],1)
        self.assertTrue(status["current_event_has_chained_sidecar_digests"])
        self.assertTrue(status["current_event_has_chained_command_nonce"])
        self.assertFalse(status["youtube_publishing_authorized"])

    def test_nonce_reopen_hash_binding_and_tamper_refusal(self):
        ledger=OfflineTranscriptReviewLedger(self.db)
        boundary=StrictTranscriptReviewCommandBoundary(
            ledger,reviews=self.reviews,hmac_key=self.secret
        )
        boundary.execute(pack(self.fields,self.secret))
        with sqlite3.connect(self.db) as conn:
            rows=conn.execute(
                "SELECT nonce,event_sha,expires_at_epoch "
                "FROM transcript_review_command_nonces"
            ).fetchall()
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0][0],self.fields["nonce"])
        self.assertEqual(rows[0][2],self.fields["expires_at_epoch"])
        reopened=OfflineTranscriptReviewLedger(self.db)
        self.assertTrue(reopened.current_status(self.episode)[
            "current_event_has_chained_command_nonce"])
        with sqlite3.connect(self.db) as conn:
            conn.execute(
                "UPDATE transcript_review_command_nonces "
                "SET expires_at_epoch=expires_at_epoch+1"
            )
        with self.assertRaises(WorkflowError):
            OfflineTranscriptReviewLedger(self.db)

    def test_deleted_command_nonce_breaks_hash_chain(self):
        boundary=StrictTranscriptReviewCommandBoundary(
            OfflineTranscriptReviewLedger(self.db),
            reviews=self.reviews,hmac_key=self.secret
        )
        boundary.execute(pack(self.fields,self.secret))
        with sqlite3.connect(self.db) as conn:
            conn.execute("DELETE FROM transcript_review_command_nonces")
        with self.assertRaises(WorkflowError):
            OfflineTranscriptReviewLedger(self.db)

    def test_sqlite_host_clock_rejects_expired_signed_command(self):
        import autopilot.cloud_transcript_replay_ledger as ledger_module
        ledger=OfflineTranscriptReviewLedger(self.db)
        boundary=StrictTranscriptReviewCommandBoundary(
            ledger,reviews=self.reviews,hmac_key=self.secret
        )
        # IPC process wall-time preflight still passes, but the journal's
        # transactional SQLite clock considers the exact HMAC expiry stale.
        simulated=int(time.time())+400
        with patch.object(ledger_module,"_sqlite_host_epoch",
                          return_value=simulated):
            with self.assertRaises(WorkflowError):
                boundary.execute(pack(self.fields,self.secret))
        with sqlite3.connect(self.db) as conn:
            self.assertEqual(conn.execute(
                "SELECT COUNT(*) FROM transcript_review_command_nonces"
            ).fetchone()[0],0)
            self.assertEqual(conn.execute(
                "SELECT COUNT(*) FROM transcript_review_consumed"
            ).fetchone()[0],0)

    def test_bad_evidence_rolls_back_nonce_and_later_valid_try_is_single_use(self):
        ledger=OfflineTranscriptReviewLedger(self.db)
        boundary=StrictTranscriptReviewCommandBoundary(
            ledger,reviews=self.reviews,hmac_key=self.secret
        )
        command=pack(self.fields,self.secret)
        path=next(iter(self.evidence.values()))
        original=path.read_bytes()
        path.write_bytes(original+b" ")
        with self.assertRaises(WorkflowError):
            boundary.execute(command)
        with sqlite3.connect(self.db) as conn:
            self.assertEqual(conn.execute(
                "SELECT COUNT(*) FROM transcript_review_command_nonces"
            ).fetchone()[0],0)
        path.write_bytes(original)
        self.assertTrue(boundary.execute(command)["signed_command_nonce_persisted"])
        with self.assertRaises(WorkflowError):
            boundary.execute(command)

    def test_socket_direct_close_cleans_only_owned_node(self):
        ledger=OfflineTranscriptReviewLedger(self.db)
        boundary=StrictTranscriptReviewCommandBoundary(
            ledger,reviews=self.reviews,hmac_key=self.secret
        )
        service=OfflineStrictTranscriptReviewIPC(self.socket,boundary)
        self.assertTrue(self.socket.exists())
        self.assertEqual(stat.S_IMODE(self.socket.stat().st_mode),0o600)
        service.server_close()
        self.assertFalse(self.socket.exists())


if __name__=="__main__":
    unittest.main()
