"""No secrets, real OAuth, Cloudflare connection or YouTube publishing."""
import sqlite3
import tempfile
import unittest
from pathlib import Path

from autopilot.core import CHANNEL_ID
from autopilot.phase4_offline_ledger import OfflineLedger, ProtocolBlocked

NOW="2026-10-17T14:00:00+00:00"
LATER="2026-10-17T14:00:30+00:00"
EXPIRED="2026-10-17T14:03:00+00:00"
SLOT="2026-10-20T05:30:00+00:00"
SHA="a"*64


class Phase4OfflineLedgerTests(unittest.TestCase):
    def setUp(self):
        self.l=OfflineLedger(offline_test_only=True)
        self.l.reserve(channel=CHANNEL_ID,episode="ep_01",planned_utc=SLOT,
                       media_sha256=SHA,now_utc=NOW)
        self.version,self.fence=self.l.claim("ep_01",expected_version=0,
                                                owner="worker_1",now_utc=NOW)

    def tearDown(self):
        self.l.close()

    def step(self,stage):
        self.version=self.l.local_step("ep_01",target=stage,
                         expected_version=self.version,owner="worker_1",
                         fence=self.fence,now_utc=LATER,
                         review_digest="b"*64 if stage=="media_qa_passed" else None)

    def ready(self):
        for s in ("research_verified","script_verified","media_qa_passed"):
            self.step(s)

    def test_offline_flag_is_mandatory(self):
        with self.assertRaises(ProtocolBlocked):
            OfflineLedger()

    def test_duplicate_reserve_is_read_only(self):
        count=len(self.l.events("ep_01"))
        self.assertFalse(self.l.reserve(channel=CHANNEL_ID,episode="ep_01",
            planned_utc=SLOT,media_sha256=SHA,now_utc=NOW))
        self.assertEqual(count,len(self.l.events("ep_01")))

    def test_episode_media_immutable(self):
        with self.assertRaises(ProtocolBlocked):
            self.l.reserve(channel=CHANNEL_ID,episode="ep_01",planned_utc=SLOT,
                           media_sha256="c"*64,now_utc=NOW)

    def test_other_format_same_utc_slot_is_denied(self):
        with self.assertRaises(ProtocolBlocked):
            self.l.reserve(channel=CHANNEL_ID,episode="long_02",planned_utc=SLOT,
                           media_sha256="c"*64,now_utc=NOW)

    def test_identical_media_other_episode_denied(self):
        with self.assertRaises(ProtocolBlocked):
            self.l.reserve(channel=CHANNEL_ID,episode="ep_02",
                planned_utc="2026-10-21T05:30:00+00:00",media_sha256=SHA,now_utc=NOW)

    def test_wrong_channel_denied(self):
        with self.assertRaises(ProtocolBlocked):
            self.l.reserve(channel="another_channel",episode="ep_03",
                planned_utc="2026-10-21T05:30:00+00:00",media_sha256="c"*64,now_utc=NOW)

    def test_noncanonical_datetime_denied(self):
        with self.assertRaises(ProtocolBlocked):
            self.l.reserve(channel=CHANNEL_ID,episode="ep_03",
                planned_utc="2026-10-21T11:00:00+05:30",media_sha256="c"*64,now_utc=NOW)

    def test_unreviewed_or_skipped_media_denied(self):
        with self.assertRaises(ProtocolBlocked):
            self.l.local_step("ep_01",target="media_qa_passed",expected_version=self.version,
                              owner="worker_1",fence=self.fence,now_utc=LATER,review_digest="b"*64)
        self.step("research_verified")
        self.step("script_verified")
        with self.assertRaises(ProtocolBlocked):
            self.l.local_step("ep_01",target="media_qa_passed",expected_version=self.version,
                              owner="worker_1",fence=self.fence,now_utc=LATER)

    def test_stale_version_and_repeated_lease_denied(self):
        with self.assertRaises(ProtocolBlocked):
            self.l.claim("ep_01",expected_version=0,owner="worker_2",now_utc=LATER)
        with self.assertRaises(ProtocolBlocked):
            self.l.claim("ep_01",expected_version=self.version,owner="worker_1",now_utc=LATER)

    def test_lease_expiry_and_fencing_prevent_old_writer(self):
        self.ready()
        new_version,new_fence=self.l.claim("ep_01",expected_version=self.version,
                                             owner="worker_2",now_utc=EXPIRED)
        with self.assertRaises(ProtocolBlocked):
            self.l.begin_upload_once("ep_01",expected_version=self.version,
                owner="worker_1",fence=self.fence,media_sha256=SHA,
                intent_id="intentA",now_utc=EXPIRED)
        new_version=self.l.begin_upload_once("ep_01",expected_version=new_version,
                owner="worker_2",fence=new_fence,media_sha256=SHA,
                intent_id="intentA",now_utc="2026-10-17T14:03:20+00:00")
        self.assertEqual(self.l.get("ep_01")["stage"],"upload_uncertain")

    def test_upload_reservation_is_single_shot_and_uncertain(self):
        self.ready()
        self.version=self.l.begin_upload_once("ep_01",expected_version=self.version,
            owner="worker_1",fence=self.fence,media_sha256=SHA,
            intent_id="intentA",now_utc=LATER)
        with self.assertRaises(ProtocolBlocked):
            self.l.begin_upload_once("ep_01",expected_version=self.version,
                owner="worker_1",fence=self.fence,media_sha256=SHA,
                intent_id="intentA",now_utc=LATER)
        self.assertEqual(self.l.get("ep_01")["stage"],"upload_uncertain")

    def test_upload_wrong_hash_fails_without_state_change(self):
        self.ready()
        with self.assertRaises(ProtocolBlocked):
            self.l.begin_upload_once("ep_01",expected_version=self.version,
                owner="worker_1",fence=self.fence,media_sha256="c"*64,
                intent_id="intentA",now_utc=LATER)
        self.assertEqual(self.l.get("ep_01")["stage"],"media_qa_passed")

    def upload(self,video_id="abc123def45"):
        self.ready()
        self.version=self.l.begin_upload_once("ep_01",expected_version=self.version,
            owner="worker_1",fence=self.fence,media_sha256=SHA,
            intent_id="intentA",now_utc=LATER)
        self.version=self.l.bind_private_readback("ep_01",expected_version=self.version,
            owner="worker_1",fence=self.fence,now_utc=LATER,
            remote_channel=CHANNEL_ID,youtube_id=video_id,
            processed=True,privacy="private",authenticated=True)

    def test_wrong_remote_owner_or_privacy_is_denied(self):
        self.ready()
        self.version=self.l.begin_upload_once("ep_01",expected_version=self.version,
            owner="worker_1",fence=self.fence,media_sha256=SHA,
            intent_id="intentA",now_utc=LATER)
        for overrides in ({"remote_channel":"fake"},{"privacy":"public"},
                          {"authenticated":False},{"processed":False}):
            args=dict(remote_channel=CHANNEL_ID,youtube_id="abc123def45",
                      processed=True,privacy="private",authenticated=True)
            args.update(overrides)
            with self.assertRaises(ProtocolBlocked):
                self.l.bind_private_readback("ep_01",expected_version=self.version,
                    owner="worker_1",fence=self.fence,now_utc=LATER,**args)
        self.assertEqual(self.l.get("ep_01")["stage"],"upload_uncertain")

    def test_verified_private_schedule_public_sequence(self):
        self.upload()
        self.version=self.l.begin_schedule_once("ep_01",expected_version=self.version,
            owner="worker_1",fence=self.fence,now_utc=LATER)
        with self.assertRaises(ProtocolBlocked):
            self.l.begin_schedule_once("ep_01",expected_version=self.version,
                owner="worker_1",fence=self.fence,now_utc=LATER)
        with self.assertRaises(ProtocolBlocked):
            self.l.bind_schedule_readback("ep_01",expected_version=self.version,
                owner="worker_1",fence=self.fence,now_utc=LATER,
                youtube_id="abc123def45",publish_at_utc="2026-10-20T05:31:00+00:00",
                authenticated=True,privacy="private")
        self.version=self.l.bind_schedule_readback("ep_01",expected_version=self.version,
                owner="worker_1",fence=self.fence,now_utc=LATER,
                youtube_id="abc123def45",publish_at_utc=SLOT,
                authenticated=True,privacy="private")
        with self.assertRaises(ProtocolBlocked):
            self.l.bind_public_readback("ep_01",expected_version=self.version,
                owner="worker_1",fence=self.fence,now_utc=LATER,
                youtube_id="abc123def45",authenticated=True,playable=False,privacy="public")
        self.version=self.l.bind_public_readback("ep_01",expected_version=self.version,
                owner="worker_1",fence=self.fence,now_utc=LATER,
                youtube_id="abc123def45",authenticated=True,playable=True,privacy="public")
        self.assertEqual(self.l.get("ep_01")["stage"],"public_verified")

    def test_event_records_are_append_only(self):
        event=self.l.events("ep_01")[0]["event_id"]
        with self.assertRaises(sqlite3.IntegrityError):
            self.l.db.execute("DELETE FROM phase4_events WHERE event_id=?",(event,))
        with self.assertRaises(sqlite3.IntegrityError):
            self.l.db.execute("UPDATE phase4_events SET action='fake' WHERE event_id=?",(event,))

    def test_quarantine_is_terminal(self):
        self.version=self.l.quarantine("ep_01",expected_version=self.version,
            owner="worker_1",fence=self.fence,now_utc=LATER,reason="Failed independent media review")
        with self.assertRaises(ProtocolBlocked):
            self.l.claim("ep_01",expected_version=self.version,owner="worker_2",now_utc=EXPIRED)

    def test_durable_crash_reopen_preserves_uncertain_and_events(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"simulation.sqlite"
            a=OfflineLedger(path,offline_test_only=True)
            a.reserve(channel=CHANNEL_ID,episode="crashed",planned_utc=SLOT,
                      media_sha256=SHA,now_utc=NOW)
            v,f=a.claim("crashed",expected_version=0,owner="worker_1",now_utc=NOW)
            for s in ("research_verified","script_verified","media_qa_passed"):
                v=a.local_step("crashed",target=s,expected_version=v,owner="worker_1",
                    fence=f,now_utc=LATER,review_digest="b"*64 if s=="media_qa_passed" else None)
            v=a.begin_upload_once("crashed",expected_version=v,owner="worker_1",
                fence=f,media_sha256=SHA,intent_id="intent_crash",now_utc=LATER)
            a.close()
            b=OfflineLedger(path,offline_test_only=True)
            self.assertEqual(b.get("crashed")["stage"],"upload_uncertain")
            v2,f2=b.claim("crashed",expected_version=v,owner="worker_2",now_utc=EXPIRED)
            with self.assertRaises(ProtocolBlocked):
                b.begin_upload_once("crashed",expected_version=v2,owner="worker_2",
                    fence=f2,media_sha256=SHA,intent_id="intent_new",now_utc=EXPIRED)
            self.assertEqual(len(b.events("crashed")),7)
            b.close()

    def test_racing_writers_one_lease_wins(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"racing.sqlite"
            a=OfflineLedger(path,offline_test_only=True)
            a.reserve(channel=CHANNEL_ID,episode="race",planned_utc=SLOT,
                      media_sha256=SHA,now_utc=NOW)
            b=OfflineLedger(path,offline_test_only=True)
            a.claim("race",expected_version=0,owner="a",now_utc=NOW)
            with self.assertRaises(ProtocolBlocked):
                b.claim("race",expected_version=0,owner="b",now_utc=NOW)
            self.assertEqual(len(a.events("race")),2)
            b.close()
            a.close()


if __name__=="__main__":
    unittest.main()
