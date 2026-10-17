"""Synthetic Ed25519 receipt tests. Keys are ephemeral, never production secrets."""
import base64
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import unittest

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from autopilot.core import CHANNEL_ID
from autopilot.phase4d_signed_observations import (
    CollectorTrust, ObservationBlocked, ObservationClaim, SignedObservation,
    _canonical, sanitized_snapshot_hash, verify_readonly_observation_bundle,
)

NOW=datetime(2026,10,17,16,0,tzinfo=timezone.utc)
NONCE="nonce_123456"
HASHES={"d1_schema": "a"*64, "youtube_history":"b"*64}


class Phase4DTests(unittest.TestCase):
    def setUp(self):
        self.records=[]
        self.registry={}
        self.keys={}
        for kind,identity in (("d1_schema","collector_d1"),("youtube_history","collector_youtube")):
            key=Ed25519PrivateKey.generate()
            self.keys[identity]=key
            self.registry[identity]=CollectorTrust(
                collector_id=identity,
                key_id=f"key_{identity}",
                public_key_b64=base64.b64encode(
                    key.public_key().public_bytes(serialization.Encoding.Raw,
                                                  serialization.PublicFormat.Raw)).decode(),
                allowed_kind=kind,
            )
            claim=ObservationClaim(1,kind,CHANNEL_ID,identity,f"key_{identity}",
                                   HASHES[kind],NONCE,
                                   (NOW-timedelta(minutes=1)).isoformat(timespec="seconds"),
                                   (NOW+timedelta(minutes=4)).isoformat(timespec="seconds"))
            self.records.append(SignedObservation(
                claim=claim,signature_b64=base64.b64encode(key.sign(_canonical(claim))).decode()))

    def verify(self,receipts=None,trust=None,hashes=None,nonce=NONCE,now=NOW,seen=frozenset()):
        return verify_readonly_observation_bundle(
            receipts=self.records if receipts is None else receipts,
            trusted_registry=self.registry if trust is None else trust,
            expected_payload_sha256=HASHES if hashes is None else hashes,
            expected_nonce=nonce,already_seen_nonces=seen,now=now)

    def resign(self,number=0,**updates):
        old=self.records[number]
        claim=replace(old.claim,**updates)
        r=SignedObservation(claim,base64.b64encode(
            self.keys[old.claim.collector_id].sign(_canonical(claim))).decode())
        items=list(self.records)
        items[number]=r
        return items

    def test_valid_signatures_are_never_permission_to_migrate(self):
        r=self.verify()
        self.assertTrue(r.signature_integrity_valid)
        self.assertEqual(len(r.collector_ids),2)
        self.assertFalse(r.provider_connection_observed)
        self.assertFalse(r.authenticated_channel_readback)
        self.assertFalse(r.production_migration_ready)
        self.assertFalse(r.production_upload_ready)
        self.assertFalse(r.production_schedule_ready)

    def test_reverse_order_retains_report(self):
        self.assertEqual(self.verify(),self.verify(list(reversed(self.records))))

    def test_missing_receipt_denied(self):
        with self.assertRaises(ObservationBlocked):
            self.verify(self.records[:1])

    def test_duplicate_kind_and_collector_denied(self):
        with self.assertRaises(ObservationBlocked):
            self.verify([self.records[0],self.records[0]])

    def test_wrong_channel_denied(self):
        with self.assertRaises(ObservationBlocked):
            self.verify(self.resign(channel_id="another_channel"))

    def test_explicit_readonly_scope_required(self):
        with self.assertRaises(ObservationBlocked):
            self.verify(self.resign(access_mode="upload"))

    def test_digest_tamper_invalidates_signature(self):
        bad=replace(self.records[0].claim,payload_sha256="c"*64)
        items=[replace(self.records[0],claim=bad),self.records[1]]
        with self.assertRaises(ObservationBlocked):
            self.verify(items,hashes={"d1_schema":"c"*64,"youtube_history":"b"*64})

    def test_digest_changes_must_match_expected(self):
        with self.assertRaises(ObservationBlocked):
            self.verify(hashes={"d1_schema":"c"*64,"youtube_history":"b"*64})

    def test_signature_string_tampered(self):
        original=self.records[1]
        bad=replace(original,signature_b64=base64.b64encode(b"\x00"*64).decode())
        with self.assertRaises(ObservationBlocked):
            self.verify([self.records[0],bad])

    def test_untrusted_or_changed_trust_root_denied(self):
        with self.assertRaises(ObservationBlocked):
            self.verify(trust={"collector_d1":self.registry["collector_d1"]})
        other=Ed25519PrivateKey.generate()
        newpub=base64.b64encode(other.public_key().public_bytes(
            serialization.Encoding.Raw,serialization.PublicFormat.Raw)).decode()
        trust=dict(self.registry)
        trust["collector_d1"]=replace(trust["collector_d1"],public_key_b64=newpub)
        with self.assertRaises(ObservationBlocked):
            self.verify(trust=trust)

    def test_two_collector_identities_cannot_share_one_signing_key(self):
        first_key=self.keys["collector_d1"]
        second_claim=self.records[1].claim
        second_signed=SignedObservation(second_claim,base64.b64encode(
            first_key.sign(_canonical(second_claim))).decode())
        same_key=self.registry["collector_d1"].public_key_b64
        trust=dict(self.registry)
        trust["collector_youtube"]=replace(
            trust["collector_youtube"],public_key_b64=same_key)
        with self.assertRaises(ObservationBlocked):
            self.verify(receipts=[self.records[0],second_signed],trust=trust)

    def test_role_mismatch_denied(self):
        trust=dict(self.registry)
        trust["collector_d1"]=replace(trust["collector_d1"],allowed_kind="youtube_history")
        with self.assertRaises(ObservationBlocked):
            self.verify(trust=trust)

    def test_disabled_collector_denied(self):
        trust=dict(self.registry)
        trust["collector_d1"]=replace(trust["collector_d1"],enabled=False)
        with self.assertRaises(ObservationBlocked):
            self.verify(trust=trust)

    def test_stale_receipt_denied(self):
        with self.assertRaises(ObservationBlocked):
            self.verify(now=NOW+timedelta(minutes=16))

    def test_future_receipt_denied(self):
        items=self.resign(collected_at_utc=(NOW+timedelta(seconds=2)).isoformat(timespec="seconds"))
        with self.assertRaises(ObservationBlocked):
            self.verify(items)

    def test_wrong_or_replayed_nonce_denied(self):
        with self.assertRaises(ObservationBlocked):
            self.verify(nonce="nonce_different")
        with self.assertRaises(ObservationBlocked):
            self.verify(seen=frozenset([NONCE]))

    def test_expired_and_too_long_receipt_denied(self):
        with self.assertRaises(ObservationBlocked):
            self.verify(self.resign(expires_at_utc=(NOW-timedelta(seconds=1)).isoformat(timespec="seconds")))
        with self.assertRaises(ObservationBlocked):
            self.verify(self.resign(expires_at_utc=(NOW+timedelta(hours=1)).isoformat(timespec="seconds")))

    def test_noncanonical_timestamp_denied(self):
        items=self.resign(collected_at_utc="2026-10-17T21:29:00+05:30")
        with self.assertRaises(ObservationBlocked):
            self.verify(items)

    def test_invalid_clock_and_schema_version_denied(self):
        with self.assertRaises(ObservationBlocked):
            self.verify(now=datetime(2026,10,17,16))
        with self.assertRaises(ObservationBlocked):
            self.verify(self.resign(schema_version=True))

    def test_snapshot_hash_deterministic_and_bounded(self):
        self.assertEqual(sanitized_snapshot_hash({"a":1,"b":2}),
                         sanitized_snapshot_hash({"b":2,"a":1}))
        with self.assertRaises(ObservationBlocked):
            sanitized_snapshot_hash({"blob":"a"*260000})


if __name__=="__main__":
    unittest.main()
