"""A2 adversarial signed-review and revocation tests, no real key or license."""
from __future__ import annotations

import base64
import copy
from datetime import datetime, timezone
import json
import unittest

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from scripts.branch3_discovery import build_report, mock_fixture
from scripts.branch3_rights_case_intake import build_rights_cases, PENDING_CHECKS
from scripts.branch3_a2_review_receipt import (
    OUTCOME, POLICY, REGISTRY, ReviewDenied, REVIEW_DOMAIN, REVOKE_DOMAIN,
    audit_pending_handoff, digest, read_json, review_subject, revocation_subject,
    verify_ed25519, verify_offline_receipt_preview, verify_pending_case
)

NOW = datetime(2026, 11, 13, 10, 0, tzinfo=timezone.utc)
CREATED = "2026-11-12T12:02:00Z"


def inputs():
    discovery = build_report(mock_fixture(), mode="fixture", category="gaming",
                             query="", now=datetime(2026,11,12,12,tzinfo=timezone.utc),
                             fixture=True)
    cases = build_rights_cases(discovery, generated_at_utc=CREATED)
    return discovery, cases


def fixture():
    _, cases = inputs()
    case = cases["cases"][0]
    receipt = {
        "schema_version": 1,
        "channel_id": case["channel_id"],
        "case_id": case["case_id"],
        "case_sha256": digest(case),
        "source_channel_id": case["source_channel_id"],
        "source_video_id": case["source_video_id"],
        "receipt_id": "clivox_review_test_receipt_00000001",
        "reviewer_key_id": "synthetic_review_test_key",
        "creator_grant_evidence_sha256": "a"*64,
        "review_outcome": OUTCOME,
        "reviewed_at_utc": "2026-11-12T12:03:00Z",
        "expires_at_utc": "2026-12-12T12:03:00Z",
        "source_is_synthetic": True,
        "required_human_checks": {
            k: "REVIEWER_CLAIMS_COMPLETED_NOT_AUTHENTICATED"
            for k in PENDING_CHECKS
        }
    }
    reviewer_private = Ed25519PrivateKey.generate()
    revoker_private = Ed25519PrivateKey.generate()
    reviewer_pub = reviewer_private.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    revoker_pub = revoker_private.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    signature = base64.b64encode(
        reviewer_private.sign(review_subject(case, receipt))
    ).decode("ascii")
    return case, receipt, reviewer_private, reviewer_pub, revoker_private, revoker_pub, signature


def params():
    case,receipt,rprivate,rpub,vprivate,vpub,sig = fixture()
    return {
        "case":case, "receipt":receipt, "signature_b64":sig,
        "reviewer_public_key":rpub, "revocations":[],
        "revocation_public_key":vpub, "now":NOW,
        "last_trusted_revocation_sequence":0
    }


def revocation_entry(receipt, private_key, sequence=1, reason="OWNER_HOLD",
                     timestamp="2026-11-13T08:00:00Z"):
    event = {
        "schema_version": 1,
        "channel_id": receipt["channel_id"],
        "case_sha256": receipt["case_sha256"],
        "receipt_id": receipt["receipt_id"],
        "revocation_sequence": sequence,
        "revoked_at_utc": timestamp,
        "reason_code": reason
    }
    signature = base64.b64encode(
        private_key.sign(revocation_subject(receipt,event))
    ).decode("ascii")
    return {"event":event, "signature_base64":signature}


class SignedRightsReviewTests(unittest.TestCase):

    def test_closed_real_policy_and_empty_registry(self):
        d,cases = inputs()
        result = audit_pending_handoff(d,cases,read_json(POLICY),read_json(REGISTRY))
        self.assertEqual(result["pending_review_cases"],2)
        self.assertTrue(result["synthetic_fixture"])
        self.assertEqual(result["authentic_creator_grants"],0)
        self.assertEqual(result["actual_signed_human_review_receipts"],0)
        self.assertFalse(result["durable_revocation_ledger_present"])
        self.assertFalse(result["source_media_acquisition_authorized"])
        self.assertFalse(result["youtube_upload_authorized"])
        self.assertEqual(result["youtube_api_writes"],0)

    def test_preview_math_never_promotes_rights_or_media(self):
        result = verify_offline_receipt_preview(**params())
        self.assertTrue(result["review_signature_math_passed"])
        self.assertTrue(result["signed_receipt_case_sha256_matched"])
        for key in (
            "reviewer_identity_independently_enrolled",
            "complete_remote_revocation_ledger_verified",
            "durable_anti_rollback_checkpoint_verified",
            "creator_license_authenticity_verified",
            "media_acquisition_authorized",
            "youtube_upload_authorized",
            "youtube_schedule_authorized",
            "youtube_publish_authorized"
        ):
            self.assertFalse(result[key],key)
        self.assertEqual(result["revocation_events_supplied"],0)
        self.assertEqual(result["channel_id"],"UCfPEvy0SefE_5nNlYlY_CyQ")

    def test_signature_cannot_be_reused_with_a6_domain(self):
        case,receipt,_,reviewer_pub,_,_,sig = fixture()
        payload = review_subject(case,receipt)
        self.assertTrue(verify_ed25519(payload,sig,reviewer_pub,REVIEW_DOMAIN))
        with self.assertRaises(ReviewDenied):
            verify_ed25519(payload,sig,reviewer_pub,REVOKE_DOMAIN)

    def test_wrong_signer_or_signature_fails(self):
        for mutate in ("wrong_key", "corrupt_signature", "missing_signature", "wrong_key_length"):
            p = params()
            if mutate=="wrong_key":
                k = Ed25519PrivateKey.generate()
                p["reviewer_public_key"]=k.public_key().public_bytes(
                    serialization.Encoding.Raw,serialization.PublicFormat.Raw)
            elif mutate=="corrupt_signature":
                p["signature_b64"]=base64.b64encode(b"x"*64).decode()
            elif mutate=="missing_signature":
                p["signature_b64"]=""
            else:
                p["reviewer_public_key"]=b"x"*31
            with self.subTest(mutate=mutate),self.assertRaises(ReviewDenied):
                verify_offline_receipt_preview(**p)

    def test_all_receipt_tampering_fails(self):
        changes=(
            ("channel_id","UCCcL9Q_jqVq6LJmnYUSAFZA"),
            ("case_id","clivox_rights_abcdefghijk"),
            ("case_sha256","b"*64),
            ("source_channel_id","UC"+"z"*22),
            ("source_video_id","notvalid!!!"),
            ("receipt_id","clivox_review_anotherreceipt_00000002"),
            ("reviewer_key_id","unknown_review_key"),
            ("creator_grant_evidence_sha256","b"*64),
            ("review_outcome","LEGAL_LICENSE_GRANTED"),
            ("reviewed_at_utc","2026-11-12T12:04:00Z"),
            ("expires_at_utc","2027-04-12T12:03:00Z"),
            ("source_is_synthetic",False),
            ("schema_version",2)
        )
        for field,value in changes:
            p = params()
            p["receipt"][field] = value
            with self.subTest(field=field),self.assertRaises(ReviewDenied):
                verify_offline_receipt_preview(**p)

    def test_claims_and_new_secret_fields_cannot_be_injected(self):
        for change in ("extra","checks_missing","checks_changed"):
            p=params()
            if change=="extra":
                p["receipt"]["private_contract"]="SECRET"
            elif change=="checks_missing":
                p["receipt"]["required_human_checks"].pop(next(iter(PENDING_CHECKS)))
            else:
                p["receipt"]["required_human_checks"][PENDING_CHECKS[0]]="APPROVED"
            with self.subTest(change=change),self.assertRaises(ReviewDenied):
                verify_offline_receipt_preview(**p)

    def test_case_is_bound_to_exact_source_and_pending_status(self):
        changes = (
            ("source_video_id","AAAAAAAAAAA"),
            ("source_channel_id","UC"+"z"*22),
            ("case_state","RIGHTS_VERIFIED"),
            ("media_acquisition_authorized",True),
            ("permission_evidence_sha256","a"*64),
            ("actual_grant_document_available",True),
            ("case_is_synthetic",False),
        )
        for field,value in changes:
            p=params()
            p["case"][field]=value
            with self.subTest(field=field),self.assertRaises(ReviewDenied):
                verify_offline_receipt_preview(**p)

    def test_expired_future_and_naive_clock_denied(self):
        p=params()
        p["now"]=datetime(2027,1,1,tzinfo=timezone.utc)
        with self.assertRaises(ReviewDenied):
            verify_offline_receipt_preview(**p)
        p=params()
        p["now"]=datetime(2026,11,1,tzinfo=timezone.utc)
        with self.assertRaises(ReviewDenied):
            verify_offline_receipt_preview(**p)
        p=params()
        p["now"]=datetime(2026,11,13)
        with self.assertRaises(ReviewDenied):
            verify_offline_receipt_preview(**p)

    def test_revocation_tombstone_blocks_even_previously_valid_receipt(self):
        p=params()
        _,_,_,_,revoker_private,_,_=fixture()
        # Bind this distinct revoker key to the current params.
        p["revocation_public_key"]=revoker_private.public_key().public_bytes(
            serialization.Encoding.Raw,serialization.PublicFormat.Raw)
        p["revocations"]=[revocation_entry(p["receipt"],revoker_private)]
        with self.assertRaisesRegex(ReviewDenied,"RECEIPT_REVOKED"):
            verify_offline_receipt_preview(**p)

    def test_invalid_revocation_signature_does_not_silently_clear_it(self):
        p=params()
        revoker_private=Ed25519PrivateKey.generate()
        p["revocations"]=[revocation_entry(p["receipt"],revoker_private)]
        with self.assertRaisesRegex(ReviewDenied,"REVOCATION_SIGNATURE"):
            verify_offline_receipt_preview(**p)

    def test_revocation_wrong_receipt_or_case_or_reason_denied(self):
        for field,value in (
            ("receipt_id","clivox_review_other_00000"),
            ("case_sha256","c"*64),
            ("reason_code","none"),
            ("revoked_at_utc","2026-11-14T00:00:00Z")
        ):
            p=params()
            k=Ed25519PrivateKey.generate()
            p["revocation_public_key"]=k.public_key().public_bytes(
                serialization.Encoding.Raw,serialization.PublicFormat.Raw)
            event=revocation_entry(p["receipt"],k)
            event["event"][field]=value
            p["revocations"]=[event]
            with self.subTest(field=field),self.assertRaises(ReviewDenied):
                verify_offline_receipt_preview(**p)

    def test_revocation_replay_and_rollback_denied(self):
        p=params()
        k=Ed25519PrivateKey.generate()
        p["revocation_public_key"]=k.public_key().public_bytes(
            serialization.Encoding.Raw,serialization.PublicFormat.Raw)
        item=revocation_entry(p["receipt"],k)
        p["revocations"]=[item,copy.deepcopy(item)]
        with self.assertRaises(ReviewDenied):
            verify_offline_receipt_preview(**p)
        p=params()
        p["last_trusted_revocation_sequence"]=3
        with self.assertRaisesRegex(ReviewDenied,"REVOCATION_ROLLBACK"):
            verify_offline_receipt_preview(**p)
        p=params()
        p["last_trusted_revocation_sequence"]=-1
        with self.assertRaises(ReviewDenied):
            verify_offline_receipt_preview(**p)

    def test_policy_guards_cannot_be_forged(self):
        d,cases=inputs()
        for field,val in (
            ("real_human_reviewer_key_enrolled",True),
            ("real_revocation_authority_key_enrolled",True),
            ("durable_revocation_ledger",True),
            ("latest_trusted_revocation_sequence",100),
            ("real_authentic_creator_grants",1),
            ("real_human_reviews_completed",1),
            ("source_media_download_enabled",True),
            ("youtube_write_enabled",True),
            ("creator_registry_auto_promotion_enabled",True),
        ):
            pol=read_json(POLICY)
            pol[field]=val
            with self.subTest(field=field),self.assertRaises(ReviewDenied):
                audit_pending_handoff(d,cases,pol,read_json(REGISTRY))

    def test_a1_a2_case_or_registry_forgery_denied(self):
        d,cases=inputs()
        cases["cases"][0]["case_state"]="RIGHTS_VERIFIED"
        with self.assertRaises(ReviewDenied):
            audit_pending_handoff(d,cases,read_json(POLICY),read_json(REGISTRY))
        d,cases=inputs()
        d["candidates"][0]["source_title"]="FORGED AFTER RIGHTS INTAKE"
        with self.assertRaises(ReviewDenied):
            audit_pending_handoff(d,cases,read_json(POLICY),read_json(REGISTRY))
        d,cases=inputs()
        registry=read_json(REGISTRY)
        registry["creators"]=[{"fake":"grant"}]
        with self.assertRaises(ReviewDenied):
            audit_pending_handoff(d,cases,read_json(POLICY),registry)

    def test_no_real_identifiers_or_grants_are_emitted_by_audit(self):
        d,cases=inputs()
        output=json.dumps(audit_pending_handoff(d,cases,read_json(POLICY),read_json(REGISTRY)))
        for forbidden in ("private_contract","refresh_token","creator_contact",
                          "clivox_rights_", "AUTHENTIC_RIGHTS_GRANTED"):
            self.assertNotIn(forbidden,output)


if __name__=="__main__":
    unittest.main()
