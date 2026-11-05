"""B4b2 negative status-probe tests: all synthetic, no Google API or network."""
from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, time, timezone
from zoneinfo import ZoneInfo
import unittest

from autopilot.youtube_private_first_contract import prepare_unapproved_intent
from autopilot.youtube_resumable_recovery_contract import (
    FakeSession, RecoveryRefused, fake_persisted_session,
    make_status_probe, interpret_fake_status_reply,
)

CHANNEL = "UC" + "X"*22
VIDEO_ID = "ABCdef012_-"
FAKE_HANDLE = "e"*64


def intention():
    date=(datetime.now(timezone.utc).astimezone(ZoneInfo("Asia/Kolkata"))+
          timedelta(days=90)).date()
    local=datetime.combine(date,time(11,0),tzinfo=ZoneInfo("Asia/Kolkata"))
    stamp=local.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return prepare_unapproved_intent(
        episode_id="mock_original_2099_001",slot="short_am",
        channel_id=CHANNEL,
        final_mp4_sha256="a"*64,captions_srt_sha256="b"*64,
        thumbnail_sha256="c"*64,source_review_context_sha256="d"*64,
        title="Original experiment: photon travel",
        description="Synthetic code-only no-release fixture",
        language="en",synthetic_media_disclosure=False,
        made_for_kids=False,publish_at_utc=stamp,
        now=datetime.now(timezone.utc),
    )


def session(size=3000000):
    return fake_persisted_session(
        intent=intention(),total_bytes=size,
        encrypted_session_reference_sha256=FAKE_HANDLE,
        synthetic_checkpoint_saved=True,
    )


def fake_video(id=VIDEO_ID, channel=CHANNEL, privacy="private"):
    return {"id":id, "snippet":{"channelId":channel},
            "status":{"privacyStatus":privacy}}


class SessionBindingTests(unittest.TestCase):
    def test_status_probe_has_exact_zero_byte_inquiry_only(self):
        sess=session()
        p=make_status_probe(sess)
        self.assertEqual(p.action,"QUERY_EXISTING_SESSION_ONLY")
        self.assertEqual(p.method,"PUT")
        self.assertEqual(p.headers,{"Content-Length":"0",
                                   "Content-Range":"bytes */3000000"})
        self.assertFalse(p.actual_http_executed)
        self.assertFalse(p.actual_video_uploaded)
        self.assertFalse(p.actual_video_scheduled)
        self.assertFalse(p.release_authorized)
        self.assertEqual(sess.state,"PROBE_REQUIRED")

    def test_no_saved_session_no_new_upload(self):
        with self.assertRaises(RecoveryRefused):
            fake_persisted_session(
                intent=intention(), total_bytes=100,
                encrypted_session_reference_sha256=FAKE_HANDLE,
                synthetic_checkpoint_saved=False)

    def test_invalid_media_size_session_hash_and_intent_rejected(self):
        good=intention()
        for length in (0,-1,True,256000000001,3.5):
            with self.subTest(length=length), self.assertRaises(RecoveryRefused):
                fake_persisted_session(
                    intent=good,total_bytes=length,
                    encrypted_session_reference_sha256=FAKE_HANDLE,
                    synthetic_checkpoint_saved=True)
        for digest in ("","not-sha256","F"*64,None):
            with self.subTest(digest=digest), self.assertRaises(RecoveryRefused):
                fake_persisted_session(
                    intent=good,total_bytes=2,
                    encrypted_session_reference_sha256=digest,
                    synthetic_checkpoint_saved=True)
        for changes in (dict(context_sha256="f"*64),
                        dict(real_owner_approval=True),
                        dict(release_authorized=True),
                        dict(simulation_only=False)):
            with self.subTest(changes=changes), self.assertRaises(RecoveryRefused):
                fake_persisted_session(
                    intent=replace(good,**changes),total_bytes=20,
                    encrypted_session_reference_sha256=FAKE_HANDLE,
                    synthetic_checkpoint_saved=True)

    def test_session_false_authorities_are_enforced(self):
        s=session()
        for changes in (
            dict(release_authorized=True),
            dict(real_cloud_storage_verified=True),
            dict(owner_oauth_verified=True),
            dict(actual_upload_verified=True),
            dict(mock_only=False),
            dict(synthetic_checkpoint_saved=False),
            dict(context_sha256="z"*64),
            dict(encrypted_session_reference_sha256="f"),
            dict(total_bytes=0),
            dict(acknowledged_end=-2),
            dict(acknowledged_end=s.total_bytes),
            dict(transient_responses=5),
            dict(transient_responses=True),
        ):
            with self.subTest(changes=changes), self.assertRaises(RecoveryRefused):
                make_status_probe(replace(s,**changes))


class ProbeInterpretationTests(unittest.TestCase):
    def test_empty_308_restarts_at_exact_zero(self):
        after,p=interpret_fake_status_reply(session(size=10),
                   status_code=308,response_headers={})
        self.assertEqual(p.action,"RESUME_EXISTING_SESSION_BYTES_ONLY")
        self.assertEqual(p.headers["Content-Range"],"bytes 0-9/10")
        self.assertEqual(p.headers["Content-Length"],"10")
        self.assertEqual(p.next_offset,0)
        self.assertEqual(after.acknowledged_end,-1)
        self.assertFalse(p.actual_video_uploaded)

    def test_partial_308_resumes_at_next_byte_not_overlap_or_gap(self):
        after,p=interpret_fake_status_reply(session(),
                    status_code=308,response_headers={"Range":"bytes=0-999999"})
        self.assertEqual(p.headers["Content-Range"],"bytes 1000000-2999999/3000000")
        self.assertEqual(p.headers["Content-Length"],"2000000")
        self.assertEqual((p.next_offset,p.remaining_bytes),(1000000,2000000))
        self.assertEqual(after.acknowledged_end,999999)
        # Response to later query still cannot go backwards.
        after2,p2=interpret_fake_status_reply(
            after,status_code=308,response_headers={"Range":"bytes=0-1499999"})
        self.assertEqual(p2.next_offset,1500000)
        self.assertEqual(after2.acknowledged_end,1499999)

    def test_308_regression_overrun_end_and_malformed_ranges_halt(self):
        orig=replace(session(size=100),acknowledged_end=19)
        for headers in (
            {}, {"Range":"bytes=0-10"}, {"Range":"bytes=0-99"},
            {"Range":"bytes=1-40"}, {"Range":"bytes=0-100"},
            {"Range":"bytes=0--1"}, {"Range":"bytes=0-01"},
            {"Range":"0-49"}, {"Range":"bytes=0-1,2-4"},
            {"Range":"bytes=0-30","range":"bytes=0-31"},
            {"Retry-After":"not-validated"},
        ):
            with self.subTest(headers=headers):
                nxt,decision=interpret_fake_status_reply(
                    orig,status_code=308,response_headers=headers)
                self.assertEqual(decision.action,"STOP_NO_NEW_INSERT")
                self.assertEqual(nxt.state,"HALTED_RECONCILIATION")
                self.assertFalse(decision.release_authorized)
                with self.assertRaises(RecoveryRefused):
                    make_status_probe(nxt)

    def test_308_valid_retry_after_is_explicitly_carried_into_resume_plan(self):
        nxt,p=interpret_fake_status_reply(
            session(size=1000),status_code=308,
            response_headers={"Range":"bytes=0-499","Retry-After":"15"})
        self.assertEqual(p.action,"RESUME_EXISTING_SESSION_BYTES_ONLY")
        self.assertEqual(p.min_delay_seconds,15)
        self.assertEqual(p.headers["Content-Range"],"bytes 500-999/1000")
        self.assertEqual(nxt.acknowledged_end,499)

    def test_308_completion_body_is_protocol_violation(self):
        s,d=interpret_fake_status_reply(session(),status_code=308,
                    response_headers={"Range":"bytes=0-12"},
                    response_video=fake_video())
        self.assertEqual((s.state,d.action),
                         ("HALTED_RECONCILIATION","STOP_NO_NEW_INSERT"))

    def test_uncertain_responses_only_query_same_session(self):
        for code in (None,500,502,503,504):
            with self.subTest(code=code):
                nxt,p=interpret_fake_status_reply(session(),status_code=code,
                    response_headers={"Retry-After":"7"})
                self.assertEqual(p.action,"REQUERY_EXISTING_SESSION_ONLY")
                self.assertTrue(p.same_session_only)
                self.assertIn("7 seconds",p.reason)
                self.assertEqual(nxt.transient_responses,1)
                self.assertEqual(p.min_delay_seconds,7)
                self.assertEqual(nxt.state,"PROBE_REQUIRED")

    def test_failure_budget_stops_not_creates_fresh_session(self):
        original=session()
        for attempt in range(4):
            original,p=interpret_fake_status_reply(
                original,status_code=503,response_headers={})
        self.assertEqual(p.action,"STOP_NO_NEW_INSERT")
        self.assertEqual(original.state,"HALTED_RECONCILIATION")
        with self.assertRaises(RecoveryRefused):
            interpret_fake_status_reply(original,status_code=308)

    def test_invalid_retry_after_fails_closed(self):
        for value in ("-1","3601","10000","1.5","Wed, 21 Oct 2015 07:28:00 GMT",
                      " 2","001","bad"):
            with self.subTest(value=value):
                nxt,p=interpret_fake_status_reply(session(),
                    status_code=503,response_headers={"Retry-After":value})
                self.assertEqual(p.action,"STOP_NO_NEW_INSERT")
                self.assertEqual(nxt.state,"HALTED_RECONCILIATION")

    def test_expired_and_other_4xx_never_start_another_insert(self):
        for status in (400,401,403,404,409,410,422,429,499,501):
            with self.subTest(status=status):
                nxt,p=interpret_fake_status_reply(session(),
                    status_code=status,response_headers={})
                self.assertEqual(p.action,"STOP_NO_NEW_INSERT")
                self.assertEqual(nxt.state,"HALTED_RECONCILIATION")
                self.assertTrue(p.same_session_only)

    def test_completion_200_or_201_still_needs_independent_real_readback(self):
        for status in (200,201):
            with self.subTest(status=status):
                nxt,p=interpret_fake_status_reply(
                    session(),status_code=status,response_video=fake_video())
                self.assertEqual(nxt.state,"REMOTE_ID_REPORTED_UNVERIFIED")
                self.assertEqual(nxt.unverified_video_id,VIDEO_ID)
                self.assertEqual(p.returned_video_id_unverified,VIDEO_ID)
                self.assertFalse(nxt.actual_upload_verified)
                self.assertFalse(nxt.release_authorized)
                self.assertFalse(p.actual_video_scheduled)
                with self.assertRaises(RecoveryRefused):
                    make_status_probe(nxt)

    def test_forged_completion_private_channel_or_id_fails(self):
        for video in (None,{},{"id":VIDEO_ID},
                      fake_video("invalid video id"),
                      fake_video(channel="UC"+"Y"*22),
                      fake_video(privacy="public"),
                      fake_video(privacy="unlisted"),
                      fake_video(privacy=None),
                      {"id":VIDEO_ID,"snippet":[],"status":{"privacyStatus":"private"}},
                      {"id":VIDEO_ID,"snippet":{"channelId":CHANNEL},"status":[]}):
            with self.subTest(video=video):
                nxt,p=interpret_fake_status_reply(session(),
                            status_code=201,response_video=video)
                self.assertEqual(p.action,"STOP_NO_NEW_INSERT")
                self.assertEqual(nxt.state,"HALTED_RECONCILIATION")

    def test_unknown_response_and_replayed_state_fail(self):
        s=session()
        for bad in (True,"201",1.5,[]):
            with self.subTest(status=bad),self.assertRaises(RecoveryRefused):
                interpret_fake_status_reply(s,status_code=bad)
        nxt,p=interpret_fake_status_reply(s,status_code=404)
        with self.assertRaises(RecoveryRefused):
            interpret_fake_status_reply(nxt,status_code=201,response_video=fake_video())

    def test_remote_payload_not_allowed_on_transient_status(self):
        nxt,p=interpret_fake_status_reply(session(),status_code=503,
                response_video=fake_video())
        self.assertEqual(p.action,"REQUERY_EXISTING_SESSION_ONLY")
        self.assertFalse(p.actual_video_uploaded)

    def test_case_variant_duplicate_headers_halt(self):
        nxt,p=interpret_fake_status_reply(session(),status_code=308,
                  response_headers={"Range":"bytes=0-2","range":"bytes=0-4"})
        self.assertEqual(p.action,"STOP_NO_NEW_INSERT")
        self.assertEqual(nxt.state,"HALTED_RECONCILIATION")


if __name__ == "__main__":
    unittest.main()
