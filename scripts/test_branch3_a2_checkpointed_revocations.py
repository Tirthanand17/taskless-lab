"""Offline, adversarial receipt-scoped signed hash-chain verifier tests."""
from __future__ import annotations

import base64
import copy
from datetime import datetime, timedelta, timezone
import json
import unittest

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from scripts.branch3_a2_review_receipt import ReviewDenied
from scripts.branch3_a2_checkpointed_revocations import (
    CHECKPOINT_DOMAIN, CHECKPOINT_FIELDS, ENTRY_FIELDS,
    GENESIS_HEAD_SHA256, LEDGER_ID, MAX_CHECKPOINT_AGE,
    checkpoint_subject, hash_entry, verify_checkpointed_receipt_preview,
    validate_anchor,
)
from scripts.test_branch3_a2_review_receipt import (
    NOW, fixture, revocation_entry,
)


def raw_public(private_key):
    return private_key.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw
    )


def signed_checkpoint(snapshot, key, *,
                      signed_at="2026-11-13T09:55:00Z"):
    c = snapshot["checkpoint"]
    c["sequence"] = len(snapshot["entries"])
    c["head_sha256"] = (
        snapshot["entries"][-1]["entry_sha256"]
        if snapshot["entries"] else GENESIS_HEAD_SHA256
    )
    c["signed_at_utc"] = signed_at
    snapshot["checkpoint_signature_base64"] = base64.b64encode(
        key.sign(checkpoint_subject(c))
    ).decode("ascii")


def prepare(*, revoked=False, checkpoint_time="2026-11-13T09:55:00Z"):
    case, receipt, _, reviewer_pub, revoker_priv, revoker_pub, review_signature = fixture()
    checkpoint_priv = Ed25519PrivateKey.generate()
    snapshot = {
        "schema_version": 1,
        "channel_id": receipt["channel_id"],
        "ledger_id": LEDGER_ID,
        "receipt_id": receipt["receipt_id"],
        "entries": [],
        "checkpoint": {
            "schema_version": 1,
            "channel_id": receipt["channel_id"],
            "ledger_id": LEDGER_ID,
            "receipt_id": receipt["receipt_id"],
            "sequence": 0,
            "head_sha256": GENESIS_HEAD_SHA256,
            "signed_at_utc": checkpoint_time,
            "checkpoint_key_id": "synthetic_checkpoint_key",
        },
        "checkpoint_signature_base64": None,
    }
    if revoked:
        evt = revocation_entry(receipt, revoker_priv, sequence=1)
        entry = {
            "sequence": 1,
            "previous_head_sha256": GENESIS_HEAD_SHA256,
            "event": evt["event"],
            "revocation_signature_base64": evt["signature_base64"],
        }
        entry["entry_sha256"] = hash_entry(**entry)
        snapshot["entries"].append(entry)
    signed_checkpoint(snapshot, checkpoint_priv, signed_at=checkpoint_time)
    params = {
        "case": case,
        "receipt": receipt,
        "review_signature_b64": review_signature,
        "reviewer_public_key": reviewer_pub,
        "revocation_public_key": revoker_pub,
        "checkpoint_public_key": raw_public(checkpoint_priv),
        "snapshot": snapshot,
        "trusted_floor": {
            "sequence": 0,
            "head_sha256": GENESIS_HEAD_SHA256,
        },
        "now": NOW,
    }
    return params, revoker_priv, checkpoint_priv


class CheckpointedA2Tests(unittest.TestCase):
    def test_valid_empty_signed_snapshot_still_never_licenses(self):
        p, _, _ = prepare()
        result = verify_checkpointed_receipt_preview(**p)
        for flag in (
            "real_independently_enrolled_keys",
            "real_external_durable_floor_verified",
            "remote_ledger_freshness_and_completeness_verified",
            "authentic_creator_license_verified",
            "source_media_download_authorized",
            "creator_registry_update_authorized",
            "youtube_upload_authorized",
            "youtube_schedule_authorized",
            "youtube_publish_authorized",
        ):
            self.assertFalse(result[flag], flag)
        self.assertTrue(result["synthetic_checkpoint_signature_mathematically_valid"])
        self.assertTrue(result["supplied_hash_chain_mathematically_valid"])
        self.assertEqual(result["actual_external_api_calls"], 0)
        self.assertNotIn(p["receipt"]["receipt_id"], json.dumps(result))

    def test_a_signed_revocation_is_permanent_even_with_recent_checkpoint(self):
        p, _, _ = prepare(revoked=True)
        with self.assertRaisesRegex(ReviewDenied, "TARGET_RECEIPT_REVOKED"):
            verify_checkpointed_receipt_preview(**p)

    def test_dropped_tombstone_with_old_signed_checkpoint_denied_by_anchor(self):
        current, _, checkpoint_key = prepare(revoked=True)
        # Start with the same signed review and receipt, not another fixture.
        stale = copy.deepcopy(current)
        stale["trusted_floor"] = {
            "sequence": 1,
            "head_sha256": current["snapshot"]["entries"][0]["entry_sha256"],
        }
        stale["snapshot"]["entries"] = []
        # Even if someone can produce a signed older checkpoint, a separately
        # persisted newer anchor prevents the fork from being accepted.
        signed_checkpoint(stale["snapshot"], checkpoint_key)
        with self.assertRaisesRegex(ReviewDenied, "ROLLBACK_OR_FORK"):
            verify_checkpointed_receipt_preview(**stale)

    def test_mutations_of_signed_checkpoint_fail(self):
        cases = (
            ("channel_id", "UCCcL9Q_jqVq6LJmnYUSAFZA"),
            ("ledger_id", "flowminute_wrong"),
            ("receipt_id", "clivox_review_other_000000000"),
            ("sequence", 1),
            ("head_sha256", "a"*64),
            ("signed_at_utc", "2026-11-13T09:56:00Z"),
            ("checkpoint_key_id", "fake_other_key"),
            ("schema_version", 2),
        )
        for field, bad in cases:
            p, _, _ = prepare()
            p["snapshot"]["checkpoint"][field] = bad
            with self.subTest(field=field), self.assertRaises(ReviewDenied):
                verify_checkpointed_receipt_preview(**p)

    def test_checkpoint_wrong_key_or_signature_denied(self):
        p, _, _ = prepare()
        p["checkpoint_public_key"] = raw_public(Ed25519PrivateKey.generate())
        with self.assertRaisesRegex(ReviewDenied, "BAD_CHECKPOINT_SIGNATURE"):
            verify_checkpointed_receipt_preview(**p)
        p, _, _ = prepare()
        p["snapshot"]["checkpoint_signature_base64"] = base64.b64encode(b"x"*64).decode("ascii")
        with self.assertRaisesRegex(ReviewDenied, "BAD_CHECKPOINT_SIGNATURE"):
            verify_checkpointed_receipt_preview(**p)

    def test_stale_future_or_naive_clock_rejected(self):
        for bad_time in ("2026-11-13T09:44:00Z", "2026-11-13T10:01:00Z",
                         "2026-11-13T09:55:00+00:00"):
            p, _, key = prepare()
            if bad_time.endswith("Z"):
                signed_checkpoint(p["snapshot"], key, signed_at=bad_time)
            else:
                # Malformed timestamp cannot itself be signed by helper.
                p["snapshot"]["checkpoint"]["signed_at_utc"] = bad_time
            with self.subTest(signed_at=bad_time), self.assertRaises(ReviewDenied):
                verify_checkpointed_receipt_preview(**p)
        p, _, _ = prepare()
        p["now"] = datetime(2026,11,13,10)
        with self.assertRaises(ReviewDenied):
            verify_checkpointed_receipt_preview(**p)
        self.assertEqual(MAX_CHECKPOINT_AGE, timedelta(minutes=15))

    def test_previous_hash_and_changed_entry_sha_rejected(self):
        for field,value in (
            ("previous_head_sha256", "b"*64),
            ("entry_sha256", "c"*64),
            ("sequence", 2),
            ("revocation_signature_base64", "unsigned"),
        ):
            p, _, _ = prepare(revoked=True)
            p["snapshot"]["entries"][0][field] = value
            with self.subTest(field=field), self.assertRaises(ReviewDenied):
                verify_checkpointed_receipt_preview(**p)

    def test_changed_revocation_target_or_signature_cannot_launder(self):
        for field,value in (
            ("receipt_id", "clivox_review_different_receipt_00000"),
            ("case_sha256", "d"*64),
            ("reason_code", "NOT_A_REVOKE"),
            ("revocation_sequence", 2),
            ("revoked_at_utc", "2026-11-14T00:00:00Z"),
        ):
            p, _, _ = prepare(revoked=True)
            p["snapshot"]["entries"][0]["event"][field] = value
            with self.subTest(field=field), self.assertRaises(ReviewDenied):
                verify_checkpointed_receipt_preview(**p)
        p, _, _ = prepare(revoked=True)
        p["revocation_public_key"] = raw_public(Ed25519PrivateKey.generate())
        with self.assertRaisesRegex(ReviewDenied, "BAD_REVOCATION_SIGNATURE"):
            verify_checkpointed_receipt_preview(**p)

    def test_snapshot_fields_strict_no_secret_leak(self):
        p, _, _ = prepare()
        p["snapshot"]["raw_contract"] = "DONT_STORE_SECRET"
        with self.assertRaises(ReviewDenied):
            verify_checkpointed_receipt_preview(**p)
        p, _, _ = prepare(revoked=True)
        p["snapshot"]["entries"][0]["token"] = "DONT_STORE_TOKEN"
        with self.assertRaises(ReviewDenied):
            verify_checkpointed_receipt_preview(**p)
        self.assertEqual(len(CHECKPOINT_FIELDS), 8)
        self.assertEqual(len(ENTRY_FIELDS), 5)

    def test_external_floor_digest_wrong_or_wrong_sequence_denied(self):
        for anchor in (
            None, {}, {"sequence": -1, "head_sha256": GENESIS_HEAD_SHA256},
            {"sequence": 0, "head_sha256": "f"*64},
            {"sequence": 1, "head_sha256": GENESIS_HEAD_SHA256},
            {"sequence": 2, "head_sha256": "a"*64},
            {"sequence": True, "head_sha256": GENESIS_HEAD_SHA256},
            {"sequence": 0, "head_sha256": GENESIS_HEAD_SHA256, "token": "bad"},
        ):
            p, _, _ = prepare()
            p["trusted_floor"] = anchor
            with self.subTest(anchor=anchor), self.assertRaises(ReviewDenied):
                verify_checkpointed_receipt_preview(**p)

    def test_receipt_wrong_identity_and_bad_review_signature_denied(self):
        p, _, _ = prepare()
        p["receipt"]["source_video_id"] = "ABCDEFGHIJK"
        with self.assertRaises(ReviewDenied):
            verify_checkpointed_receipt_preview(**p)
        p, _, _ = prepare()
        p["review_signature_b64"] = base64.b64encode(b"wrong"*12+b"xxxx").decode()
        with self.assertRaises(ReviewDenied):
            verify_checkpointed_receipt_preview(**p)

    def test_no_local_persistence_and_no_production_entrypoint(self):
        p, _, _ = prepare()
        result = verify_checkpointed_receipt_preview(**p)
        self.assertFalse(result["real_external_durable_floor_verified"])
        self.assertFalse(result["remote_ledger_freshness_and_completeness_verified"])
        self.assertEqual(result["supplied_revocation_event_count"],0)


if __name__ == "__main__":
    unittest.main()
