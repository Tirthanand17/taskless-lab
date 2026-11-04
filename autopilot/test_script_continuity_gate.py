"""B3d1 GitHub-only negative tests. All signing keys are ephemeral test fixtures.

An authenticated-looking test signature NEVER attests a human fact check,
licensed media, editorial novelty, private ledger, or publication permission.
"""
from __future__ import annotations

import base64
from copy import deepcopy
from dataclasses import asdict, replace
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
import unittest

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

from autopilot.test_claim_review_dossier import fixture
from autopilot.script_draft_agent import build_draft_input, validate_proposal
from autopilot.script_continuity_gate import (
    PURPOSE, STATUS, DetachedScriptSeal, ScriptContinuityError,
    ScriptSealClaim, TrustedScriptCustodian, freeze_script_manifest,
    verify_script_seal,
)

NOW = datetime(2026, 11, 4, 6, 0, tzinfo=timezone.utc)
EXCLUDED = frozenset(("creator_agent", "publisher_service"))


def serialized(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def signed_fixture(index=0):
    proposal, slot, sources = fixture(index)
    manifest = freeze_script_manifest(proposal, slot, sources)
    anchor = sha256(serialized(manifest)).hexdigest()
    signer = Ed25519PrivateKey.generate()
    pub = signer.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    custodian_id = "trusted_custodian"
    root = {custodian_id: TrustedScriptCustodian(
        custodian_id, "custodian_key_01", base64.b64encode(pub).decode()
    )}
    claim = ScriptSealClaim(
        purpose=PURPOSE,
        manifest_sha256=anchor,
        episode_id=manifest["episode_id"],
        channel_id=manifest["channel_id"],
        release_slot=manifest["release_slot"],
        release_utc=manifest["release_utc"],
        custodian_id=custodian_id,
        key_id="custodian_key_01",
        issued_at_utc=(NOW-timedelta(minutes=15)).isoformat(),
        expires_at_utc=(NOW+timedelta(hours=3)).isoformat(),
    )
    seal = DetachedScriptSeal(
        claim=claim,
        signature_ed25519_b64=base64.b64encode(signer.sign(serialized(asdict(claim)))).decode()
    )
    return proposal, slot, sources, anchor, root, seal, signer


def validate(item, *, excluded=EXCLUDED, now=NOW):
    proposal, slot, sources, anchor, root, seal, _ = item
    return verify_script_seal(
        proposal, slot, sources, seal=seal, anchor_manifest_sha256=anchor,
        registry=root, excluded_creator_and_publisher_ids=excluded, now=now,
    )


class ScriptContinuityGateTests(unittest.TestCase):
    def setUp(self):
        self.item = signed_fixture(0)

    def test_valid_external_signature_only_authenticates_continuity(self):
        result = validate(self.item)
        self.assertEqual(result["status"], STATUS)
        self.assertTrue(result["immutable_content_binding_checked"])
        self.assertFalse(result["authenticity_of_external_trust_root_verified_by_software"])
        self.assertFalse(result["external_append_only_ledger_deployed"])
        self.assertFalse(result["claim_level_independent_fact_review_complete"])
        self.assertFalse(result["rights_and_originality_review_complete"])
        self.assertFalse(result["human_editorial_review_complete"])
        self.assertFalse(result["media_render_enabled"])
        self.assertFalse(result["youtube_upload_enabled"])
        self.assertFalse(result["youtube_schedule_enabled"])
        self.assertFalse(result["release_authorized"])

    def test_each_of_three_episodes_has_different_nonpublish_manifest(self):
        items = [signed_fixture(i) for i in range(3)]
        digests = {item[3] for item in items}
        self.assertEqual(len(digests), 3)
        for item in items:
            self.assertEqual(validate(item)["status"], STATUS)

    def test_plain_hash_without_detached_signature_cannot_pass(self):
        item = list(self.item)
        item[5] = None
        with self.assertRaises(ScriptContinuityError):
            validate(item)

    def test_caller_supplied_correct_digest_is_not_enough(self):
        item = list(self.item)
        seal = item[5]
        item[5] = replace(seal, signature_ed25519_b64="A"*88)
        with self.assertRaises(ScriptContinuityError):
            validate(item)

    def test_altered_narration_validly_rebuilt_draft_still_breaks_external_anchor(self):
        item = list(self.item)
        proposal, slot, sources = item[:3]
        raw = {k: deepcopy(proposal[k]) for k in (
            "title", "hook", "viewer_benefit", "example_walkthrough", "narration",
            "visual_beats", "claim_candidates"
        )}
        raw["narration"] += " Protect the original example data throughout this short tutorial."
        item[0] = validate_proposal(raw, build_draft_input(slot, sources))
        with self.assertRaises(ScriptContinuityError):
            validate(item)

    def test_modified_source_observation_blocks(self):
        item = list(self.item)
        item[2] = deepcopy(item[2])
        item[2]["sources"][0]["title"] = "This replacement source title is still a valid-looking observation"
        with self.assertRaises(ScriptContinuityError):
            validate(item)

    def test_claim_candidates_changed_without_new_external_anchor_blocks(self):
        item = list(self.item)
        proposal, slot, sources = item[:3]
        raw = {k: deepcopy(proposal[k]) for k in (
            "title", "hook", "viewer_benefit", "example_walkthrough", "narration",
            "visual_beats", "claim_candidates"
        )}
        raw["claim_candidates"][0]["claim"] = "A different factual assertion should be independently fact checked."
        item[0] = validate_proposal(raw, build_draft_input(slot, sources))
        with self.assertRaises(ScriptContinuityError):
            validate(item)

    def test_replay_to_another_release_slot_rejected(self):
        item = list(self.item)
        item[1] = fixture(1)[1]
        with self.assertRaises(ScriptContinuityError):
            validate(item)

    def test_changed_release_clock_rejected_before_signature(self):
        item = list(self.item)
        item[1] = dict(item[1], release_utc="2026-11-05T00:00:00Z")
        with self.assertRaises(ScriptContinuityError):
            validate(item)

    def test_unverified_media_or_publishing_status_cannot_be_promoted(self):
        item = list(self.item)
        item[1] = dict(item[1], release_authorized=True)
        with self.assertRaises(ScriptContinuityError):
            validate(item)

    def test_incorrect_independent_anchor_rejected(self):
        item = list(self.item)
        item[3] = "1"*64
        with self.assertRaises(ScriptContinuityError):
            validate(item)

    def test_missing_independent_anchor_rejected(self):
        item = list(self.item)
        item[3] = ""
        with self.assertRaises(ScriptContinuityError):
            validate(item)

    def test_signature_bitflip_rejected(self):
        item = list(self.item)
        sig = bytearray(base64.b64decode(item[5].signature_ed25519_b64))
        sig[10] ^= 0x01
        item[5] = replace(item[5], signature_ed25519_b64=base64.b64encode(sig).decode())
        with self.assertRaises(ScriptContinuityError):
            validate(item)

    def test_unknown_authorization_registry_rejected(self):
        item = list(self.item)
        item[4] = {}
        with self.assertRaises(ScriptContinuityError):
            validate(item)

    def test_replaced_public_key_does_not_validate_old_signature(self):
        item = list(self.item)
        changed = Ed25519PrivateKey.generate()
        public = changed.public_key().public_bytes(
            serialization.Encoding.Raw, serialization.PublicFormat.Raw)
        item[4] = {"trusted_custodian": replace(
            item[4]["trusted_custodian"],
            public_key_ed25519_b64=base64.b64encode(public).decode())}
        with self.assertRaises(ScriptContinuityError):
            validate(item)

    def test_revoked_custodian_rejected(self):
        item = list(self.item)
        item[4] = {"trusted_custodian": replace(item[4]["trusted_custodian"], active=False)}
        with self.assertRaises(ScriptContinuityError):
            validate(item)

    def test_signed_wrong_channel_rejected_even_if_resigned(self):
        item = list(self.item)
        claim = replace(item[5].claim, channel_id="another_youtube_channel")
        item[5] = DetachedScriptSeal(
            claim, base64.b64encode(item[6].sign(serialized(asdict(claim)))).decode())
        with self.assertRaises(ScriptContinuityError):
            validate(item)

    def test_signed_wrong_episode_rejected_even_if_resigned(self):
        item = list(self.item)
        claim = replace(item[5].claim, episode_id="fm_20261105_short_pm")
        item[5] = DetachedScriptSeal(
            claim, base64.b64encode(item[6].sign(serialized(asdict(claim)))).decode())
        with self.assertRaises(ScriptContinuityError):
            validate(item)

    def test_custodian_cannot_be_creator_or_publisher(self):
        with self.assertRaises(ScriptContinuityError):
            validate(self.item, excluded=frozenset(("trusted_custodian", "publisher_service")))

    def test_absent_excluded_identities_rejected(self):
        with self.assertRaises(ScriptContinuityError):
            validate(self.item, excluded=frozenset())

    def test_future_signed_seal_rejected(self):
        with self.assertRaises(ScriptContinuityError):
            validate(self.item, now=NOW-timedelta(hours=1))

    def test_expired_signed_seal_rejected(self):
        with self.assertRaises(ScriptContinuityError):
            validate(self.item, now=NOW+timedelta(hours=5))

    def test_naive_verifier_time_rejected(self):
        with self.assertRaises(ScriptContinuityError):
            validate(self.item, now=NOW.replace(tzinfo=None))


if __name__ == "__main__":
    unittest.main()
