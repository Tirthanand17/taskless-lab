"""D1-shaped atomic conditional SQL tests in TWO local RAM-only SQLite sessions.

These do not prove actual D1 Worker behavior, distributed clocks or YouTube
external side effects. No real API, files, cloud schema migrations or tokens.
"""
from unittest.mock import patch
import sqlite3
import unittest

from autopilot.agent_org import WorkflowError
from autopilot.cloud_d1_cas_lease_design import (
    CLAIM_SQL,RENEW_SQL,RESERVE_UPLOAD_SQL,
    open_disposable_d1_cas_model,
    claim_shadow_d1_lease,renew_shadow_d1_lease,
    reserve_shadow_upload_once,
    rehearse_d1_conditional_lease_and_upload_reservation,
)

A="A"*32
B="B"*32
DATE="2026-10-20"
EP="tutorial_short_en"
SHA="a"*64


class D1CASLeaseModelTests(unittest.TestCase):
    def open_pair(self):
        a,b=open_disposable_d1_cas_model()
        self.addCleanup(a.close)
        self.addCleanup(b.close)
        return a,b

    def claim(self,conn,owner=A,expected=0,tick=100,ttl=10):
        return claim_shadow_d1_lease(
            conn,nonce=owner,expected_epoch=expected,
            now_tick=tick,ttl_seconds=ttl,
        )

    def reserve(self,conn,owner=A,epoch=1,tick=101,sha=SHA):
        return reserve_shadow_upload_once(
            conn,nonce=owner,epoch=epoch,now_tick=tick,
            release_date=DATE,episode_id=EP,media_sha256=sha,
        )

    def test_end_to_end_disposable_d1_cas_and_upload_reservation(self):
        result=rehearse_d1_conditional_lease_and_upload_reservation()
        self.assertTrue(result["single_statement_claim_conflict_rejected"])
        self.assertTrue(result["same_owner_live_lease_renewal_rehearsed"])
        self.assertTrue(result["monotonic_epoch_takeover_rehearsed"])
        self.assertTrue(result["stale_epoch_release_reservation_rejected"])
        self.assertTrue(result["duplicate_upload_reservation_rejected"])
        self.assertEqual(result["shadow_final_release_state"],"upload_started")
        for forbidden in (
            "real_d1_schema_migrated","real_d1_statement_execution_verified",
            "real_cloud_consistency_or_clock_proven",
            "durable_exclusive_cloud_publisher_verified",
            "actual_youtube_upload_attempted",
            "external_http_side_effect_fenced",
            "lost_youtube_ack_safe_to_retry","publishing_authorized",
        ):
            self.assertFalse(result[forbidden])
        self.assertEqual(result["cloud_database_writes"],0)
        self.assertEqual(result["external_api_requests"],0)
        self.assertNotIn(A,str(result))
        self.assertNotIn(SHA,str(result))

    def test_competing_claim_same_epoch_only_one_succeeds(self):
        a,b=self.open_pair()
        self.assertEqual(self.claim(a),1)
        with self.assertRaises(WorkflowError):
            self.claim(b,owner=B)
        self.assertEqual(a.execute(
            "SELECT fence_epoch FROM fm_release_lease_shadow"
        ).fetchone(),(1,))

    def test_wrong_epoch_even_after_expiration_rejected(self):
        a,b=self.open_pair()
        self.claim(a)
        for guess in (0,2,3):
            with self.subTest(epoch=guess),self.assertRaises(WorkflowError):
                self.claim(b,owner=B,expected=guess,tick=110)
        self.assertEqual(self.claim(b,owner=B,expected=1,tick=110),2)

    def test_renew_unexpired_owner_extends_deadline(self):
        a,b=self.open_pair()
        first=self.claim(a)
        renew_shadow_d1_lease(
            a,nonce=A,epoch=first,now_tick=105,ttl_seconds=10
        )
        with self.assertRaises(WorkflowError):
            self.claim(b,owner=B,expected=first,tick=110)
        self.assertEqual(
            self.claim(b,owner=B,expected=first,tick=115),2)

    def test_stale_or_wrong_owner_cannot_renew(self):
        a,b=self.open_pair()
        ep=self.claim(a)
        for owner,epoch,tick in ((B,ep,105),(A,ep+1,105),(A,ep,110)):
            with self.subTest(owner=owner,epoch=epoch,tick=tick):
                with self.assertRaises(WorkflowError):
                    renew_shadow_d1_lease(
                        b,nonce=owner,epoch=epoch,now_tick=tick,ttl_seconds=5)
        renew_shadow_d1_lease(
            a,nonce=A,epoch=ep,now_tick=105,ttl_seconds=10)

    def test_stale_writer_cannot_reserve_after_takeover(self):
        a,b=self.open_pair()
        self.claim(a)
        self.claim(b,owner=B,expected=1,tick=110)
        with self.assertRaises(WorkflowError):
            self.reserve(a,owner=A,epoch=1,tick=111)
        self.reserve(b,owner=B,epoch=2,tick=111)
        self.assertEqual(b.execute(
            "SELECT stage FROM fm_releases_shadow"
        ).fetchone(),("upload_started",))

    def test_duplicate_reservation_and_media_digest_mismatch_fail_closed(self):
        a,b=self.open_pair()
        self.claim(a)
        with self.assertRaises(WorkflowError):
            self.reserve(a,sha="b"*64)
        self.reserve(a)
        with self.assertRaises(WorkflowError):
            self.reserve(b)
        self.assertEqual(a.execute(
            "SELECT stage FROM fm_releases_shadow"
        ).fetchone(),("upload_started",))

    def test_expired_or_unclaimed_lease_cannot_reserve(self):
        a,_=self.open_pair()
        with self.assertRaises(WorkflowError):
            self.reserve(a)
        self.claim(a)
        with self.assertRaises(WorkflowError):
            self.reserve(a,tick=110)
        self.assertEqual(a.execute(
            "SELECT stage FROM fm_releases_shadow"
        ).fetchone(),("media_qa_passed",))

    def test_bad_nonce_epoch_time_ttl_stage_and_media_denied(self):
        a,_=self.open_pair()
        for owner,epoch,tick,ttl in (
            ("A"*12,0,100,10),(A,True,100,10),
            (A,-1,100,10),(A,0,True,10),
            (A,0,100,0),(A,0,100,3601),
            (A,0,10**12,10),
        ):
            with self.subTest(owner=owner,epoch=epoch,tick=tick,ttl=ttl):
                with self.assertRaises(WorkflowError):
                    self.claim(a,owner=owner,expected=epoch,tick=tick,ttl=ttl)
        ep=self.claim(a)
        for sha in ("bad","g"*64,123):
            with self.subTest(sha=str(sha)),self.assertRaises(WorkflowError):
                self.reserve(a,epoch=ep,sha=sha)

    def test_sql_is_fixed_bounded_prepared_update_with_no_remote_endpoint(self):
        for sql in (CLAIM_SQL,RENEW_SQL,RESERVE_UPLOAD_SQL):
            self.assertEqual(sql.strip().split()[0],"UPDATE")
            self.assertIn("WHERE",sql)
            self.assertNotIn("DELETE",sql)
            self.assertNotIn("DROP",sql)
            self.assertNotIn("INSERT",sql)
            self.assertNotIn("BEGIN",sql)
            self.assertNotIn("SELECT *",sql)
            self.assertLess(len(sql),100000)
            self.assertLess(sql.count("?"),100)
        self.assertIn("stage='media_qa_passed'",RESERVE_UPLOAD_SQL)
        self.assertIn("fence_epoch=?",RESERVE_UPLOAD_SQL)

    def test_sqlite_connections_are_disposable_mode_memory_only(self):
        called=[]
        original=sqlite3.connect
        def spy(name,*args,**kwargs):
            called.append((name,kwargs))
            return original(name,*args,**kwargs)
        with patch("autopilot.cloud_d1_cas_lease_design.sqlite3.connect",
                   side_effect=spy):
            rehearse_d1_conditional_lease_and_upload_reservation()
        self.assertEqual(len(called),2)
        for name,kw in called:
            self.assertTrue(name.startswith("file:flowminute-d1-cas-"))
            self.assertTrue(name.endswith("?mode=memory&cache=shared"))
            self.assertIs(kw["uri"],True)


if __name__=="__main__":
    unittest.main()
