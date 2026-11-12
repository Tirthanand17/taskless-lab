"""Adversarial release signature tests (ephemeral generated test keys ONLY)."""
from __future__ import annotations
import base64
from datetime import datetime,timezone
import json
import unittest

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from scripts.branch3_a6_signed_release import (
    FIXTURE,POLICY,ReleaseBlocked,signing_payload,verify_signature,
    validate_quarantine_manifest,validate_future_release_time,production_release,
)

def inputs():
    return json.loads(FIXTURE.read_text("utf-8")),json.loads(POLICY.read_text("utf-8"))

ARGS=dict(
    channel_id="UCfPEvy0SefE_5nNlYlY_CyQ",
    release_id="clivox_test_original_demo_v1",
    video_sha256="a"*64,metadata_sha256="b"*64,rights_sha256="c"*64,
    privacy="private",publish_at_utc="2026-11-14T11:00:00Z"
)

class TestA6SignatureSafety(unittest.TestCase):
    def test_all_real_release_actions_stay_blocked(self):
        m,p=inputs()
        r=validate_quarantine_manifest(m,p)
        self.assertEqual(r["status"],"HOLD_MISSING_LICENSE_AND_OWNER_SIGNATURE")
        for field in ("video_download_authorized","video_upload_authorized",
                      "youtube_schedule_authorized","youtube_publish_authorized"):
            self.assertFalse(r[field])
        with self.assertRaises(ReleaseBlocked):
            production_release(m)

    def test_canonical_signature_round_trip_is_only_math_not_rights(self):
        key=Ed25519PrivateKey.generate()  # local ephemeral test-only key
        pub=key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        payload=signing_payload(**ARGS)
        sig=base64.b64encode(key.sign(payload)).decode("ascii")
        self.assertTrue(verify_signature(payload,sig,pub))
        self.assertEqual(payload,signing_payload(**dict(ARGS)))
        with self.assertRaises(ReleaseBlocked):
            production_release(payload,sig,pub)

    def test_every_signed_subject_field_is_integrity_bound(self):
        key=Ed25519PrivateKey.generate()
        pub=key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        sig=base64.b64encode(key.sign(signing_payload(**ARGS))).decode("ascii")
        modifications=(
            ("video_sha256","1"*64),("metadata_sha256","2"*64),
            ("rights_sha256","3"*64),
            ("publish_at_utc","2026-11-14T12:00:00Z"),
            ("release_id","clivox_test_original_demo_v2")
        )
        for field,value in modifications:
            changed=dict(ARGS);changed[field]=value
            with self.subTest(field=field):
                self.assertFalse(verify_signature(signing_payload(**changed),sig,pub))
        changed=dict(ARGS);changed["channel_id"]="UCCcL9Q_jqVq6LJmnYUSAFZA"
        with self.assertRaises(ReleaseBlocked):
            signing_payload(**changed)

    def test_wrong_signer_or_corrupted_signature(self):
        payload=signing_payload(**ARGS)
        first=Ed25519PrivateKey.generate()
        another=Ed25519PrivateKey.generate()
        pub=another.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        encoded=base64.b64encode(first.sign(payload)).decode("ascii")
        self.assertFalse(verify_signature(payload,encoded,pub))
        self.assertFalse(verify_signature(payload,base64.b64encode(b"\0"*64).decode("ascii"),pub))
        with self.assertRaises(ReleaseBlocked):
            verify_signature(payload,"%%%BAD",pub)

    def test_no_fake_approval_by_mutating_manifest(self):
        for key,value in (
            ("release_state","APPROVED"),("asset_kind","RIGHTS_CLEARED"),
        ):
            m,p=inputs();m[key]=value
            with self.subTest(key=key),self.assertRaises(ReleaseBlocked):
                validate_quarantine_manifest(m,p)
        for field in ("creator_rights_grant_verified","underlying_rights_cleared",
                      "final_video_human_reviewed"):
            m,p=inputs();m["reviewed"][field]=True
            with self.subTest(field=field),self.assertRaises(ReleaseBlocked):
                validate_quarantine_manifest(m,p)
        for field,value in (
            ("video_sha256","a"*64),("video_bytes",12345),
            ("third_party_footage_present",True)
        ):
            m,p=inputs();m["asset"][field]=value
            with self.subTest(field=field),self.assertRaises(ReleaseBlocked):
                validate_quarantine_manifest(m,p)

    def test_no_false_key_provisioning(self):
        for field,value in (
            ("public_key_id","owner_1"),
            ("owner_signed",True),
            ("detached_signature_base64","AAAA"),
        ):
            m,p=inputs();m["signature"][field]=value
            with self.subTest(field=field),self.assertRaises(ReleaseBlocked):
                validate_quarantine_manifest(m,p)
        m,p=inputs();p["real_owner_signing_public_key_enrolled"]=True
        with self.assertRaises(ReleaseBlocked):
            validate_quarantine_manifest(m,p)

    def test_wrong_channel_public_or_past_schedule(self):
        for field,value in (
            ("target_channel_id","UCCcL9Q_jqVq6LJmnYUSAFZA"),
            ("privacy_status","public"),
            ("publish_at_utc","2026-11-13T10:00:00Z"),
            ("owner_approved_exact_schedule",True),
        ):
            m,p=inputs();m["planned_release"][field]=value
            with self.subTest(field=field),self.assertRaises(ReleaseBlocked):
                validate_quarantine_manifest(m,p)
        now=datetime(2026,11,12,16,00,tzinfo=timezone.utc)
        for when in (
            "2026-11-12T15:59:59Z","2026-11-12T16:20:00Z",
            "2026-11-12T21:40:00+05:30","not-a-date"
        ):
            with self.subTest(when=when),self.assertRaises(ReleaseBlocked):
                validate_future_release_time(when,now=now)
        self.assertTrue(validate_future_release_time("2026-11-13T16:00:00Z",now=now))

    def test_quarantine_enabled_and_all_youtube_actions_disabled(self):
        m,p=inputs()
        for field in (
            "media_download_enabled","youtube_upload_enabled",
            "youtube_schedule_enabled","youtube_publish_enabled",
            "channel_oauth_verified","production_release_key_enrolled",
        ):
            x,y=inputs();x["controls"][field]=True
            with self.subTest(field=field),self.assertRaises(ReleaseBlocked):
                validate_quarantine_manifest(x,y)
        m["controls"]["quarantine_enabled"]=False
        with self.assertRaises(ReleaseBlocked):
            validate_quarantine_manifest(m,p)

if __name__=="__main__":
    unittest.main()
