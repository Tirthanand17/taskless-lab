"""Synthetic two-connection SQLite lease proof, NOT cloud concurrency proof."""
from unittest.mock import patch
import sqlite3
import unittest

from autopilot.agent_org import WorkflowError
from autopilot.cloud_single_writer_lease_shadow import (
    _claim,_fence,_open_pair,rehearse_in_memory_writer_fencing,
)


class ShadowSingleWriterFenceTests(unittest.TestCase):
    def pair(self):
        a,b=_open_pair()
        self.addCleanup(a.close)
        self.addCleanup(b.close)
        return a,b

    def test_two_distinct_in_memory_connections_rehearse_fence_lifecycle(self):
        r=rehearse_in_memory_writer_fencing()
        self.assertEqual(r["different_sqlite_connections"],2)
        self.assertTrue(r["synthetic_writer_conflict_denied"])
        self.assertTrue(r["synthetic_epoch_takeover_monotonic"])
        self.assertTrue(r["synthetic_stale_worker_fenced"])
        self.assertTrue(r["synthetic_expired_worker_fenced"])
        for key in (
            "real_D1_writer_or_lease_deployed",
            "real_cloud_lease_atomicity_verified",
            "network_partition_or_clock_skew_safety_proven",
            "external_publisher_fencing_integrated",
            "cloud_backup_restore_verified",
            "upload_retry_authorized",
            "youtube_upload_or_publish_authorized",
        ):
            self.assertFalse(r[key])
        self.assertEqual(r["cloud_database_writes"],0)
        self.assertEqual(r["external_api_requests"],0)

    def test_two_owners_cannot_both_claim_unexpired_token(self):
        a,b=self.pair()
        t1=_claim(a,"shadow_writer_one",100,10)
        self.assertEqual(t1,1)
        with self.assertRaises(WorkflowError):
            _claim(b,"shadow_writer_two",101,10)
        _fence(a,"shadow_writer_one",t1,105)
        with self.assertRaises(WorkflowError):
            _fence(b,"shadow_writer_two",t1,105)

    def test_expired_owner_cannot_use_old_token_after_takeover(self):
        a,b=self.pair()
        old=_claim(a,"shadow_writer_one",100,10)
        fresh=_claim(b,"shadow_writer_two",110,10)
        self.assertGreater(fresh,old)
        with self.assertRaises(WorkflowError):
            _fence(a,"shadow_writer_one",old,111)
        _fence(b,"shadow_writer_two",fresh,111)

    def test_expired_epoch_alone_without_takeover_is_also_denied(self):
        a,_=self.pair()
        epoch=_claim(a,"shadow_writer_one",100,2)
        _fence(a,"shadow_writer_one",epoch,101)
        with self.assertRaises(WorkflowError):
            _fence(a,"shadow_writer_one",epoch,102)

    def test_same_owner_must_claim_new_epoch_after_expiry(self):
        a,_=self.pair()
        old=_claim(a,"shadow_writer_one",100,3)
        new=_claim(a,"shadow_writer_one",103,3)
        self.assertEqual(new,old+1)
        with self.assertRaises(WorkflowError):
            _fence(a,"shadow_writer_one",old,104)
        _fence(a,"shadow_writer_one",new,104)

    def test_explicit_owner_clock_duration_and_epoch_validation(self):
        a,_=self.pair()
        for owner in ("unknown",None,""):
            with self.subTest(owner=owner),self.assertRaises(WorkflowError):
                _claim(a,owner,10,5)
        for tick,ttl in ((-1,10),(True,10),(10,0),(10,3601),
                         (10,"10"),(10**12,10)):
            with self.subTest(tick=tick,ttl=ttl),self.assertRaises(WorkflowError):
                _claim(a,"shadow_writer_one",tick,ttl)
        t=_claim(a,"shadow_writer_one",100,5)
        for epoch in (0,True,None,t+1):
            with self.subTest(epoch=epoch),self.assertRaises(WorkflowError):
                _fence(a,"shadow_writer_one",epoch,102)

    def test_failed_conflicting_transaction_does_not_poison_next_claim(self):
        a,b=self.pair()
        original=_claim(a,"shadow_writer_one",100,10)
        with self.assertRaises(WorkflowError):
            _claim(b,"shadow_writer_two",105,10)
        takeover=_claim(b,"shadow_writer_two",110,10)
        self.assertEqual(takeover,original+1)
        _fence(b,"shadow_writer_two",takeover,111)

    def test_shadow_database_uri_is_memory_only_never_a_user_disk_path(self):
        original=sqlite3.connect
        called=[]
        def spy(db,*args,**kwargs):
            called.append((db,kwargs.get("uri",False)))
            return original(db,*args,**kwargs)
        with patch("autopilot.cloud_single_writer_lease_shadow.sqlite3.connect",
                   side_effect=spy):
            rehearse_in_memory_writer_fencing()
        self.assertEqual(len(called),2)
        for name,uri in called:
            self.assertTrue(name.startswith("file:fm-lease-"))
            self.assertTrue(name.endswith("?mode=memory&cache=shared"))
            self.assertIs(uri,True)


if __name__=="__main__":
    unittest.main()
