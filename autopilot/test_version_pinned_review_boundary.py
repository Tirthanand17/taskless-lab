"""B3d4c2d2 adversarial seven-role synthetic signer + immutable S3 version tests.

No real identity, no human source review, no real MP4 bytes. Generated
private Ed25519 keys exist only in memory inside isolated GitHub runner.
"""
from __future__ import annotations

import base64
from copy import deepcopy
from dataclasses import asdict,replace
from datetime import datetime,timedelta,timezone
from hashlib import sha256
import json
import math
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from autopilot.mock_final_editorial_review import ROLES
from autopilot.primary_sourced_storyboards import canonical
from autopilot.test_private_versioned_media_escrow import CONFIG,FakeS3,fixture
from autopilot.private_versioned_media_escrow import (
    prepare_exact_private_escrow,escrow_once_and_readback,
)
from autopilot.version_pinned_review_boundary import (
    PURPOSE,DOMAIN,ExternalMockReviewer,VersionBoundMockReviewClaim,
    DetachedVersionBoundMockReview,VersionedReviewError,
    reconstruct_version_bound_review_context,verify_version_bound_mock_reviews,
    mock_registry_digest,_strict_json,
)

NOW=datetime(2026,11,4,16,0,tzinfo=timezone.utc)
EXCLUDED=frozenset(("model_agent","publisher_agent","script_creator","untrusted_reviewer"))


def register_fake_people():
    """A synthetic key-pair table, never a real-world human/owner enrollment."""
    registry={}
    private={}
    for i,role in enumerate(ROLES):
        key=Ed25519PrivateKey.generate()
        rid=f"fake_reviewer_{i+1:02d}"
        kid=f"fake_key_{i+1:02d}"
        pub=key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        registry[rid]=ExternalMockReviewer(
            reviewer_id=rid,key_id=kid,role=role,
            public_ed25519_b64=base64.b64encode(pub).decode(),
        )
        private[rid]=key
    return registry,private


def fake_signed_reviews(context:dict,registry:dict,private:dict,
                        *,now:datetime=NOW,
                        overrides:dict|None=None,
                        sign_domain:bytes=DOMAIN):
    overrides=overrides or {}
    rec=[]
    for i,role in enumerate(ROLES):
        rid=f"fake_reviewer_{i+1:02d}"
        kwargs=dict(
            purpose=PURPOSE,
            episode_id=context["episode_id"],
            context_sha256=context["version_bound_review_context_sha256"],
            role=role,
            role_binding_sha256=sha256(canonical({
                "purpose":PURPOSE,"role":role,
                "version_bound_review_context_sha256":
                    context["version_bound_review_context_sha256"],
            })).hexdigest(),
            reviewer_id=rid,key_id=registry[rid].key_id,
            receipt_id=f"fake_receipt_{i+1:02d}",
            decision="MOCK_ACCEPT",
            notes="Synthetic test-only signature, never an actual human content decision.",
            signed_at_utc=(now-timedelta(minutes=8)).isoformat(),
            expires_at_utc=(now+timedelta(hours=3)).isoformat(),
            claimed_full_watch_seconds=(
                math.ceil(context["expected_playback_seconds_claimed_not_human_observed"])
                if role=="human_full_watch_listen" else 0
            ),
            synthetic_disclosure_choice=(
                "DISCLOSE_NO" if role=="altered_synthetic_disclosure" else "NOT_DECIDED"
            ),
        )
        kwargs.update(overrides.get(role,{}))
        claim=VersionBoundMockReviewClaim(**kwargs)
        signature=private[rid].sign(sign_domain+canonical(asdict(claim)))
        rec.append(DetachedVersionBoundMockReview(
            claim=claim,signature_ed25519_b64=base64.b64encode(signature).decode(),
        ))
    return tuple(rec)


class VersionPinnedReviewerBoundaryTests(unittest.TestCase):
    def setUp(self):
        temp=TemporaryDirectory(prefix="flowminute-synthetic-review-scope-")
        self.addCleanup(temp.cleanup)
        self.root=Path(temp.name)
        self.story,self.folder,self.report=fixture(self.root)
        self.plan=prepare_exact_private_escrow(
            story=self.story,folder=self.folder,
            producer_report=self.report,config=CONFIG,
        )
        self.s3=FakeS3()
        self.escrow=escrow_once_and_readback(
            s3=self.s3,plan=self.plan,folder=self.folder,
            config=CONFIG,now=NOW,
        )
        self.context=self.read_context()
        self.registry,self.private=register_fake_people()
        self.receipts=fake_signed_reviews(self.context,self.registry,self.private)

    def read_context(self,**kwargs):
        data=dict(
            s3=self.s3,plan=self.plan,escrow_receipt=self.escrow,
            config=CONFIG,runtime_seconds=61.79,now=NOW,
        )
        data.update(kwargs)
        return reconstruct_version_bound_review_context(**data)

    def signed(self,**kwargs):
        values=dict(
            context=self.context,
            expected_context_sha256=self.context["version_bound_review_context_sha256"],
            registry=self.registry,
            expected_external_registry_sha256=mock_registry_digest(self.registry),
            receipts=self.receipts,
            excluded_agent_editor_and_publisher_ids=EXCLUDED,
            now=NOW,
        )
        values.update(kwargs)
        return verify_version_bound_mock_reviews(**values)

    def test_complete_seven_distinct_synthetic_roles_strictly_not_real_approval(self):
        result=self.signed()
        self.assertEqual(result["synthetic_valid_role_count"],7)
        self.assertEqual(set(result["synthetic_role_coverage"]),set(ROLES))
        self.assertTrue(result["all_synthetic_signature_shapes_valid"])
        self.assertEqual(self.context["object_count"],43)
        self.assertTrue(self.context["critical_media_version_pins"]["UNAPPROVED_FULL_EDUCATION_TEST.mp4"]["object_version_id"])
        self.assertEqual(self.context["source_claim_count"],3)
        self.assertEqual(self.context["source_spoken_caption_cue_count"],13)
        self.assertFalse(result["external_actual_human_reviewer_identities_authenticated"])
        self.assertFalse(result["real_owner_key_enrolled_from_private_authority"])
        self.assertFalse(result["actual_human_source_fact_rights_originality_disclosure_and_full_watch_verified"])
        self.assertFalse(result["real_production_immutable_approval_ledger_connected"])
        self.assertFalse(result["release_authorized"])
        self.assertFalse(result["youtube_upload_enabled"])

    def test_one_missing_role_or_signed_disagreement_stays_blocked(self):
        missing=self.signed(receipts=self.receipts[:-1])
        self.assertEqual(missing["synthetic_valid_role_count"],6)
        self.assertTrue(missing["synthetic_unresolved_roles"])
        self.assertFalse(missing["all_synthetic_signature_shapes_valid"])
        for decision in ("MOCK_REJECT","MOCK_UNRESOLVED"):
            changed=fake_signed_reviews(
                self.context,self.registry,self.private,
                overrides={ROLES[2]:{"decision":decision}},
            )
            with self.subTest(decision=decision):
                result=self.signed(receipts=changed)
                self.assertIn(ROLES[2],result["synthetic_unresolved_roles"])
                self.assertFalse(result["release_authorized"])

    def test_source_claim_or_pinned_manifest_context_replay_denied_even_with_new_sha(self):
        for key,bad in (
            ("source_claim_docket_sha256","0"*64),
            ("media_inventory_sha256","1"*64),
            ("pinned_manifest_version_id","fake/other_version"),
            ("pinned_manifest_sha256","2"*64),
            ("all_version_specific_assets_sha256","3"*64),
            ("release_authorized",True),
        ):
            changed=deepcopy(self.context)
            changed[key]=bad
            changed["version_bound_review_context_sha256"]=sha256(canonical({
                k:v for k,v in changed.items()
                if k!="version_bound_review_context_sha256"
            })).hexdigest()
            with self.subTest(key=key),self.assertRaises(VersionedReviewError):
                self.signed(context=changed)

    def test_manifest_or_blob_bytes_modified_after_signing_fail_on_new_remote_readback(self):
        for name in (
            "UNAPPROVED_FULL_EDUCATION_TEST.mp4",
            "scene_captions.srt",
            "original_voice.wav",
            "UNAPPROVED_THUMBNAIL_TEST.png",
            "moving_01_02.png",
        ):
            key=next(r["key"] for r in self.plan["objects"] if r["name"]==name)
            original=self.s3.objects[key]["raw"]
            self.s3.objects[key]["raw"]=original+b"evil"
            with self.subTest(name=name),self.assertRaises(VersionedReviewError):
                self.read_context()
            self.s3.objects[key]["raw"]=original

    def test_current_delete_marker_or_key_replacement_is_not_sufficient_to_replay(self):
        key=self.plan["objects"][0]["key"]
        before=self.s3.objects[key]["version"]
        self.s3.objects[key]["version"]="fake/new_version_with_same_key"
        with self.assertRaises(VersionedReviewError):
            self.read_context()
        self.s3.objects[key]["version"]=before

    def test_missing_or_weaker_object_lock_and_kms_block_further_review(self):
        for attr in ("weaken_lock","forget_kms","break_get"):
            setattr(self.s3,attr,True)
            with self.subTest(attr=attr),self.assertRaises(VersionedReviewError):
                self.read_context()
            setattr(self.s3,attr,False)
        key=self.plan["objects"][0]["key"]
        original=self.s3.objects[key]["retain_until"]
        self.s3.objects[key]["retain_until"]=NOW-timedelta(seconds=2)
        with self.assertRaises(VersionedReviewError):
            self.read_context()
        self.s3.objects[key]["retain_until"]=original

    def test_mismatch_report_wrong_episode_or_source_is_pre_readback_error(self):
        for field,bad in (
            ("episode_id","fm_20261112_short_pm"),
            ("escrow_plan_sha256","a"*64),
            ("exact_source_claim_surface_docket_sha256","b"*64),
            ("total_object_count_including_final_manifest",43),
            ("release_authorized",True),
            ("real_cloud_account_identity_and_bucket_iam_verified",True),
        ):
            changed=dict(self.escrow)
            changed[field]=bad
            with self.subTest(field=field),self.assertRaises(VersionedReviewError):
                self.read_context(escrow_receipt=changed)

    def test_forged_signer_wrong_key_wrong_domain_and_reassignment_denied(self):
        original=self.receipts[0]
        changed=list(self.receipts)
        changed[0]=replace(original,signature_ed25519_b64=
                           base64.b64encode(b"x"*64).decode())
        with self.assertRaises(VersionedReviewError):
            self.signed(receipts=changed)
        bad=fake_signed_reviews(self.context,self.registry,self.private,
                                sign_domain=b"WRONG_ED25519_SIGNING_DOMAIN\x00")
        with self.assertRaises(VersionedReviewError):
            self.signed(receipts=bad)
        registry=dict(self.registry)
        old=registry["fake_reviewer_01"]
        registry["fake_reviewer_01"]=replace(old,key_id="fake_forged_key")
        with self.assertRaises(VersionedReviewError):
            self.signed(registry=registry,
                        expected_external_registry_sha256=mock_registry_digest(registry))

    def test_no_inference_publisher_creator_can_impersonate_a_separate_reviewer(self):
        bad=fake_signed_reviews(
            self.context,self.registry,self.private,
            overrides={ROLES[0]:{"reviewer_id":"publisher_agent"}},
        )
        with self.assertRaises(VersionedReviewError):
            self.signed(receipts=bad)
        registry=dict(self.registry)
        registry["fake_reviewer_02"]=replace(
            registry["fake_reviewer_02"],public_ed25519_b64=
            registry["fake_reviewer_01"].public_ed25519_b64,
        )
        with self.assertRaises(VersionedReviewError):
            self.signed(registry=registry,
                        expected_external_registry_sha256=mock_registry_digest(registry))
        duplicate=list(self.receipts)
        duplicate[-1]=duplicate[0]
        with self.assertRaises(VersionedReviewError):
            self.signed(receipts=duplicate)

    def test_expired_naive_future_and_stale_signature_rejected(self):
        for issued,expiry in (
            (NOW+timedelta(seconds=5),NOW+timedelta(hours=1)),
            (NOW-timedelta(hours=30),NOW+timedelta(hours=1)),
            (NOW-timedelta(minutes=1),NOW-timedelta(seconds=1)),
        ):
            bad=fake_signed_reviews(self.context,self.registry,self.private,
                overrides={ROLES[0]:{
                    "signed_at_utc":issued.isoformat(),
                    "expires_at_utc":expiry.isoformat(),
                }})
            with self.subTest(issued=issued),self.assertRaises(VersionedReviewError):
                self.signed(receipts=bad)
        bad=fake_signed_reviews(self.context,self.registry,self.private,
            overrides={ROLES[0]:{"signed_at_utc":"2026-11-04T16:00:00"}})
        with self.assertRaises(VersionedReviewError):
            self.signed(receipts=bad)

    def test_forged_full_watch_seconds_or_missing_ai_disclosure_rejected(self):
        for role,override in (
            ("human_full_watch_listen",{"claimed_full_watch_seconds":1}),
            ("independent_fact_sufficiency",{"claimed_full_watch_seconds":61}),
            ("altered_synthetic_disclosure",{"synthetic_disclosure_choice":"NOT_DECIDED"}),
            ("channel_owner_release_intent",{"synthetic_disclosure_choice":"DISCLOSE_YES"}),
        ):
            bad=fake_signed_reviews(
                self.context,self.registry,self.private,
                overrides={role:override},
            )
            with self.subTest(role=role),self.assertRaises(VersionedReviewError):
                self.signed(receipts=bad)

    def test_forged_mock_registry_anchor_or_key_revocation_blocks(self):
        with self.assertRaises(VersionedReviewError):
            self.signed(expected_external_registry_sha256="f"*64)
        registry=dict(self.registry)
        registry["fake_reviewer_03"]=replace(registry["fake_reviewer_03"],active=False)
        with self.assertRaises(VersionedReviewError):
            self.signed(registry=registry,
                        expected_external_registry_sha256=mock_registry_digest(registry))

    def test_unsigned_manifest_duplicate_json_keys_or_wrong_canonical_format_denied(self):
        raw=b'{"schema_version":1,"schema_version":2,"other":"'+b"x"*110+b'"}'
        with self.assertRaises(VersionedReviewError):
            _strict_json(raw)
        raw=b'{ "status" : "other", "padding":"'+b"x"*105+b'"}'
        with self.assertRaises(VersionedReviewError):
            _strict_json(raw)

    def test_different_episode_and_manifest_versions_produce_different_exact_roots(self):
        roots={self.context["version_bound_review_context_sha256"]}
        for slot,runtime in (("long",219.12),("short_pm",60.02)):
            separate=self.root/slot
            separate.mkdir()
            story,folder,report=fixture(separate,slot)
            plan=prepare_exact_private_escrow(
                story=story,folder=folder,producer_report=report,config=CONFIG,
            )
            receipt=escrow_once_and_readback(
                s3=self.s3,plan=plan,folder=folder,config=CONFIG,now=NOW,
            )
            context=reconstruct_version_bound_review_context(
                s3=self.s3,plan=plan,escrow_receipt=receipt,
                config=CONFIG,runtime_seconds=runtime,now=NOW,
            )
            roots.add(context["version_bound_review_context_sha256"])
            self.assertEqual(context["object_count"],127 if slot=="long" else 43)
            self.assertFalse(context["actual_full_playback_by_real_human_verified"])
        self.assertEqual(len(roots),3)

    def test_invalid_claims_cannot_be_published_or_find_live_aws_or_youtube_client(self):
        import autopilot.version_pinned_review_boundary as m
        for forbidden in (
            "upload_to_youtube","publish","get_real_aws_creds",
            "make_owner_private_key","enroll_real_owner","invoke_gemini",
            "create_aws_s3_client","activate_cloud_storage",
        ):
            self.assertFalse(hasattr(m,forbidden))
        for k in ("release_authorized","youtube_upload_enabled"):
            self.assertIs(self.context[k],False)


if __name__=="__main__":
    unittest.main()
