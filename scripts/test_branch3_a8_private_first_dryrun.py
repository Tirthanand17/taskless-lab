"""Clivox A8 no-write private-first schedule and idempotency safety tests."""
from __future__ import annotations
from datetime import datetime,timezone
import copy
import json
import unittest
from scripts.branch3_a8_private_first_dryrun import (
    PLAN,LEDGER,CLIVOX,DryRunBlocked,candidate_attempt_key,
    reserve_attempt_preview,reconcile_ambiguous_attempt,
    schedule_preflight,validate_fixture,perform_upload_or_schedule
)

class A8DryRunTests(unittest.TestCase):
    def setUp(self):
        self.plan=json.loads(PLAN.read_text("utf-8"))
        self.ledger=json.loads(LEDGER.read_text("utf-8"))
        self.now=datetime(2026,11,12,12,tzinfo=timezone.utc)

    def test_fixed_synthetic_fixture_never_authorizes_release(self):
        r=validate_fixture(self.plan,self.ledger)
        self.assertEqual(r["actual_youtube_network_calls"],0)
        self.assertFalse(r["real_creator_license_verified"])
        self.assertFalse(r["youtube_upload_authorized"])
        self.assertFalse(r["youtube_schedule_authorized"])
        self.assertFalse(r["youtube_publish_authorized"])
        self.assertEqual(r["future_utc_example_preflight"]["initial_privacy"],"private")
        self.assertFalse(r["persistent_atomic_upload_lock_implemented"])

    def test_wrong_channel_or_fake_release_flags_denied(self):
        for key,value in (
            ("channel_id","UCCcL9Q_jqVq6LJmnYUSAFZA"),
            ("mode","LIVE_YOUTUBE_UPLOAD"),("license_status","VERIFIED"),
            ("owner_exact_asset_signature_verified",True),
            ("owner_google_upload_oauth_verified",True),
            ("github_protected_release_environment_verified",True),
            ("real_media_sha256","a"*64),
            ("metadata_sha256","b"*64),
            ("rights_evidence_sha256","c"*64),
            ("publish_at_is_not_a_real_schedule",False),
        ):
            p=copy.deepcopy(self.plan);p[key]=value
            with self.subTest(key=key),self.assertRaises(DryRunBlocked):
                validate_fixture(p,self.ledger)

    def test_all_media_and_youtube_operations_disabled(self):
        for key in self.plan["production_actions"]:
            p=copy.deepcopy(self.plan)
            p["production_actions"][key]=True
            with self.subTest(key=key),self.assertRaises(DryRunBlocked):
                validate_fixture(p,self.ledger)
        with self.assertRaises(DryRunBlocked):
            perform_upload_or_schedule()

    def test_no_fake_atomic_ledger_or_remote_readback(self):
        for key,value in (
            ("atomic_persistent_lock_enabled",True),
            ("remote_api_writes",1),
            ("reservations",[{"key":"a"*64,"status":"ATTEMPT_RESERVED"}]),
            ("remote_video_ids",["ABCDEFGHIJK"]),
        ):
            ledger=copy.deepcopy(self.ledger);ledger[key]=value
            with self.subTest(key=key),self.assertRaises(DryRunBlocked):
                validate_fixture(self.plan,ledger)

    def test_future_utc_private_first_only(self):
        self.assertTrue(schedule_preflight("2026-11-12T13:00:00Z",self.now)["future_utc_timestamp_valid"])
        for when in (
            "2026-11-12T11:59:59Z",
            "2026-11-12T12:00:00Z",
            "2026-11-12T12:30:00Z",
            "2026-11-12T17:40:00+05:30",
            "bad-time",
        ):
            with self.subTest(when=when),self.assertRaises(DryRunBlocked):
                schedule_preflight(when,self.now)
        for privacy in ("public","unlisted",None):
            with self.subTest(privacy=privacy),self.assertRaises(DryRunBlocked):
                schedule_preflight("2026-11-12T13:00:00Z",self.now,privacy=privacy)
        with self.assertRaises(DryRunBlocked):
            schedule_preflight("2026-11-12T13:00:00Z",
                              datetime(2026,11,12,12))
        with self.assertRaises(DryRunBlocked):
            schedule_preflight("2026-11-12T13:00:00Z",self.now,
                              target_channel_id="UCCcL9Q_jqVq6LJmnYUSAFZA")

    def test_release_digest_key_is_stable_and_exact(self):
        data=dict(channel_id=CLIVOX,release_id="clivox_test_exact_release_v1",
                  media_sha256="a"*64,metadata_sha256="b"*64,
                  rights_evidence_sha256="c"*64)
        key=candidate_attempt_key(**data)
        self.assertEqual(len(key),64)
        self.assertEqual(key,candidate_attempt_key(**data))
        for part,value in (
            ("media_sha256","d"*64),("metadata_sha256","e"*64),
            ("rights_evidence_sha256","f"*64),
            ("release_id","clivox_test_exact_release_v2")
        ):
            mutated=dict(data);mutated[part]=value
            with self.subTest(part=part):
                self.assertNotEqual(key,candidate_attempt_key(**mutated))
        data["channel_id"]="UCCcL9Q_jqVq6LJmnYUSAFZA"
        with self.assertRaises(DryRunBlocked):
            candidate_attempt_key(**data)

    def test_duplicate_or_ambiguous_attempt_never_blindly_retried(self):
        key="a"*64
        first=reserve_attempt_preview([],key)
        self.assertEqual(first["decision"],"DRY_RUN_ONLY_KEY_NOT_PRESENT")
        self.assertFalse(first["upload_authorized"])
        for status in (
            "ATTEMPT_RESERVED","UNKNOWN_REMOTE_STATE_RECONCILE",
            "PRIVATE_UPLOADED_CONFIRMED","SCHEDULED_CONFIRMED",
        ):
            existing=[{"key":key,"status":status}]
            report=reserve_attempt_preview(existing,key)
            self.assertEqual(report["decision"],"BLOCK_DUPLICATE_OR_AMBIGUOUS_ATTEMPT")
            self.assertFalse(report["automatic_retry_allowed"])
            for asserted_readback in (False,True):
                x=reconcile_ambiguous_attempt(
                    attempt_status=status,remote_readback_verified=asserted_readback)
                self.assertFalse(x["blind_retry_allowed"])
                self.assertFalse(x["upload_authorized"])

    def test_idempotency_fails_closed_for_invalid_input(self):
        with self.assertRaises(DryRunBlocked):
            reserve_attempt_preview([], "not-a-key")
        with self.assertRaises(DryRunBlocked):
            reserve_attempt_preview([{"key":"a"*64,"status":"UNKNOWN"}], "a"*64)
        with self.assertRaises(DryRunBlocked):
            reconcile_ambiguous_attempt(attempt_status="SAFE_TO_RETRY",
                                        remote_readback_verified=True)

if __name__=="__main__":
    unittest.main()
