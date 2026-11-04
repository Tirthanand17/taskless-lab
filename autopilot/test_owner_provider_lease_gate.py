"""Adversarial B3d4c2a owner-signed zero-cost *technical* permission tests.

Only disposable Ed25519 keys and synthetic source headlines. Signatures do
not establish real person enrollment, tier verification or provider consent.
"""
from __future__ import annotations

import base64
from dataclasses import asdict, replace
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import unittest

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

from autopilot.daily_cloud_plan import build_plan
from autopilot.script_draft_agent import build_draft_input
from autopilot.test_script_draft_agent import source, observations
from autopilot.owner_provider_lease_gate import (
    PURPOSE, STATUS, ModelLeaseError, TrustedProviderOwner,
    ProviderLeaseTerms, SignedProviderLease, canonical_bytes, digest,
    verify_owner_provider_lease, verify_three_daily_owner_lease_packets,
)
from autopilot.core import CHANNEL_ID

NOW = datetime(2026,11,4,6,40,tzinfo=timezone.utc)
EXCLUDED = frozenset({"publisher_agent", "script_generator_agent"})
PRIVATE_RECORD_HASH = sha256(b"private synthetic account consent fixture").hexdigest()


def make(index=0):
    slot = build_plan("2026-11-05",generated_at_utc=NOW)["slots"][index]
    obs = observations(source())
    context = build_draft_input(slot,obs)
    key = Ed25519PrivateKey.generate()
    pub = key.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw,
    )
    owner = TrustedProviderOwner(
        "enrolled_owner", "owner_key_one",
        base64.b64encode(pub).decode(),
    )
    terms=ProviderLeaseTerms(
        purpose=PURPOSE,
        channel_id=CHANNEL_ID,
        episode_id=slot["episode_id"],
        model_id="gemini-3.8-flash",
        provider_id="google_gemini_developer_api",
        draft_context_sha256=digest(context),
        owner_id=owner.owner_id,
        key_id=owner.key_id,
        lease_id=f"lease_{index:02d}_only",
        free_tier_billing_project_fingerprint_sha256=PRIVATE_RECORD_HASH,
        free_tier_entitlement_attestation_sha256=PRIVATE_RECORD_HASH,
        provider_data_terms_snapshot_sha256=PRIVATE_RECORD_HASH,
        owner_provider_data_use_consent_record_sha256=PRIVATE_RECORD_HASH,
        private_secret_custody_policy_sha256=PRIVATE_RECORD_HASH,
        allowed_data_class="PUBLIC_HEADLINE_METADATA_ONLY",
        requests_allowed=1,
        incremental_paid_budget_cents=0,
        accepts_provider_improvement_use=True,
        owner_grants_external_inference=True,
        issued_at_utc=(NOW-timedelta(minutes=10)).isoformat(),
        expires_at_utc=(NOW+timedelta(minutes=40)).isoformat(),
    )
    signature=base64.b64encode(key.sign(canonical_bytes(asdict(terms)))).decode()
    return {
        "slot":slot, "observations":obs, "terms":terms, "key":key,
        "lease":SignedProviderLease(terms,signature),
        "anchor":digest(asdict(terms)),
        "registry":{owner.owner_id:owner},
    }


def verify_fixture(item,*,clock=NOW, excluded=EXCLUDED):
    return verify_owner_provider_lease(
        slot=item["slot"], observations=item["observations"],
        signed_lease=item["lease"],
        external_lease_anchor_sha256=item["anchor"],
        owner_registry=item["registry"],
        excluded_automated_agent_ids=excluded,
        now=clock,
    )


def resign(item, **changes):
    new=replace(item["lease"].terms,**changes)
    item["lease"]=SignedProviderLease(new,base64.b64encode(
        item["key"].sign(canonical_bytes(asdict(new)))).decode())
    item["terms"]=new
    item["anchor"]=digest(asdict(new))


class OwnerSignedProviderLeaseTests(unittest.TestCase):
    def setUp(self):
        self.d=make()

    def test_signed_owner_packet_is_only_a_cryptographic_not_an_entitlement_preflight(self):
        packet=verify_fixture(self.d)
        self.assertEqual(packet["status"],STATUS)
        self.assertTrue(packet["provider_owner_key_signature_valid"])
        self.assertEqual(packet["signed_scope_limit_requests"],1)
        self.assertEqual(packet["signed_max_incremental_paid_budget_cents"],0)
        self.assertEqual(packet["episode_id"],self.d["slot"]["episode_id"])
        self.assertEqual(packet["draft_context_sha256"],digest(
            build_draft_input(self.d["slot"],self.d["observations"])))
        for key in (
            "owner_identity_real_world_authenticated_by_software",
            "private_entitlement_records_independently_validated",
            "actual_provider_project_and_zero_spend_verified",
            "private_immutable_request_ledger_connected",
            "private_key_vault_connected",
            "provider_terms_real_consent_verified",
            "provider_live_call_enabled",
            "youtube_upload_enabled",
            "youtube_schedule_enabled",
            "release_authorized",
        ):
            self.assertIs(packet[key],False,key)

    def test_three_distinct_daily_intent_preflights_but_no_model_calls(self):
        records=[verify_fixture(make(i)) for i in range(3)]
        r=verify_three_daily_owner_lease_packets(records)
        self.assertEqual(r["signed_lease_count"],3)
        self.assertEqual(len(r["episode_ids"]),3)
        self.assertFalse(r["provider_inference_executed"])
        self.assertFalse(r["budget_lease_atomically_consumed"])
        self.assertFalse(r["youtube_upload_enabled"])
        self.assertFalse(r["release_authorized"])

    def test_duplicate_episode_or_lease_never_counts_as_three(self):
        records=[verify_fixture(make(i)) for i in range(3)]
        for field in ("episode_id","lease_id","draft_context_sha256"):
            with self.subTest(field=field):
                changed=[dict(x) for x in records]
                changed[1][field]=changed[0][field]
                with self.assertRaises(ModelLeaseError):
                    verify_three_daily_owner_lease_packets(changed)

    def test_cross_day_mixed_lease_packets_block(self):
        records=[verify_fixture(make(i)) for i in range(3)]
        records[2]["episode_id"]="fm_20261106_short_pm"
        with self.assertRaises(ModelLeaseError):
            verify_three_daily_owner_lease_packets(records)

    def test_missing_owner_registry_or_automated_exclusion_blocks(self):
        for field,value in (
            ("registry",{}),("registry",{"untrusted":self.d["registry"]["enrolled_owner"]}),
        ):
            with self.subTest(field=field):
                d=make()
                d[field]=value
                with self.assertRaises(ModelLeaseError):
                    verify_fixture(d)
        with self.assertRaises(ModelLeaseError):
            verify_fixture(self.d,excluded=frozenset())

    def test_robot_cannot_impersonate_owner_even_with_valid_own_signature(self):
        resign(self.d, owner_id="publisher_agent")
        with self.assertRaises(ModelLeaseError):
            verify_fixture(self.d)

    def test_revoked_owner_key_blocks(self):
        item=self.d["registry"]["enrolled_owner"]
        self.d["registry"]["enrolled_owner"]=replace(item,active=False)
        with self.assertRaises(ModelLeaseError):
            verify_fixture(self.d)

    def test_wrong_public_key_denies_signature(self):
        item=self.d["registry"]["enrolled_owner"]
        wrong=Ed25519PrivateKey.generate().public_key().public_bytes(
            serialization.Encoding.Raw,serialization.PublicFormat.Raw)
        self.d["registry"]["enrolled_owner"]=replace(
            item,public_key_ed25519_b64=base64.b64encode(wrong).decode())
        with self.assertRaises(ModelLeaseError):
            verify_fixture(self.d)

    def test_changed_signed_consent_scope_even_if_hash_correct_requires_new_key_signature(self):
        t=replace(self.d["lease"].terms,model_id="gemini-2.5-flash")
        self.d["lease"]=SignedProviderLease(t,self.d["lease"].signature_ed25519_b64)
        self.d["anchor"]=digest(asdict(t))
        with self.assertRaises(ModelLeaseError):
            verify_fixture(self.d)

    def test_changed_owner_lease_external_anchor_blocks(self):
        self.d["anchor"]="f"*64
        with self.assertRaises(ModelLeaseError):
            verify_fixture(self.d)

    def test_source_headline_change_after_signing_blocks(self):
        self.d["observations"]["sources"][0]["title"] += " Tampered by an attacker"
        with self.assertRaises(ModelLeaseError):
            verify_fixture(self.d)

    def test_wrong_episode_or_channel_replay_blocks_even_resigned(self):
        for value in ("fm_20261106_long","fm_20261105_short_pm"):
            with self.subTest(value=value):
                d=make()
                resign(d,episode_id=value)
                with self.assertRaises(ModelLeaseError):
                    verify_fixture(d)
        resign(self.d,channel_id="another_channel")
        with self.assertRaises(ModelLeaseError):
            verify_fixture(self.d)

    def test_owner_free_tier_record_digests_cannot_be_empty(self):
        for field in (
            "free_tier_billing_project_fingerprint_sha256",
            "free_tier_entitlement_attestation_sha256",
            "provider_data_terms_snapshot_sha256",
            "owner_provider_data_use_consent_record_sha256",
            "private_secret_custody_policy_sha256",
        ):
            with self.subTest(field=field):
                d=make()
                resign(d,**{field:"unverified"})
                with self.assertRaises(ModelLeaseError):
                    verify_fixture(d)

    def test_no_paid_spend_or_multiple_requests_even_with_signed_owner(self):
        for field,value in (
            ("incremental_paid_budget_cents",1),
            ("incremental_paid_budget_cents",-1),
            ("incremental_paid_budget_cents",False),
            ("requests_allowed",2),
            ("requests_allowed",0),
            ("requests_allowed",True),
        ):
            with self.subTest(field=field,value=value):
                d=make()
                resign(d,**{field:value})
                with self.assertRaises(ModelLeaseError):
                    verify_fixture(d)

    def test_data_use_consent_did_not_occur_by_default(self):
        for field,value in (
            ("accepts_provider_improvement_use",False),
            ("accepts_provider_improvement_use","yes"),
            ("owner_grants_external_inference",False),
            ("allowed_data_class","FULL_PRIVATE_SOURCE_BODIES"),
        ):
            with self.subTest(field=field):
                d=make()
                resign(d,**{field:value})
                with self.assertRaises(ModelLeaseError):
                    verify_fixture(d)

    def test_wrong_model_provider_or_purpose_denied(self):
        for field,value in (
            ("model_id","gemini-vision-unapproved"),
            ("provider_id","unknown_provider"),
            ("purpose","PUBLISH_RIGHT_NOW"),
        ):
            with self.subTest(field=field):
                d=make()
                resign(d,**{field:value})
                with self.assertRaises(ModelLeaseError):
                    verify_fixture(d)

    def test_expired_or_future_signed_attestation_denied(self):
        for clock in (
            NOW + timedelta(hours=2),
            NOW - timedelta(hours=1),
            NOW.replace(tzinfo=None),
        ):
            with self.subTest(clock=clock),self.assertRaises(ModelLeaseError):
                verify_fixture(self.d,clock=clock)

    def test_malformed_signature_or_public_key_denied(self):
        item=self.d["lease"]
        self.d["lease"]=replace(item,signature_ed25519_b64="aaaa")
        with self.assertRaises(ModelLeaseError):
            verify_fixture(self.d)

    def test_forged_source_approval_flags_denied(self):
        self.d["observations"]["sources"][0]["facts_verified"]=True
        with self.assertRaises(ModelLeaseError):
            verify_fixture(self.d)

    def test_slot_replay_and_prepublished_slots_denied(self):
        d=make()
        d["slot"]["release_authorized"]=True
        with self.assertRaises(ModelLeaseError):
            verify_fixture(d)

    def test_unsigned_or_missing_owner_does_not_return_approved(self):
        d=make()
        d["lease"]=None
        with self.assertRaises(ModelLeaseError):
            verify_fixture(d)

    def test_valid_signature_does_not_allow_upload_even_with_mock_provider(self):
        preflight=verify_fixture(self.d)
        self.assertFalse(preflight["provider_live_call_enabled"])
        self.assertFalse(preflight["release_authorized"])
        self.assertFalse(preflight["youtube_upload_enabled"])


if __name__=="__main__":
    unittest.main()
