"""A6 mathematical signature tests with per-test ephemeral keys, never production."""
from __future__ import annotations

import base64
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from scripts.branch3_a6_original_handoff import (
    PACKET_NAME, METADATA_NAME, MP4, WAV, SRT, MANIFEST, TECH_QA,
    build_packet
)
from scripts.branch3_a6_original_review_signature import (
    CHECKS, DOMAIN, FIELDS, REQUEST_FILE, EditorialReviewDenied,
    create_unsigned_requests, verify_unsigned_requests, fixture, make_unsigned_review_request,
    payload, strict_review_claim, verify_attestation
)
from scripts.branch3_original_arcade_pilots import (
    CATALOG, sha, validate_catalog
)

NOW=datetime(2026,11,13,16,30,tzinfo=timezone.utc)
REVIEW_TIME="2026-11-13T16:00:00Z"


def ep():
    return validate_catalog(json.loads(CATALOG.read_text("utf-8")))[0]


class A6EditorialSignatureTests(unittest.TestCase):

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.folder=self.root/ep()["id"]
        self.folder.mkdir()
        (self.folder/MP4).write_bytes(b"synthetic-unit-test-mp4")
        (self.folder/WAV).write_bytes(b"synthetic-unit-test-wav")
        (self.folder/SRT).write_bytes(b"synthetic-unit-test-srt")
        (self.folder/MANIFEST).write_text(
            json.dumps({"render_mode":"preview"}),encoding="utf-8"
        )
        self.report={"actual_ffprobe_checks_passed":True,
                     "youtube_upload_authorized":False}
        (self.folder/TECH_QA).write_text(json.dumps(self.report),"utf-8")
        with patch.multiple(
            "scripts.branch3_a6_original_handoff",
            probe=lambda *_:{"fake":"unit-mock"},
            validate_episode_report=lambda *a,**kw:self.report
        ):
            self.packet,self.metadata=build_packet(
                ep(),self.folder,catalog_sha256=sha(CATALOG)
            )
        (self.folder/PACKET_NAME).write_text(json.dumps(self.packet),"utf-8")
        (self.folder/METADATA_NAME).write_text(json.dumps(self.metadata),"utf-8")
        self.unsigned=make_unsigned_review_request(self.packet,self.metadata)
        self.key=Ed25519PrivateKey.generate()
        self.public=self.key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        self.pin=hashlib.sha256(self.public).hexdigest()
        self.body={**self.unsigned,
                   "owner_review_checks":{k:True for k in CHECKS},
                   "owner_review_completed_at_utc":REVIEW_TIME}

    def sign(self,body=None,key=None):
        k=self.key if key is None else key
        return base64.b64encode(
            k.sign(payload(self.body if body is None else body))
        ).decode("ascii")

    def check(self,body=None,signature=None,public=None,pin=None):
        return verify_attestation(
            packet=self.packet,metadata=self.metadata,
            signed_body=self.body if body is None else body,
            signature_b64=self.sign() if signature is None else signature,
            signer_public_key=self.public if public is None else public,
            caller_pinned_public_key_sha256=self.pin if pin is None else pin,
            now=NOW
        )

    def test_unsigned_review_worksheet_is_all_false_and_hash_bound(self):
        self.assertEqual(set(self.unsigned),FIELDS)
        self.assertEqual(self.unsigned["domain"],DOMAIN)
        self.assertEqual(self.unsigned["episode_id"],ep()["id"])
        self.assertEqual(self.unsigned["exact_video_sha256"],
                         self.packet["exact_video_sha256"])
        self.assertEqual(self.unsigned["exact_audio_sha256"],
                         self.packet["exact_audio_sha256"])
        self.assertEqual(self.unsigned["exact_captions_sha256"],
                         self.packet["exact_captions_sha256"])
        self.assertEqual(self.unsigned["exact_metadata_sha256"],
                         self.packet["exact_metadata_sha256"])
        self.assertEqual(self.unsigned["exact_review_packet_sha256"],
                         self.packet["packet_sha256"])
        self.assertEqual(self.unsigned["owner_review_checks"],
                         {k:False for k in CHECKS})
        self.assertIsNone(self.unsigned["owner_review_completed_at_utc"])
        self.assertFalse(self.unsigned["third_party_footage_present"])
        self.assertIn("NO_UPLOAD",self.unsigned["action"])

    def test_ephemeral_ed25519_signature_valid_but_cannot_grant_release(self):
        res=self.check()
        self.assertTrue(res["cryptographic_ed25519_detached_claim_valid"])
        self.assertTrue(res["exact_handoff_video_audio_captions_and_metadata_bound"])
        self.assertFalse(res["owner_signing_identity_independently_enrolled"])
        self.assertFalse(res["claim_of_human_playback_independently_observed"])
        self.assertFalse(res["production_a6_signed_release_issued"])
        self.assertFalse(res["youtube_upload_authorized"])
        self.assertFalse(res["youtube_schedule_authorized"])
        self.assertFalse(res["youtube_publish_authorized"])
        self.assertEqual(res["actual_google_api_calls"],0)
        self.assertNotIn(self.pin,json.dumps(res))
        self.assertNotIn(self.sign(),json.dumps(res))

    def test_unsigned_or_incomplete_claim_is_rejected(self):
        with self.assertRaisesRegex(EditorialReviewDenied,"UNREVIEWED"):
            self.check(self.unsigned)
        for check in CHECKS:
            body=copy.deepcopy(self.body)
            body["owner_review_checks"][check]=False
            with self.subTest(check=check),self.assertRaises(
                EditorialReviewDenied
            ):
                self.check(body)
        for bad in (None,1,"yes",[],{},0):
            body=copy.deepcopy(self.body)
            body["owner_review_checks"]["exact_full_video_watched"]=bad
            with self.subTest(bad=bad),self.assertRaises(EditorialReviewDenied):
                self.check(body)

    def test_tampered_media_voice_caption_metadata_or_owner_packet_denied(self):
        for key,value in (
            ("exact_video_sha256","1"*64),
            ("exact_audio_sha256","2"*64),
            ("exact_captions_sha256","3"*64),
            ("exact_metadata_sha256","4"*64),
            ("exact_review_packet_sha256","5"*64),
            ("channel_id","UCCcL9Q_jqVq6LJmnYUSAFZA"),
            ("episode_id","clivox_fake_other_episode"),
            ("domain","CLIVOX-A8-ATTEMPT"),
            ("action","PUBLISH_AUTOMATICALLY"),
            ("third_party_footage_present",True),
        ):
            body=copy.deepcopy(self.body)
            body[key]=value
            with self.subTest(key=key),self.assertRaises(
                EditorialReviewDenied
            ):
                self.check(body)
        body=copy.deepcopy(self.body)
        body["upload_refresh_token"]="anything"
        with self.assertRaises(EditorialReviewDenied):
            self.check(body)

    def test_change_assertion_after_signing_invalidates_signature(self):
        original_sig=self.sign()
        body=copy.deepcopy(self.body)
        body["owner_review_completed_at_utc"]="2026-11-13T16:01:00Z"
        with self.assertRaisesRegex(EditorialReviewDenied,"INVALID_DETACHED_SIGNATURE"):
            self.check(body,signature=original_sig)
        body=copy.deepcopy(self.body)
        body["owner_review_checks"]["narration_voice_and_sound_reviewed"]=False
        with self.assertRaises(EditorialReviewDenied):
            self.check(body,signature=original_sig)

    def test_wrong_key_or_wrong_owner_pin_fails_closed(self):
        different=Ed25519PrivateKey.generate()
        wrong_pub=different.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        with self.assertRaisesRegex(EditorialReviewDenied,"CALLER_PIN_MISMATCH"):
            self.check(pin="f"*64)
        with self.assertRaisesRegex(EditorialReviewDenied,"INVALID_DETACHED_SIGNATURE"):
            self.check(public=wrong_pub,
                       pin=hashlib.sha256(wrong_pub).hexdigest())
        for value in ("", "bad@@@", "AA==",self.sign()[:-1]+"%"):
            with self.subTest(sig=value),self.assertRaises(EditorialReviewDenied):
                self.check(signature=value)
        with self.assertRaises(EditorialReviewDenied):
            self.check(public=b"a"*12)

    def test_missing_and_future_noncanonical_review_times_fail(self):
        for value in (
            None,"2026-11-13T16:00:00+00:00",
            "2026-11-13T16:00Z","2026-11-13",
            "2026-11-14T20:00:00Z","2020-01-01T00:00:00Z",
            "2026-00-13T16:00:00Z",
        ):
            body=copy.deepcopy(self.body)
            body["owner_review_completed_at_utc"]=value
            with self.subTest(value=value),self.assertRaises(EditorialReviewDenied):
                self.check(body)
        with self.assertRaises(EditorialReviewDenied):
            verify_attestation(
                packet=self.packet,metadata=self.metadata,
                signed_body=self.body,signature_b64=self.sign(),
                signer_public_key=self.public,
                caller_pinned_public_key_sha256=self.pin,
                now=datetime(2026,11,13,16)
            )

    def test_forged_handoff_or_unapproved_metadata_denied(self):
        for key,value in (
            ("owner_detached_signature_present",True),
            ("exact_video_human_review_confirmed",True),
            ("rights_of_all_final_assets_independently_approved",True),
            ("youtube_upload_authorized",True),
            ("packet_sha256","a"*64),
            ("exact_audio_sha256","a"*64),
        ):
            p={**self.packet,key:value}
            with self.subTest(key=key),self.assertRaises(EditorialReviewDenied):
                make_unsigned_review_request(p,self.metadata)
        meta={**self.metadata,"title":"Forged owner title"}
        with self.assertRaises(EditorialReviewDenied):
            make_unsigned_review_request(self.packet,meta)

    def test_no_overwrite_unsigned_request_and_wrong_folder(self):
        with patch(
            "scripts.branch3_a6_original_review_signature.verify_packet",
            return_value={"verified":True}
        ):
            generated=create_unsigned_requests(self.root,selection="one")
            self.assertEqual(generated["unsigned_requests_written"],1)
            self.assertFalse(generated["owner_approval_claimed"])
            self.assertFalse(generated["youtube_upload_authorized"])
            saved=json.loads(
                (self.folder/REQUEST_FILE).read_text("utf-8")
            )
            self.assertEqual(saved,self.unsigned)
            with self.assertRaisesRegex(EditorialReviewDenied,"NO_OVERWRITE"):
                create_unsigned_requests(self.root,selection="one")
        with self.assertRaises(EditorialReviewDenied):
            create_unsigned_requests(Path.cwd(),selection="one")

    def test_downloaded_artifact_unsigned_forms_must_match_exact_rehashed_subject(self):
        # Fake source bytes and mock FFprobe only here; actual render CI
        # executes verify_packet against actual MP4 and FFprobe.
        with patch(
            "scripts.branch3_a6_original_review_signature.verify_packet",
            return_value={"technical_video_verified":True}
        ):
            create_unsigned_requests(self.root,selection="one")
            passed=verify_unsigned_requests(self.root,selection="one")
            self.assertEqual(passed["episode_count"],1)
            self.assertTrue(passed["unsigned_checklist_files_matched_exact_media"])
            self.assertEqual(passed["actual_human_video_approvals_verified"],0)
            self.assertFalse(passed["youtube_upload_authorized"])
            self.assertFalse(passed["youtube_publish_authorized"])
            target=self.folder/REQUEST_FILE
            original=target.read_text("utf-8")
            wrong=json.loads(original)
            wrong["owner_review_checks"]["exact_full_video_watched"]=True
            target.write_text(json.dumps(wrong),encoding="utf-8")
            with self.assertRaisesRegex(EditorialReviewDenied,
                                        "CHANGED_OR_FORGED_UNSIGNED"):
                verify_unsigned_requests(self.root,selection="one")
            target.write_text(original,encoding="utf-8")
            wrong=json.loads(original)
            wrong["exact_video_sha256"]="f"*64
            target.write_text(json.dumps(wrong),encoding="utf-8")
            with self.assertRaisesRegex(EditorialReviewDenied,
                                        "CHANGED_OR_FORGED_UNSIGNED"):
                verify_unsigned_requests(self.root,selection="one")
            target.write_text(original,encoding="utf-8")
            altered_metadata={**self.metadata,"title":"Injected false title"}
            (self.folder/METADATA_NAME).write_text(
                json.dumps(altered_metadata),encoding="utf-8")
            with self.assertRaises(EditorialReviewDenied):
                verify_unsigned_requests(self.root,selection="one")
            (self.folder/METADATA_NAME).write_text(
                json.dumps(self.metadata),encoding="utf-8")
            self.assertTrue(verify_unsigned_requests(
                self.root,selection="one"
            )["unsigned_checklist_files_matched_exact_media"])
            target.unlink()
            target.symlink_to(self.folder/METADATA_NAME)
            with self.assertRaisesRegex(EditorialReviewDenied,
                                        "MISSING_UNSIGNED_REVIEW"):
                verify_unsigned_requests(self.root,selection="one")
            target.unlink()
            target.write_text(original,encoding="utf-8")
            with self.assertRaises(EditorialReviewDenied):
                verify_unsigned_requests(Path.cwd(),selection="one")

    def test_quarantined_fixture_remains_unsigned(self):
        v=fixture()
        self.assertTrue(v["fixed_video_audio_caption_metadata_binding_implemented"])
        self.assertFalse(v["owner_trusted_public_key_independently_enrolled"])
        self.assertFalse(v["real_owner_review_verified"])
        self.assertFalse(v["real_signed_release_issued"])
        self.assertEqual(v["actual_google_api_calls"],0)
        self.assertFalse(v["youtube_upload_authorized"])
        self.assertFalse(v["youtube_publish_authorized"])


if __name__=="__main__":
    unittest.main()
