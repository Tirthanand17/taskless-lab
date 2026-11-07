"""B4f1 ephemeral in-memory test keys ONLY; never store/sign owner production data."""
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
import unittest

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from scripts.owner_signed_release_b4f1 import (
    CHECKS, INTENT, SCHEMA, OwnerSignatureRejected,
    canonical_owner_release_bytes, verify_owner_release_signature,
)

NOW=datetime(2026,11,7,4,0,tzinfo=timezone.utc)
CHANNEL="UC"+"x"*22
META="d"*64
VIDEO="a"*64
SRT="b"*64
THUMB="c"*64
EPISODE="fm_20261108_short_am"
TIME="2026-11-08T05:30:00Z"


def fixture():
    private=Ed25519PrivateKey.generate()  # fake test-only in-memory material
    pub=private.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw).hex()
    fields={
        "intent":INTENT,
        "channel_id":CHANNEL,
        "episode_id":EPISODE,
        "mp4_sha256":VIDEO,
        "srt_sha256":SRT,
        "thumbnail_sha256":THUMB,
        "metadata_sha256":META,
        "publish_at_utc":TIME,
        "signed_at_utc":"2026-11-07T03:30:00Z",
        "expires_at_utc":"2026-11-09T03:30:00Z",
        "checks":{key:True for key in CHECKS},
    }
    envelope={
        "schema":SCHEMA,
        "payload":fields,
        "signature_hex":private.sign(canonical_owner_release_bytes(fields)).hex(),
    }
    approval={"signed_owner_release":envelope,**{key:True for key in CHECKS}}
    expected=dict(channel_id=CHANNEL,episode_id=EPISODE,mp4_sha256=VIDEO,
                  srt_sha256=SRT,thumbnail_sha256=THUMB,metadata_sha256=META,
                  publish_at_utc=TIME,now=NOW,public_key_hex=pub)
    return approval,expected


class SignedOwnerReleaseTests(unittest.TestCase):
    def test_fake_test_signature_round_trip_never_authorizes_upload_by_itself(self):
        approval,expected=fixture()
        result=verify_owner_release_signature(approval,**expected)
        self.assertTrue(result["signed_exact_bytes_channel_and_schedule_verified"])
        self.assertFalse(result["independent_source_facts_or_rights_review_proven"])
        self.assertFalse(result["youtube_upload_authorized_by_this_function"])

    def test_absent_public_key_signature_or_owner_checkbox_fails_closed(self):
        for edit in (
            lambda a,x:a.pop("signed_owner_release"),
            lambda a,x:x.update(public_key_hex=None),
            lambda a,x:a["signed_owner_release"].update(signature_hex="0"*128),
            lambda a,x:a.update(owner_publish_authorized=False),
            lambda a,x:a.update(owner_rejected_current_candidate=True),
        ):
            approval,expected=fixture();edit(approval,expected)
            with self.assertRaises(OwnerSignatureRejected):
                verify_owner_release_signature(approval,**expected)

    def test_change_any_signed_media_or_channel_or_time_rejected(self):
        for key, new in (
            ("mp4_sha256","e"*64),
            ("srt_sha256","e"*64),
            ("thumbnail_sha256","e"*64),
            ("metadata_sha256","e"*64),
            ("channel_id","UC"+"y"*22),
            ("episode_id","fm_20261108_short_pm"),
            ("publish_at_utc","2026-11-08T10:30:00Z"),
            ("signed_at_utc","2026-11-07T03:35:00Z"),
            ("expires_at_utc","2026-11-09T03:35:00Z"),
        ):
            approval,expected=fixture()
            approval["signed_owner_release"]["payload"][key]=new
            with self.subTest(key=key),self.assertRaises(OwnerSignatureRejected):
                verify_owner_release_signature(approval,**expected)

    def test_expected_media_mismatch_blocks_even_with_valid_signature(self):
        for key,new in (
            ("mp4_sha256","e"*64),("srt_sha256","e"*64),
            ("thumbnail_sha256","e"*64),("metadata_sha256","e"*64),
            ("channel_id","UC"+"z"*22),
            ("episode_id","wrong_episode_id"),
            ("publish_at_utc","2026-11-09T05:30:00Z"),
        ):
            approval,expected=fixture();expected[key]=new
            with self.subTest(key=key),self.assertRaises(OwnerSignatureRejected):
                verify_owner_release_signature(approval,**expected)

    def test_signed_but_stale_or_replayed_release_blocks(self):
        for when in (
            datetime(2026,11,6,2,tzinfo=timezone.utc),
            datetime(2026,11,9,4,tzinfo=timezone.utc),
            datetime(2026,11,8,5,29,tzinfo=timezone.utc),
        ):
            approval,expected=fixture()
            expected["now"]=when
            with self.subTest(when=when),self.assertRaises(OwnerSignatureRejected):
                verify_owner_release_signature(approval,**expected)

    def test_signed_owner_review_cannot_extend_expiry_without_resigning(self):
        approval,expected=fixture()
        approval["signed_owner_release"]["payload"]["expires_at_utc"]="2026-11-12T03:30:00Z"
        with self.assertRaises(OwnerSignatureRejected):
            verify_owner_release_signature(approval,**expected)

    def test_signed_envelope_rejects_unknown_authority_fields(self):
        approval,expected=fixture()
        approval["signed_owner_release"]["autonomous_uploads_allowed"]=True
        with self.assertRaises(OwnerSignatureRejected):
            verify_owner_release_signature(approval,**expected)

    def test_signed_payload_extra_fields_or_forged_pass_rejected(self):
        approval,expected=fixture()
        approval["signed_owner_release"]["payload"]["extra"]="ignored?"
        with self.assertRaises(OwnerSignatureRejected):
            verify_owner_release_signature(approval,**expected)
        approval,expected=fixture()
        approval["signed_owner_release"]["payload"]["checks"]["rights_cleared"]=False
        with self.assertRaises(OwnerSignatureRejected):
            verify_owner_release_signature(approval,**expected)

    def test_signature_from_wrong_key_does_not_pass(self):
        approval,expected=fixture()
        other=Ed25519PrivateKey.generate()
        expected["public_key_hex"]=other.public_key().public_bytes(
            serialization.Encoding.Raw,serialization.PublicFormat.Raw).hex()
        with self.assertRaises(OwnerSignatureRejected):
            verify_owner_release_signature(approval,**expected)

    def test_manual_publisher_verifies_signature_before_oauth_and_insert(self):
        code=(Path(__file__).resolve().parent/"publish_youtube.py").read_text()
        self.assertLess(code.index("verify_owner_release_signature("),
                        code.index("youtube=load_service()"))
        self.assertLess(code.index("verify_owner_release_signature("),
                        code.index("req=youtube.videos().insert("))
        self.assertIn("FLOWMINUTE_OWNER_RELEASE_ED25519_PUBLIC_HEX",code)
        workflow=(Path(__file__).resolve().parents[1]/
            ".github/workflows/publish-artifact-youtube.yml").read_text()
        self.assertIn("FLOWMINUTE_OWNER_RELEASE_ED25519_PUBLIC_HEX",workflow)


if __name__=="__main__":
    unittest.main()
