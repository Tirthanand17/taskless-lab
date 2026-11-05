"""Actual disposable PostgreSQL 16 one-shot mock YouTube upload fence drill.

Dedicated cloud CI invokes the earlier role/bootstrap suite FIRST, then this
suite against its ONLY isolated disposable database. Other pytest suites skip
real PostgreSQL cases without the CI-specific environment flag.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime, time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
import os
import unittest

from autopilot.ci_youtube_attempt_fence import (
    ProtectedCiYouTubeFence, MockYouTubeFenceAuditor,
    MockUploadFenceError, validate_mock_intent,
)
from autopilot.ci_protected_pg_boundary import GATEWAY_ROLE, AUDITOR_ROLE, WORKER_ROLE
from autopilot.test_ci_protected_pg_boundary import (
    ADMIN_DSN, connect_admin, connect_gateway,
    connect_worker, connect_auditor,
)
from autopilot.youtube_private_first_contract import prepare_unapproved_intent

CHANNEL = "UC" + "X" * 22
NOW = datetime.now(timezone.utc)
DAY = (NOW.astimezone(ZoneInfo("Asia/Kolkata"))+timedelta(days=90)).date()
KINDS = {"short_am":(11,0),"long":(16,0),"short_pm":(20,30)}
REMOTE_ID = "abcDEF123_-"


def mock_intent(slot="short_am", episode="original_2035_001", mp4="a"*64,
                channel=CHANNEL):
    hour,minute=KINDS[slot]
    at=datetime.combine(DAY,time(hour,minute),tzinfo=ZoneInfo("Asia/Kolkata"))
    iso=at.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return prepare_unapproved_intent(
        episode_id=episode,slot=slot,channel_id=channel,
        final_mp4_sha256=mp4,captions_srt_sha256="b"*64,
        thumbnail_sha256="c"*64,source_review_context_sha256="d"*64,
        title="An original real-world science demonstration",
        description="Only an imaginary, offline developer test; do not publish",
        language="en",synthetic_media_disclosure=False,
        made_for_kids=False,publish_at_utc=iso,
        now=datetime.now(timezone.utc),
    )


class PureMockIntentGateTests(unittest.TestCase):
    def test_forged_or_release_marked_intent_rejected(self):
        valid=mock_intent()
        validate_mock_intent(valid)
        for intent in (
            replace(valid,context_sha256="e"*64),
            replace(valid,real_youtube_oauth=True),
            replace(valid,real_owner_approval=True),
            replace(valid,release_authorized=True),
            replace(valid,simulation_only=False),
            replace(valid,publish_at_utc="2026-01-01T05:30:00Z"),
        ):
            with self.subTest(intent=intent),self.assertRaises(MockUploadFenceError):
                validate_mock_intent(intent)


@unittest.skipUnless(os.environ.get(ADMIN_DSN), "Requires dedicated disposable PostgreSQL 16 CI service")
class RealPostgresMockFenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with connect_admin() as db:
            with db.cursor() as cur:
                cur.execute("SELECT current_database(), current_user")
                assert tuple(cur.fetchone())==("flowminute_fence_ci","flowminute_test"), (
                    "Never migrate production or non-CI database")
                # 002 roles and their ephemeral passwords were initialized by the
                # prerequisite test_ci_protected_pg_boundary hosted CI command.
                cur.execute("SELECT 1 FROM pg_roles WHERE rolname='fm_ci_owner'")
                assert cur.fetchone() is not None, "Required disposable 002 schema missing"
                path=Path(__file__).parent/"sql"/"003_ci_youtube_mock_attempt_fence.sql"
                cur.execute(path.read_text(encoding="utf-8"))
        cls.gateway=ProtectedCiYouTubeFence(connect_gateway)
        cls.auditor=MockYouTubeFenceAuditor(connect_auditor)

    def setUp(self):
        with connect_admin() as db:
            with db.cursor() as cur:
                cur.execute(
                    "TRUNCATE fm_private_ci.youtube_mock_audit, "
                    "fm_private_ci.youtube_mock_attempts RESTART IDENTITY CASCADE"
                )

    def test_one_committed_reservation_survives_new_connections_and_no_retry(self):
        intent=mock_intent()
        ticket=self.gateway.reserve_mock(intent)
        self.assertNotIn(ticket.ephemeral_token,repr(ticket))
        state=self.auditor.inspect(intent.channel_id,intent.episode_id)
        self.assertEqual((state["state"],state["attempt_count"],state["audit_event_count"]),
                         ("POSSIBLY_SENT_NO_RETRY",1,1))
        self.assertFalse(state["real_youtube_insert_performed"])
        self.assertFalse(state["real_youtube_scheduled"])
        self.assertFalse(state["release_authorized"])
        second_gateway=ProtectedCiYouTubeFence(connect_gateway)
        with self.assertRaises(MockUploadFenceError):
            second_gateway.reserve_mock(intent)

    def test_actual_concurrent_connections_one_wins(self):
        intent=mock_intent()
        def try_one(_index):
            try:
                return self.gateway.reserve_mock(intent)
            except MockUploadFenceError:
                return None
        with ThreadPoolExecutor(max_workers=12) as pool:
            answers=list(pool.map(try_one,range(24)))
        self.assertEqual(sum(ticket is not None for ticket in answers),1)
        state=self.auditor.inspect(intent.channel_id,intent.episode_id)
        self.assertEqual(state["attempt_count"],1)
        self.assertEqual(state["audit_event_count"],1)

    def test_remote_id_report_does_not_remove_fence(self):
        intent=mock_intent()
        ticket=self.gateway.reserve_mock(intent)
        self.assertEqual(
            self.gateway.report_unverified_remote_id(ticket,REMOTE_ID),
            "REMOTE_ID_REPORTED_UNVERIFIED"
        )
        state=self.auditor.inspect(intent.channel_id,intent.episode_id)
        self.assertEqual(state["unverified_remote_video_id"],REMOTE_ID)
        self.assertEqual(state["audit_event_count"],2)
        self.assertFalse(state["real_youtube_processing_verified"])
        with self.assertRaises(MockUploadFenceError):
            ProtectedCiYouTubeFence(connect_gateway).reserve_mock(intent)
        with self.assertRaises(MockUploadFenceError):
            self.gateway.report_unverified_remote_id(ticket,REMOTE_ID)

    def test_wrong_nonce_invalid_id_and_replay_fail_closed(self):
        ticket=self.gateway.reserve_mock(mock_intent())
        with self.assertRaises(MockUploadFenceError):
            self.gateway.report_unverified_remote_id(replace(ticket,ephemeral_token="f"*64),
                                                     REMOTE_ID)
        with self.assertRaises(MockUploadFenceError):
            self.gateway.report_unverified_remote_id(ticket,"wrong")
        with self.assertRaises(MockUploadFenceError):
            self.gateway.report_unverified_remote_id(replace(ticket,release_authorized=True),
                                                     REMOTE_ID)
        self.assertEqual(self.auditor.inspect(ticket.channel_id,ticket.episode_id)["state"],
                         "POSSIBLY_SENT_NO_RETRY")

    def test_unique_slot_context_media_and_remote_id_across_episodes(self):
        self.gateway.reserve_mock(mock_intent())
        for collision in (
            mock_intent(episode="original_2035_002"),  # same IST slot and MP4
            mock_intent(slot="long",episode="original_2035_002"), # same MP4 other slot
        ):
            with self.subTest(collision=collision.slot),self.assertRaises(MockUploadFenceError):
                self.gateway.reserve_mock(collision)
        other=mock_intent(slot="long",episode="original_2035_002",mp4="e"*64)
        self.gateway.reserve_mock(other)
        self.assertEqual(self.auditor.inspect(CHANNEL,other.episode_id)["attempt_count"],1)

    def test_remote_id_global_uniqueness(self):
        first=self.gateway.reserve_mock(mock_intent())
        second=self.gateway.reserve_mock(
            mock_intent(slot="long",episode="original_2035_002",mp4="e"*64))
        self.gateway.report_unverified_remote_id(first,REMOTE_ID)
        with self.assertRaises(MockUploadFenceError):
            self.gateway.report_unverified_remote_id(second,REMOTE_ID)
        self.assertEqual(self.auditor.inspect(CHANNEL,second.episode_id)["state"],
                         "POSSIBLY_SENT_NO_RETRY")

    def test_direct_db_table_privileges_and_stored_function_grants(self):
        with connect_admin() as db:
            with db.cursor() as cur:
                for role in (GATEWAY_ROLE,WORKER_ROLE,AUDITOR_ROLE):
                    for table in ("youtube_mock_attempts","youtube_mock_audit"):
                        for action in ("SELECT","INSERT","UPDATE","DELETE","TRUNCATE"):
                            cur.execute(
                                "SELECT has_table_privilege(%s,%s,%s)",
                                (role,"fm_private_ci."+table,action))
                            self.assertFalse(cur.fetchone()[0],(role,table,action))
                for role in (AUDITOR_ROLE,WORKER_ROLE):
                    cur.execute(
                        "SELECT has_function_privilege(%s,%s,'EXECUTE')",
                        (role,"fm_private_ci.reserve_youtube_mock_once("
                              "text,text,text,timestamp with time zone,"
                              "text,text,text,text,text,text)"))
                    self.assertFalse(cur.fetchone()[0],role)
        with connect_auditor() as db:
            with db.cursor() as cur:
                with self.assertRaises(Exception):
                    cur.execute("INSERT INTO fm_private_ci.youtube_mock_attempts "
                                "(channel_id) VALUES ('FAKE')")

    def test_direct_gateway_bad_slot_or_wrong_time_cannot_bypass_python(self):
        intent=mock_intent()
        params=(
            intent.channel_id,intent.episode_id,"long",intent.publish_at_utc,
            intent.context_sha256,intent.final_mp4_sha256,
            intent.captions_srt_sha256,intent.thumbnail_sha256,
            intent.source_review_context_sha256,"f"*64,
        )
        with connect_gateway() as db:
            with db.cursor() as cur:
                with self.assertRaises(Exception):
                    cur.execute(
                        "SELECT fm_private_ci.reserve_youtube_mock_once("
                        "%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",params)
        with self.assertRaises(MockUploadFenceError):
            self.auditor.inspect(intent.channel_id,intent.episode_id)

    def test_worker_cannot_gain_gateway_function_or_auditor_permissions(self):
        with self.assertRaises(Exception):
            ProtectedCiYouTubeFence(connect_worker)
        with self.assertRaises(Exception):
            MockYouTubeFenceAuditor(connect_worker)
        with self.assertRaises(Exception):
            MockYouTubeFenceAuditor(connect_gateway)

    def test_different_channel_isolated_and_cannot_read_other_channel_as_owner(self):
        other_channel="UC"+"Y"*22
        first=mock_intent()
        other=mock_intent(channel=other_channel)
        self.gateway.reserve_mock(first)
        self.gateway.reserve_mock(other)
        # Test auditors have no actual owner-auth mechanism yet: synthetic
        # redacted fixtures are NOT proof of production per-channel isolation.
        state=self.auditor.inspect(other_channel,other.episode_id)
        self.assertEqual(state["attempt_count"],1)
        self.assertFalse(state["real_owner_oauth_authenticated"])
        self.assertFalse(state["real_cloud_persistence_deployed"])


if __name__=="__main__":
    unittest.main()
