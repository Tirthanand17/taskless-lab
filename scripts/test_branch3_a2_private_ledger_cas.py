"""Adversarial source-free A2 global revocation ledger SHA-CAS tests."""
from __future__ import annotations

import base64
import copy
from datetime import datetime, timezone
import json
import unittest

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from scripts.branch3_a2_review_receipt import ReviewDenied, REVOKE_DOMAIN, canonical
from scripts.branch3_a2_checkpointed_revocations import GENESIS_HEAD_SHA256
from scripts.branch3_a2_private_ledger_cas import (
    CLIVOX_ID, ENTRY_DOMAIN, FILE_PATH, MAX_BYTES, MAX_ENTRIES,
    PUBLIC_REPO, build_cas_put_body, canonical_ledger,
    decode_github_contents, entry_sha, fixture_report, git_blob_sha,
    initial_ledger, prepare_append, simulate_github_cas,
    validate_private_target, verify_journal,
)

NOW = datetime(2026, 11, 13, 5, 0, tzinfo=timezone.utc)
R1 = "clivox_review_synthetic_receipt_000001"
R2 = "clivox_review_synthetic_receipt_000002"


def pub(k: Ed25519PrivateKey) -> bytes:
    return k.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw
    )


def event_for(key: Ed25519PrivateKey, sequence=1, receipt=R1,
              reason="CREATOR_WITHDREW_PERMISSION",
              at="2026-11-13T04:00:00Z") -> dict:
    event = {
        "schema_version": 1,
        "channel_id": CLIVOX_ID,
        "case_sha256": "a" * 64,
        "receipt_id": receipt,
        "revocation_sequence": sequence,
        "revoked_at_utc": at,
        "reason_code": reason,
    }
    sig = base64.b64encode(key.sign(REVOKE_DOMAIN + canonical(event))).decode()
    return {"event": event, "signature_base64": sig}


def floor(sequence=0, head=GENESIS_HEAD_SHA256) -> dict:
    return {"sequence": sequence, "head_sha256": head}


def readback(ledger=None, *, raw=None):
    if raw is None:
        raw = canonical_ledger(initial_ledger() if ledger is None else ledger)
    return {
        "type": "file", "encoding": "base64",
        "path": FILE_PATH, "name": "revocation-journal-v1.json",
        "size": len(raw), "sha": git_blob_sha(raw),
        "content": base64.b64encode(raw).decode("ascii"),
    }


DEFAULT_ANCHOR = object()


def opts(key, anchor=DEFAULT_ANCHOR):
    return {
        "revocation_public_key": pub(key),
        "trusted_floor": floor() if anchor is DEFAULT_ANCHOR else anchor,
        "now": NOW,
    }


class PrivateCASJournalTests(unittest.TestCase):

    def test_genesis_passes_but_never_authorizes_media_or_rights(self):
        key = Ed25519PrivateKey.generate()
        summary = verify_journal(initial_ledger(), **opts(key))
        self.assertEqual(summary["supplied_events_signature_math_checked"], 0)
        self.assertTrue(summary["supplied_head_chain_valid"])
        for flag in (
            "real_issuer_enrollment_verified",
            "real_external_anchor_durability_verified",
            "complete_remote_journal_verified",
            "source_download_authorized",
            "private_media_access_authorized",
            "youtube_upload_authorized",
            "youtube_publish_authorized",
        ):
            self.assertFalse(summary[flag])
        self.assertEqual(summary["authentic_creator_licenses_verified"], 0)
        self.assertEqual(summary["actual_github_write_calls"], 0)

    def test_two_signed_tombstones_are_linked_and_pure_cas_works(self):
        key = Ed25519PrivateKey.generate()
        initial = initial_ledger()
        first = prepare_append(
            initial, signed_event=event_for(key), **opts(key)
        )
        self.assertEqual(first["sequence"], 1)
        self.assertEqual(initial["sequence"], 0)
        self.assertEqual(first["entries"][0]["previous_head_sha256"],
                         GENESIS_HEAD_SHA256)
        second = prepare_append(
            first, signed_event=event_for(key, sequence=2, receipt=R2),
            **opts(key, anchor=floor(1, first["head_sha256"]))
        )
        self.assertEqual(second["sequence"], 2)
        self.assertEqual(second["entries"][1]["previous_head_sha256"],
                         first["head_sha256"])
        self.assertEqual(
            verify_journal(second, **opts(
                key, anchor=floor(1, first["head_sha256"])
            ))["supplied_events_signature_math_checked"], 2
        )
        reply = readback(initial)
        parsed, old_blob_sha = decode_github_contents(reply)
        self.assertEqual(parsed, initial)
        proposed = build_cas_put_body(
            original_sha=old_blob_sha, new_ledger=first
        )
        self.assertEqual(proposed["sha"], old_blob_sha)
        self.assertEqual(proposed["branch"], "main")
        self.assertEqual(
            simulate_github_cas(
                server_blob_sha=old_blob_sha, proposed_put=proposed
            ),
            git_blob_sha(canonical_ledger(first)),
        )
        self.assertNotEqual(first["head_sha256"], initial["head_sha256"])

    def test_stale_sha_conflict_blocks_parallel_append(self):
        key = Ed25519PrivateKey.generate()
        raw = canonical_ledger(initial_ledger())
        before_sha = git_blob_sha(raw)
        first = prepare_append(initial_ledger(),
                               signed_event=event_for(key), **opts(key))
        body = build_cas_put_body(
            original_sha=before_sha, new_ledger=first
        )
        after_sha = git_blob_sha(canonical_ledger(first))
        self.assertNotEqual(before_sha, after_sha)
        with self.assertRaisesRegex(ReviewDenied, "GITHUB_CAS_STALE"):
            simulate_github_cas(
                server_blob_sha=after_sha, proposed_put=body
            )

    def test_removed_revocation_is_rejected_with_external_pinned_floor(self):
        key = Ed25519PrivateKey.generate()
        fresh = prepare_append(initial_ledger(),
                               signed_event=event_for(key), **opts(key))
        pinned = floor(1, fresh["head_sha256"])
        with self.assertRaisesRegex(ReviewDenied, "STALE_OR_FORKED"):
            verify_journal(initial_ledger(), **opts(key, anchor=pinned))

    def test_mutations_are_detected_against_signature_and_chain(self):
        key = Ed25519PrivateKey.generate()
        original = prepare_append(initial_ledger(),
                                  signed_event=event_for(key), **opts(key))
        changes = (
            (["head_sha256"], "b"*64),
            (["sequence"], 0),
            (["channel_id"], "UCCcL9Q_jqVq6LJmnYUSAFZA"),
            (["entries", 0, "previous_head_sha256"], "b"*64),
            (["entries", 0, "entry_sha256"], "b"*64),
            (["entries", 0, "event", "receipt_id"], R2),
            (["entries", 0, "event", "case_sha256"], "c"*64),
            (["entries", 0, "event", "revocation_sequence"], 2),
            (["entries", 0, "event", "reason_code"], "FAKE_CLEARANCE"),
            (["entries", 0, "revocation_signature_base64"], "bad"),
        )
        for path, value in changes:
            changed = copy.deepcopy(original)
            obj = changed
            for name in path[:-1]:
                obj = obj[name]
            obj[path[-1]] = value
            with self.subTest(path=path), self.assertRaises(ReviewDenied):
                verify_journal(changed, **opts(key))

    def test_duplicate_tombstone_cannot_be_appended(self):
        key = Ed25519PrivateKey.generate()
        one = prepare_append(initial_ledger(),
                             signed_event=event_for(key), **opts(key))
        with self.assertRaisesRegex(ReviewDenied, "ALREADY_REVOKED"):
            prepare_append(
                one, signed_event=event_for(key, sequence=2),
                **opts(key)
            )

    def test_wrong_key_unsafe_clock_future_tombstone_denied(self):
        key = Ed25519PrivateKey.generate()
        wrong = Ed25519PrivateKey.generate()
        with self.assertRaisesRegex(ReviewDenied, "TOMBSTONE_SIGNATURE"):
            prepare_append(initial_ledger(),
                signed_event=event_for(wrong), **opts(key))
        with self.assertRaisesRegex(ReviewDenied, "FUTURE_TOMBSTONE"):
            prepare_append(initial_ledger(),
                signed_event=event_for(key, at="2026-11-14T00:00:00Z"),
                **opts(key))
        bad = opts(key)
        bad["now"] = datetime(2026,11,13,5)
        with self.assertRaises(ReviewDenied):
            verify_journal(initial_ledger(), **bad)

    def test_wrong_repo_or_public_visibility_rejected(self):
        good = {
            "id": 123456789, "name": "clivox-owner-vault",
            "full_name": "Tirthanand17/clivox-owner-vault",
            "private": True, "visibility": "private",
            "owner": {"login": "Tirthanand17"},
            "archived": False, "disabled": False
        }
        validate_private_target(good, "clivox-owner-vault")
        for change in (
            {"private": False}, {"visibility": "public"},
            {"full_name": PUBLIC_REPO},
            {"owner": {"login": "SomeoneElse"}},
            {"disabled": True}
        ):
            bad = {**good, **change}
            with self.subTest(change=change), self.assertRaises(ReviewDenied):
                validate_private_target(bad, "clivox-owner-vault")
        with self.assertRaises(ReviewDenied):
            validate_private_target(good, "../taskless-lab")

    def test_github_contents_sha_size_and_path_all_strict(self):
        original = readback()
        for bad_field, bad_val in (
            ("type", "symlink"), ("encoding", "utf-8"),
            ("path", "README.md"),
            ("name", "private-contract.pdf"), ("size", 900),
            ("sha", "1"*40), ("content", "not base64!!"),
        ):
            case = dict(original)
            case[bad_field] = bad_val
            with self.subTest(field=bad_field), self.assertRaises(ReviewDenied):
                decode_github_contents(case)
        self.assertEqual(decode_github_contents(original)[0], initial_ledger())

    def test_forged_extra_secret_fields_or_changed_anchor_fail(self):
        key = Ed25519PrivateKey.generate()
        ledger = initial_ledger()
        ledger["raw_contract"] = "never put in public source"
        with self.assertRaises(ReviewDenied):
            verify_journal(ledger, **opts(key))
        for anchor in (
            None, {}, {"sequence": -1, "head_sha256": GENESIS_HEAD_SHA256},
            {"sequence": 0, "head_sha256": "c"*64},
            {"sequence": 1, "head_sha256": "c"*64},
        ):
            with self.subTest(anchor=anchor), self.assertRaises(ReviewDenied):
                verify_journal(initial_ledger(), **opts(key, anchor=anchor))

    def test_fixture_is_never_a_live_vault_or_licensed(self):
        report = fixture_report()
        self.assertEqual(report["github_api_calls"], 0)
        self.assertEqual(report["youtube_api_calls"], 0)
        self.assertFalse(report["live_github_contents_put_configured"])
        self.assertFalse(report["real_private_ledger_file_present"])
        self.assertFalse(report["real_external_checkpoint_pin_enrolled"])
        self.assertFalse(report["youtube_publish_authorized"])
        self.assertEqual(report["real_license_grants_verified"], 0)


if __name__ == "__main__":
    unittest.main()
